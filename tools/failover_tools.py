"""
Apollo Router Client - Interface for Apollo Router admin API
"""

import requests
import time
from typing import Dict

class ApolloRouterClient:
    """Client for interacting with Apollo Router admin API"""
    
    def __init__(self, router_url: str, admin_api_key: str):
        """
        Initialize Apollo Router client.
        
        Args:
            router_url: Apollo Router base URL
            admin_api_key: Admin API key for authentication
        """
        self.base_url = router_url
        self.admin_endpoint = f"{router_url}/admin"
        self.headers = {
            "Authorization": f"Bearer {admin_api_key}",
            "Content-Type": "application/json"
        }
    
    def get_current_configuration(self, service: str) -> Dict:
        """
        Retrieve current backend configuration for a service.
        
        Args:
            service: GraphQL service/subgraph name
        
        Returns:
            dict: Current routing configuration including backend endpoints and weights
        """
        endpoint = f"{self.admin_endpoint}/configuration/{service}"
        
        try:
            response = requests.get(endpoint, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def update_backend_weights(
        self,
        service: str,
        backend_weights: Dict[str, int]
    ) -> bool:
        """
        Update traffic distribution across backend endpoints.
        
        Args:
            service: GraphQL service name
            backend_weights: Dictionary mapping backend URLs to percentage weights
            
        Example:
            {
                "https://backend-east.example.com": 100,
                "https://backend-west.example.com": 0
            }
        
        Returns:
            bool: True if update successful, False otherwise
        """
        endpoint = f"{self.admin_endpoint}/configuration/{service}/routing"
        
        # Apollo Router expects configuration in specific format
        config = {
            "subgraph": service,
            "routing": {
                "backends": [
                    {
                        "url": backend_url,
                        "weight": weight
                    }
                    for backend_url, weight in backend_weights.items()
                ]
            }
        }
        
        try:
            response = requests.put(endpoint, json=config, headers=self.headers, timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def check_backend_health(self, backend_url: str) -> Dict:
        """
        Check health status of a specific backend endpoint.
        
        Args:
            backend_url: Backend URL to check
        
        Returns:
            dict: Health check result with status and response time
        """
        health_endpoint = f"{backend_url}/.well-known/apollo/server-health"
        
        try:
            start = time.time()
            response = requests.get(health_endpoint, timeout=5)
            latency = (time.time() - start) * 1000  # Convert to ms
            
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "latency_ms": round(latency, 2),
                "details": response.json() if response.status_code == 200 else None
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "unreachable",
                "error": str(e)
            }
