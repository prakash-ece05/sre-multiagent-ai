"""
Metrics Tools - Functions to analyze VALE metrics (Volume, Availability, Latency, Errors)
"""

import os
import requests
from typing import Dict

# Configuration
GRAFANA_URL = os.getenv("GRAFANA_URL")
GRAFANA_TOKEN = os.getenv("GRAFANA_API_TOKEN")
PROMETHEUS_DATASOURCE_ID = os.getenv("PROMETHEUS_DATASOURCE_ID", "2")

def _get_grafana_headers() -> Dict[str, str]:
    """Get standard Grafana API headers"""
    return {
        'Content-Type': 'application/json',
        'X-Disable-Provenance': 'true',
        'Authorization': f'Bearer {GRAFANA_TOKEN}'
    }

def get_success_rate_for_service(service: str, time_range: str) -> Dict:
    """
    Get the success rate for a given service and time range.
    
    Args:
        service: Service name
        time_range: The time range for the query (e.g., "1h", "24h")
    
    Returns:
        dict: Status and result or error message
    """
    url = f'{GRAFANA_URL}/api/datasources/proxy/{PROMETHEUS_DATASOURCE_ID}/api/v1/query'
    query = (
        f'sum(increase(requests_total{{service="{service}", '
        f'response_code=~"[234].."}}[{time_range}])) / '
        f'sum(increase(requests_total{{service="{service}"}}[{time_range}])) * 100'
    )
    
    headers = _get_grafana_headers()
    
    try:
        response = requests.get(url, headers=headers, params={'query': query}, timeout=8)
        response.raise_for_status()  # Raise an error for bad response
        data = response.json()
        
        if data.get("status") == "success":  # Fixed: colon instead of semicolon
            results = data.get("data", {}).get("result", [])
            if results:
                success_rate = float(results[0].get("value", [0, 0])[1])  # Fixed: proper indexing
                return {
                    "status": "success",
                    "service": service,
                    "success_rate": round(success_rate, 2),
                    "time_range": time_range
                }
            return {
                "status": "success",
                "service": service,
                "success_rate": 0.0,
                "time_range": time_range
            }
        else:
            return {
                "status": "error",
                "message": f"Failed API Request: {data.get('error', 'Unknown error')}"
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Request failed: {str(e)}"
        }

def get_p95_latency_for_service(service: str, time_range: str) -> Dict:
    """
    Get P95 latency for a given service and time range.
    
    Args:
        service: Service name
        time_range: The time range for the query (e.g., "1h", "24h")
    
    Returns:
        dict: Status and result or error message
    """
    url = f'{GRAFANA_URL}/api/datasources/proxy/{PROMETHEUS_DATASOURCE_ID}/api/v1/query'
    query = (
        f'histogram_quantile(0.95, '
        f'sum(rate(request_duration_milliseconds_bucket{{service="{service}"}}[{time_range}])) by (le))'
    )  # Fixed: changed {duration} to {time_range}, removed unused service grouping
    
    headers = _get_grafana_headers()
    
    try:
        response = requests.get(url, headers=headers, params={'query': query}, timeout=8)
        response.raise_for_status()  # Raise an error for bad response
        data = response.json()
        
        if data.get("status") == "success":  # Fixed: colon instead of semicolon
            results = data.get("data", {}).get("result", [])
            if results:
                latency = float(results[0].get("value", [0, 0])[1])  # Fixed: proper indexing
                return {
                    "status": "success",
                    "service": service,
                    "p95_latency_ms": round(latency, 2),
                    "time_range": time_range
                }
            return {
                "status": "success",
                "service": service,
                "p95_latency_ms": 0.0,
                "time_range": time_range
            }
        else:
            return {
                "status": "error",
                "message": f"Failed API Request: {data.get('error', 'Unknown error')}"
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Request failed: {str(e)}"
        }
