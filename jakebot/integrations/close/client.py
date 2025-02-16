from typing import Dict, Any, Optional
import requests
import logging
import hmac
import hashlib
import json
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from functools import lru_cache

logger = logging.getLogger(__name__)

class CloseAPIError(Exception):
    """Custom exception for Close API errors"""
    def __init__(self, message: str, status_code: int = None, response: Any = None):
        self.status_code = status_code
        self.response = response
        super().__init__(message)

class CloseClient:
    """Client for interacting with Close CRM API"""
    
    def __init__(self, 
                 api_key: str, 
                 webhook_secret: str,
                 base_url: str = "https://api.close.com/api/v1",
                 max_retries: int = 3):
        self.base_url = base_url
        self.webhook_secret = webhook_secret
        self.max_retries = max_retries
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Basic {api_key}",
            "Content-Type": "application/json"
        })
    
    @lru_cache(maxsize=100)  # Cache up to 100 call details
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=lambda e: isinstance(e, (requests.RequestException, CloseAPIError))
    )
    def get_call(self, call_id: str) -> Dict[str, Any]:
        """Get call details including transcript"""
        try:
            endpoint = f"{self.base_url}/activity/call/{call_id}/"
            response = self.session.get(endpoint, params={"_fields": "recording_transcript"})
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully retrieved call details for {call_id}")
            return data
            
        except requests.RequestException as e:
            logger.error(f"Error getting call {call_id}: {str(e)}")
            raise CloseAPIError(
                f"Failed to get call details: {str(e)}", 
                status_code=getattr(e.response, 'status_code', None),
                response=getattr(e, 'response', None)
            )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def create_task(self, 
                    lead_id: str, 
                    description: str, 
                    due_date: Optional[datetime] = None,
                    assigned_to: Optional[str] = None,
                    priority: str = "normal") -> Dict[str, Any]:
        """
        Create a task in Close
        
        Args:
            lead_id: The Close lead ID
            description: Task description
            due_date: Optional due date
            assigned_to: Optional user ID to assign the task to
            priority: Task priority (low, normal, high)
            
        Returns:
            Dict containing created task details
            
        Raises:
            CloseAPIError: If the API request fails
        """
        try:
            endpoint = f"{self.base_url}/task"
            
            data = {
                "lead_id": lead_id,
                "text": description,
                "_type": "task",
                "priority": priority
            }
            
            if due_date:
                data["due_date"] = due_date.strftime("%Y-%m-%d")
            
            if assigned_to:
                data["assigned_to"] = assigned_to
                
            response = self.session.post(endpoint, json=data)
            response.raise_for_status()
            
            task_data = response.json()
            logger.info(f"Successfully created task for lead {lead_id}")
            
            # Send notification to Slack
            send_slack_notification(f"New task created for lead {lead_id}: {description}")
            
            return task_data
            
        except requests.RequestException as e:
            logger.error(f"Error creating task for lead {lead_id}: {str(e)}")
            raise CloseAPIError(
                f"Failed to create task: {str(e)}",
                status_code=getattr(e.response, 'status_code', None),
                response=getattr(e, 'response', None)
            )
    
    def verify_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
        """
        Verify webhook signature from Close
        
        Args:
            payload: The webhook payload
            signature: The signature from the X-Close-Signature header
            
        Returns:
            bool indicating if signature is valid
        """
        try:
            # Convert payload to canonical string
            payload_string = json.dumps(payload, separators=(',', ':'))
            
            # Create HMAC with webhook secret
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                payload_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False

def send_slack_notification(message: str):
    webhook_url = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    payload = {"text": message}
    response = requests.post(webhook_url, json=payload)
    if response.status_code != 200:
        raise ValueError(f"Request to Slack returned an error {response.status_code}, the response is:\n{response.text}") 