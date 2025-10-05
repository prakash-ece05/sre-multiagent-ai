"""
KPI Tools - Functions to retrieve and analyze Key Performance Indicators
"""

import os
import requests
from typing import Dict, Tuple, Optional

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

def get_volume(capability: str, duration: str) -> Tuple[int, Optional[float]]:
    """
    Get total count for a given capability and time range.
    
    Args:
        capability: key capability name (e.g., "login")
        duration: Query duration (e.g., "1h", "24h")
    
    Returns:
        Tuple containing:
            - The HTTP status code of the response
            - The volume count (if successful) or error message (if failed)
    """
    url = f'{GRAFANA_URL}/api/datasources/proxy/{PROMETHEUS_DATASOURCE_ID}/api/v1/query'
    query = f'sum(increase(requests_total{{service="{capability}"}}[{duration}]))'
    
    headers = _get_grafana_headers()
    
    try:
        response = requests.get(url, headers=headers, params={'query': query}, timeout=8)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "success":
            results = data.get("data", {}).get("result", [])
            if results:
                volume = float(results[0].get("value", [0, 0])[1])
                return response.status_code, volume
            return response.status_code, 0.0
        else:
            return response.status_code, "Failed API Request"
            
    except requests.exceptions.RequestException as e:
        return 500, f"Request failed: {str(e)}"

def get_availability(capability: str, duration: str) -> Tuple[int, Optional[float]]:
    """
    Get availability (success rate) for a given capability and time range.
    
    Args:
        capability: key capability name (e.g., "login")
        duration: time range (e.g., "1h", "24h")
    
    Returns:
        Tuple containing:
            - The HTTP status code of the response
            - The availability percentage (if successful) or error message (if failed)
    """
    url = f'{GRAFANA_URL}/api/datasources/proxy/{PROMETHEUS_DATASOURCE_ID}/api/v1/query'
    query = (
        f'sum(increase(requests_total{{service="{capability}", '
        f'status="success"}}[{duration}])) / '
        f'sum(increase(requests_total{{service="{capability}"}}[{duration}])) * 100'
    )
    
    headers = _get_grafana_headers()
    
    try:
        response = requests.get(url, headers=headers, params={'query': query}, timeout=8)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "success":
            results = data.get("data", {}).get("result", [])
            if results:
                availability = float(results[0].get("value", [0, 0])[1])
                return response.status_code, round(availability, 2)
            return response.status_code, 0.0
        else:
            return response.status_code, "Failed API Request"
            
    except requests.exceptions.RequestException as e:
        return 500, f"Request failed: {str(e)}"
