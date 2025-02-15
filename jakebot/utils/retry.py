"""Retry logic for API calls"""
import logging
import asyncio
from typing import Callable, Any, Optional
from functools import wraps
from datetime import datetime

from jakebot.exceptions import RetryableError, APIError
from jakebot.monitoring import MetricsTracker

logger = logging.getLogger(__name__)

class RetryConfig:
    """Configuration for retry behavior"""
    def __init__(self, 
                 max_attempts: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 30.0,
                 exponential_base: float = 2.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

def with_retry(metrics_tracker: Optional[MetricsTracker] = None,
               retry_config: Optional[RetryConfig] = None):
    """Decorator for retrying operations"""
    retry_config = retry_config or RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            start_time = datetime.now()
            
            for attempt in range(retry_config.max_attempts):
                try:
                    result = await func(*args, **kwargs)
                    
                    # Track successful call
                    if metrics_tracker:
                        duration = (datetime.now() - start_time).total_seconds()
                        metrics_tracker.track_api_call(
                            system=func.__module__,
                            endpoint=func.__name__,
                            success=True,
                            duration=duration
                        )
                    
                    return result
                    
                except RetryableError as e:
                    last_exception = e
                    if attempt + 1 < retry_config.max_attempts:
                        delay = min(
                            retry_config.base_delay * (retry_config.exponential_base ** attempt),
                            retry_config.max_delay
                        )
                        
                        logger.warning(
                            f"Retryable error in {func.__name__}, "
                            f"attempt {attempt + 1}/{retry_config.max_attempts}. "
                            f"Retrying in {delay} seconds. Error: {str(e)}"
                        )
                        
                        await asyncio.sleep(delay)
                    continue
                    
                except Exception as e:
                    # Track failed call
                    if metrics_tracker:
                        duration = (datetime.now() - start_time).total_seconds()
                        metrics_tracker.track_api_call(
                            system=func.__module__,
                            endpoint=func.__name__,
                            success=False,
                            duration=duration
                        )
                    
                    raise APIError(
                        f"Operation failed: {str(e)}",
                        details={
                            'function': func.__name__,
                            'attempt': attempt + 1,
                            'args': args,
                            'kwargs': kwargs
                        }
                    )
            
            # If we get here, we've exhausted our retries
            raise last_exception
            
        return wrapper
    return decorator 