from typing import Dict, Any
import requests
from abc import ABC, abstractmethod

class BaseIntegration(ABC):
    """Base class for all external service integrations"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    @abstractmethod
    def create_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a task in the external service"""
        pass
    
    @abstractmethod
    def update_task(self, task_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a task in the external service"""
        pass 