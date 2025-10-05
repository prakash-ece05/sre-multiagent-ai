"""
Failover Tools - Functions to manage traffic failover operations with safety guardrails
"""

import os
import time
import requests
from typing import Dict, List
from clients.apollo_client import ApolloRouterClient
from config.applications import get_service_backends

# Configuration
APOLLO_ROUTER_URL = os.getenv("APOLLO_ROUTER_URL")
APOLLO_ADMIN_API_KEY = os.getenv("APOLLO_ADMIN_API_KEY")
FAILOVER_RATE_LIMIT_SECONDS = int(os.getenv("FAILOVER_RATE_LIMIT_SECONDS", "300"))

# Initialize Apollo client
apollo_client = ApolloRouterClient(APOLLO_ROUTER_URL, APOLLO_ADMIN_API_KEY)

# In-memory storage for failover tracking
_failover_history = {}
_rollback_configs = {}

def get_valid_backends_for_service(service: str) -> List[str]:
    """Get list of valid backend URLs for a service"""
    return get_service_backends(service)

def get_last_failover_time(service: str) -> float:
    """Get timestamp of last failover for a service"""
    return _failover_history.get(service, 0)

def store_rollback_config(service: str, config: Dict) -> None:
    """Store configuration for potential rollback"""
    _rollback_configs[service] = config

def record_failover_event(service: str, backend_weights: Dict[str, int]) -> None:
    """Record successful failover event"""
    _failover_history[service] = time.time()

def extract_weights_from_config(config: Dict) -> Dict[str, int]:
    """Extract backend weights from configuration"""
    backends = config.get("routing", {}).get("backends", [])
    return {
        backend["url"]: backend.get("weight", 0)
        for backend in backends
    }

def format_weight_distribution(weights: Dict[str, int]) -> str:
    """Format weight distribution for display"""
    parts = []
    for url, weight in weights.items():
        backend_name = url.split("//")[-1].split(".")[0]
        parts.append(f"{backend_name}: {weight}%")
    return ", ".join(parts)

def verify_schema_compatibility(service: str, backend_url: str) -> bool:
    """
    Verify GraphQL schema compatibility (simplified implementation).
    In production, this should check actual schema compatibility.
    """
    # Placeholder - implement actual schema verification
    return True

def verify_configuration_match(
    requested_weights: Dict[str, int],
    applied_backends: List[Dict]
) -> bool:
    """Verify that applied configuration matches requested weights"""
    applied_weights = {
        backend["url"]: backend.get("weight", 0)
        for backend in applied_backends
    }
    return requested_weights == applied_weights

def execute_failover(
    service: str,
    backend_weights: Dict[str, int]
) -> Dict:
    """
    Execute traffic failover for a GraphQL service through Apollo Router.
    
    Args:
        service: GraphQL service/subgraph name
        backend_weights: Target backend URLs with percentage weights
    
    Returns:
        dict: Failover result with success status and details
    """
    # Step 1: Validate service-backend mapping
    valid_backends = get_valid_backends_for_service(service)
    for backend_url in backend_weights.keys():
        if backend_url not in valid_backends:
            return {
                "success": False,
                "error": f"Invalid backend '{backend_url}' for service '{service}'. "
                        f"Valid backends: {', '.join(valid_backends)}"
            }
    
    # Step 2: Validate weights sum to 100%
    total_weight = sum(backend_weights.values())
    if total_weight != 100:
        return {
            "success": False,
            "error": f"Weights must sum to 100%, got {total_weight}%"
        }
    
    # Step 3: Check target backend health
    for backend_url, weight in backend_weights.items():
        if weight > 0:  # Only check backends receiving traffic
            health = apollo_client.check_backend_health(backend_url)
            if health["status"] != "healthy":
                return {
                    "success": False,
                    "error": f"Backend '{backend_url}' is {health['status']}. "
                            f"Cannot route traffic to unhealthy backend."
                }
    
    # Step 4: Check schema compatibility
    for backend_url, weight in backend_weights.items():
        if weight > 0:
            if not verify_schema_compatibility(service, backend_url):
                return {
                    "success": False,
                    "error": f"Backend '{backend_url}' has incompatible GraphQL schema"
                }
    
    # Step 5: Rate limiting check
    last_failover = get_last_failover_time(service)
    if last_failover and (time.time() - last_failover) < FAILOVER_RATE_LIMIT_SECONDS:
        wait_time = FAILOVER_RATE_LIMIT_SECONDS - (time.time() - last_failover)
        return {
            "success": False,
            "error": f"Rate limit: Wait {wait_time:.0f}s before next failover"
        }
    
    # Step 6: Store current configuration for rollback
    current_config = apollo_client.get_current_configuration(service)
    store_rollback_config(service, current_config)
    
    # Step 7: Apply new configuration to Apollo Router
    success = apollo_client.update_backend_weights(service, backend_weights)
    if not success:
        return {
            "success": False,
            "error": "Failed to update Apollo Router configuration"
        }
    
    # Step 8: Verify configuration applied correctly
    time.sleep(2)  # Allow router to propagate configuration
    new_config = apollo_client.get_current_configuration(service)
    verification_success = verify_configuration_match(
        backend_weights,
        new_config["routing"]["backends"]
    )
    
    if not verification_success:
        # Automatic rollback on verification failure
        apollo_client.update_backend_weights(
            service,
            extract_weights_from_config(current_config)
        )
        return {
            "success": False,
            "error": "Configuration verification failed. Automatic rollback executed."
        }
    
    # Step 9: Record successful failover
    record_failover_event(service, backend_weights)
    
    return {
        "success": True,
        "service": service,
        "previous_config": extract_weights_from_config(current_config),
        "new_config": backend_weights,
        "message": f"Successfully failed over '{service}' traffic. "
                  f"New distribution: {format_weight_distribution(backend_weights)}"
    }

def rollback_failover(service: str) -> Dict:
    """
    Rollback to previous configuration for a service.
    
    Args:
        service: GraphQL service/subgraph name
    
    Returns:
        dict: Rollback result
    """
    if service not in _rollback_configs:
        return {
            "success": False,
            "error": f"No rollback configuration available for {service}"
        }
    
    rollback_config = _rollback_configs[service]
    rollback_weights = extract_weights_from_config(rollback_config)
    
    success = apollo_client.update_backend_weights(service, rollback_weights)
    
    if not success:
        return {
            "success": False,
            "error": "Failed to execute rollback"
        }
    
    return {
        "success": True,
        "service": service,
        "message": f"Successfully rolled back {service} to previous configuration",
        "configuration": rollback_weights
    }
