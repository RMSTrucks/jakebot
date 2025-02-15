from typing import Dict, Any
from .base_integration import BaseIntegration

class NowCertsIntegration(BaseIntegration):
    """Integration with NowCerts API"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "https://api.nowcerts.com/api")  # Update URL as needed
    
    def create_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a task/activity in NowCerts"""
        endpoint = f"{self.base_url}/activity"  # Update endpoint as per NowCerts API
        response = self.session.post(endpoint, json=data)
        response.raise_for_status()
        return response.json()
    
    def update_task(self, task_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a task/activity in NowCerts"""
        endpoint = f"{self.base_url}/activity/{task_id}"
        response = self.session.put(endpoint, json=data)
        response.raise_for_status()
        return response.json()
    
    def update_policy(self, policy_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update policy information"""
        endpoint = f"{self.base_url}/policy/{policy_id}"
        response = self.session.put(endpoint, json=data)
        response.raise_for_status()
        return response.json() 