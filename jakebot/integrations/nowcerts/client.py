"""NowCerts API client with enhanced error handling"""
import logging
from typing import Dict, Optional, Any
import aiohttp
import backoff
from datetime import datetime
import json

from jakebot.config import JakeBotConfig
from jakebot.exceptions import NowCertsError, RetryableError, ValidationError

logger = logging.getLogger(__name__)

class NowCertsClient:
    """Client for interacting with NowCerts API"""
    
    def __init__(self, config: JakeBotConfig):
        self.api_key = config.NOWCERTS_API_KEY
        self.base_url = "https://api.nowcerts.com/api"
        self.max_retries = config.MAX_RETRIES
        
    async def _make_request(self, method: str, endpoint: str, 
                          **kwargs) -> Dict[str, Any]:
        """Make API request with error handling"""
        async with aiohttp.ClientSession() as session:
            try:
                kwargs['headers'] = self._get_headers()
                async with session.request(method, 
                                         f"{self.base_url}/{endpoint}", 
                                         **kwargs) as response:
                    
                    response_data = await response.json()
                    
                    # Handle rate limiting
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 60))
                        raise RetryableError(
                            "Rate limit exceeded",
                            retry_after=retry_after
                        )
                    
                    # Handle authentication errors
                    if response.status == 401:
                        raise NowCertsError(
                            "Invalid API credentials",
                            error_code='AUTH001',
                            status_code=401,
                            response_data=response_data
                        )
                    
                    # Handle validation errors
                    if response.status == 400:
                        raise ValidationError(
                            response_data.get('message', 'Invalid request data'),
                            details=response_data
                        )
                    
                    # Handle other errors
                    if response.status != 200:
                        error_message = response_data.get('message', 'Unknown error')
                        error_code = response_data.get('code')
                        raise NowCertsError(
                            error_message,
                            error_code=error_code,
                            status_code=response.status,
                            response_data=response_data
                        )
                    
                    return response_data
                    
            except aiohttp.ClientError as e:
                raise NowCertsError(
                    f"Network error: {str(e)}",
                    details={'original_error': str(e)}
                )
            except json.JSONDecodeError as e:
                raise NowCertsError(
                    "Invalid JSON response",
                    details={'response_text': await response.text()}
                )
    
    @backoff.on_exception(
        backoff.expo,
        RetryableError,
        max_tries=3
    )
    async def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a task using Zapier/InsertTask endpoint"""
        try:
            return await self._make_request(
                'POST',
                'Zapier/InsertTask',
                json=task_data
            )
        except ValidationError as e:
            logger.error(f"Invalid task data: {e.details}")
            raise
        except NowCertsError as e:
            logger.error(f"Failed to create task: {e.message}")
            raise

    async def find_policy(self, policy_number: str) -> Dict[str, Any]:
        """Find policy using FindPolicies endpoint"""
        return await self._make_request(
            'GET',
            f"Policy/FindPolicies",
            params={
                "Number": policy_number,
            }
        )

    async def update_policy(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update policy using Policy/Insert endpoint"""
        return await self._make_request(
            'POST',
            'Policy/Insert',
            json=policy_data
        )

    async def get_policy_files(self, insured_id: str, policy_id: str) -> Dict[str, Any]:
        """Get policy files list"""
        return await self._make_request(
            'GET',
            f"Policy/GetPolicyFilesList",
            params={
                "insuredId": insured_id,
                "policyId": policy_id
            }
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Api-Version": "2.1.5"  # From API docs
        } 