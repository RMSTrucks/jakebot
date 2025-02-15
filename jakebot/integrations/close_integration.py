from typing import Dict, Any
from .base_integration import BaseIntegration

class CloseIntegration(BaseIntegration):
    """Integration with Close CRM API"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "https://api.close.com/api/v1")
    
    def create_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a task in Close CRM"""
        endpoint = f"{self.base_url}/task"
        response = self.session.post(endpoint, json=data)
        response.raise_for_status()
        return response.json()
    
    def update_task(self, task_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a task in Close CRM"""
        endpoint = f"{self.base_url}/task/{task_id}"
        response = self.session.put(endpoint, json=data)
        response.raise_for_status()
        return response.json() 