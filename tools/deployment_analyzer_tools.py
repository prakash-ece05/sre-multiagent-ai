"""
Harness Client - Interface for Harness deployment API
"""

import requests
from typing import Dict, List
from datetime import datetime, timedelta

class HarnessDeploymentClient:
    """Client for interacting with Harness deployment API"""
    
    def __init__(self, harness_url: str, api_key: str, account_id: str):
        """
        Initialize Harness client.
        
        Args:
            harness_url: Harness base URL
            api_key: API key for authentication
            account_id: Harness account ID
        """
        self.base_url = harness_url
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        self.account_id = account_id
    
    def _get_start_time_ms(self, time_range: str) -> int:
        """
        Convert time range string to Unix timestamp in milliseconds.
        
        Args:
            time_range: Time range (e.g., "1h", "24h", "7d")
        
        Returns:
            int: Unix timestamp in milliseconds
        """
        unit = time_range[-1]
        value = int(time_range[:-1])
        
        if unit == 'h':
            delta = timedelta(hours=value)
        elif unit == 'd':
            delta = timedelta(days=value)
        elif unit == 'm':
            delta = timedelta(minutes=value)
        else:
            delta = timedelta(hours=24)
        
        start_time = datetime.now() - delta
        return int(start_time.timestamp() * 1000)
    
    def _format_timestamp(self, timestamp_ms: int) -> str:
        """
        Format Unix timestamp to ISO format string.
        
        Args:
            timestamp_ms: Unix timestamp in milliseconds
        
        Returns:
            str: ISO format timestamp or None
        """
        if not timestamp_ms:
            return None
        return datetime.fromtimestamp(timestamp_ms / 1000).isoformat()
    
    def _extract_stages(self, execution_graph: Dict) -> List[Dict]:
        """
        Extract stage information from execution graph.
        
        Args:
            execution_graph: Execution graph data
        
        Returns:
            list: Simplified stage information
        """
        stages = []
        nodes = execution_graph.get("nodes", [])
        
        for node in nodes:
            if node.get("type") == "STAGE":
                stages.append({
                    "name": node.get("name"),
                    "status": node.get("status"),
                    "duration_ms": node.get("durationMs")
                })
        
        return stages
    
    def get_recent_deployments(self, service: str, time_range: str = "24h") -> List[Dict]:
        """
        Retrieve recent deployments for a service from Harness.
        
        Args:
            service: Service name
            time_range: Lookback period (e.g., "1h", "24h", "7d")
        
        Returns:
            List of recent deployments with status and metadata
        """
        endpoint = f"{self.base_url}/ng/api/deployments"
        start_time = self._get_start_time_ms(time_range)
        
        params = {
            "accountIdentifier": self.account_id,
            "serviceId": service,
            "startTime": start_time,
            "pageSize": 20
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            deployments = response.json().get("data", {}).get("content", [])
            
            return [
                {
                    "deployment_id": dep["id"],
                    "service": dep["serviceIdentifier"],
                    "pipeline": dep["pipelineIdentifier"],
                    "status": dep["status"],
                    "start_time": self._format_timestamp(dep["startTs"]),
                    "end_time": self._format_timestamp(dep.get("endTs")),
                    "triggered_by": dep.get("triggeredBy", {}).get("identifier"),
                    "environment": dep.get("envIdentifier"),
                    "version": dep.get("tag", "unknown")
                }
                for dep in deployments
            ]
        except requests.exceptions.RequestException as e:
            raise Exception(f"Harness API error: {str(e)}")
    
    def get_deployment_details(self, deployment_id: str) -> Dict:
        """
        Get detailed information about a specific deployment.
        
        Args:
            deployment_id: Deployment ID
        
        Returns:
            dict: Detailed deployment info including stages, artifacts, and logs
        """
        endpoint = f"{self.base_url}/ng/api/deployments/{deployment_id}"
        params = {"accountIdentifier": self.account_id}
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json().get("data", {})
            
            return {
                "deployment_id": deployment_id,
                "service": data["serviceIdentifier"],
                "environment": data["envIdentifier"],
                "status": data["status"],
                "pipeline": data["pipelineIdentifier"],
                "triggered_by": data.get("triggeredBy", {}).get("identifier"),
                "start_time": self._format_timestamp(data["startTs"]),
                "end_time": self._format_timestamp(data.get("endTs")),
                "duration": data.get("duration"),
                "artifact": {
                    "type": data.get("artifactType"),
                    "version": data.get("tag"),
                    "image": data.get("artifactImage")
                },
                "stages": self._extract_stages(data.get("executionGraph", {})),
                "rollback_available": data.get("canRollback", False)
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"Harness API error: {str(e)}")
