"""
Trace Tools - Functions to analyze distributed traces
"""

import os
import requests
from typing import Dict, List

# Configuration
TEMPO_URL = os.getenv("TEMPO_URL", os.getenv("GRAFANA_URL"))

def fetch_traceid_by_service(service: str, time_range: str, duration: str = "100ms", 
                             status: str = "error") -> Dict:
    """
    Get the trace IDs for the provided service matching specified criteria.
    
    Args:
        service: Name of the service
        time_range: The time range for the query (e.g., "1h", "24h")
        duration: Minimum duration for the trace (e.g., '10ms', '1s')
        status: Status of the trace (e.g., 'ok', 'error')
    
    Returns:
        dict: Status and list of trace IDs or error message
    """
    url = f'{TEMPO_URL}/api/search'
    
    params = {  # Fixed: lowercase 'params'
        "tags": f"service.name={service}",
        "minDuration": duration,
        "status": status,
        "limit": 20  # Added limit to prevent overwhelming results
    }
    # Note: time_range handling depends on Tempo version
    # Some versions use startTime/endTime instead
    
    headers = {
        'x-scope-OrgID': '1'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)  
        response.raise_for_status()  # Raise an error for bad response
        data = response.json()
        
        if response.status_code == 200:  
            traces = data.get("traces", [])
            formatted_results = []  
            
            for trace in traces:
                trace_id = trace.get("traceID")
                if trace_id:
                    formatted_results.append({
                        "trace_id": trace_id,
                        "duration_ms": trace.get("durationMs", 0),
                        "start_time": trace.get("startTimeUnixNano", 0)
                    })
            
            return {
                "status": "success",
                "service": service,
                "count": len(formatted_results),
                "traces": formatted_results
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to retrieve data. Status code: {response.status_code}"  
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Request failed: {str(e)}"
        }
