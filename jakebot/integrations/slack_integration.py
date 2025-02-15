from typing import Dict, Any
from .base_integration import BaseIntegration

class SlackIntegration(BaseIntegration):
    """Integration with Slack API"""
    
    def __init__(self, webhook_url: str):
        # Slack uses webhook URLs instead of base_url + api_key
        super().__init__(api_key="", base_url=webhook_url)
    
    def create_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message to Slack"""
        response = self.session.post(
            self.base_url,
            json={"text": data.get("message", "No message provided")}
        )
        response.raise_for_status()
        return {"status": "sent"}
    
    def update_task(self, task_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a Slack message (not typically used)"""
        # Slack webhook doesn't support updating messages
        raise NotImplementedError("Updating Slack messages not supported via webhooks")
    
    def send_notification(self, message: str, channel: str = None) -> Dict[str, Any]:
        """Send a notification to Slack"""
        payload = {
            "text": message,
            "channel": channel
        }
        response = self.session.post(self.base_url, json=payload)
        response.raise_for_status()
        return {"status": "sent"} 