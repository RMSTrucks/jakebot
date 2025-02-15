"""Custom exceptions for task management"""
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TaskError(Exception):
    """Base exception for task-related errors"""
    def __init__(self, message: str, task_id: Optional[str] = None):
        self.message = message
        self.task_id = task_id
        super().__init__(self.message)

class TaskCreationError(TaskError):
    """Error creating a task"""
    pass

class TaskUpdateError(TaskError):
    """Error updating a task"""
    pass

class TaskNotFoundError(TaskError):
    """Task not found"""
    pass

class SystemError(Exception):
    """Error with external system"""
    def __init__(self, message: str, system: str):
        self.message = message
        self.system = system
        super().__init__(f"{system}: {message}")

class JakeBotError(Exception):
    """Base exception for all JakeBot errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()
        super().__init__(self.message)
        logger.error(f"{self.__class__.__name__}: {message}", extra=self.details)

class APIError(JakeBotError):
    """Base API error"""
    pass

class NowCertsAPIError(APIError):
    """NowCerts specific API errors"""
    ERROR_CODES = {
        'AUTH001': 'Authentication failed',
        'RATE001': 'Rate limit exceeded',
        'POL001': 'Policy not found',
        'POL002': 'Invalid policy data',
        'TASK001': 'Task creation failed',
        'SYNC001': 'Synchronization failed'
    }
    
    def __init__(self, message: str, error_code: str, **kwargs):
        super().__init__(
            f"NowCerts API Error ({error_code}): {message}",
            details={
                'error_code': error_code,
                'error_description': self.ERROR_CODES.get(error_code, 'Unknown error'),
                **kwargs
            }
        )

class CloseAPIError(APIError):
    """Close.com specific API errors"""
    ERROR_CODES = {
        'AUTH001': 'Invalid API key',
        'RATE001': 'Rate limit exceeded',
        'LEAD001': 'Lead not found',
        'CALL001': 'Call not found',
        'TASK001': 'Task creation failed'
    }
    
    def __init__(self, message: str, error_code: str, **kwargs):
        super().__init__(
            f"Close.com API Error ({error_code}): {message}",
            details={
                'error_code': error_code,
                'error_description': self.ERROR_CODES.get(error_code, 'Unknown error'),
                **kwargs
            }
        )

class RetryableError(JakeBotError):
    """Errors that should trigger a retry"""
    def __init__(self, message: str, retry_after: Optional[int] = None, 
                 attempt: int = 1, max_attempts: int = 3):
        super().__init__(message, {
            'retry_after': retry_after,
            'attempt': attempt,
            'max_attempts': max_attempts
        })

class ValidationError(JakeBotError):
    """Data validation errors"""
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        super().__init__(
            message,
            details={'field': field, 'invalid_value': str(value)}
        )

class WorkflowError(JakeBotError):
    """Workflow execution errors"""
    def __init__(self, message: str, step: str, context: Dict[str, Any]):
        super().__init__(
            f"Workflow error in {step}: {message}",
            details={'workflow_step': step, 'context': context}
        )

class CommitmentError(JakeBotError):
    """Commitment detection/processing errors"""
    pass

# System-specific errors
class NowCertsError(APIError):
    """NowCerts-specific errors"""
    ERROR_CODES = {
        'AUTH001': 'Invalid API credentials',
        'POL001': 'Policy not found',
        'POL002': 'Invalid policy data',
        'TASK001': 'Failed to create task',
    }

class CloseError(APIError):
    """Close.com-specific errors"""
    pass

class SlackError(APIError):
    """Slack-specific errors"""
    pass

# Sync Errors
class SyncError(JakeBotError):
    """Base synchronization error"""
    pass

class TaskSyncError(SyncError):
    """Task synchronization errors"""
    def __init__(self, message: str, task_id: str, source_system: str, target_system: str, **kwargs):
        super().__init__(
            f"Task sync error: {message}",
            details={
                'task_id': task_id,
                'source_system': source_system,
                'target_system': target_system,
                **kwargs
            }
        )

# Performance Errors
class PerformanceError(JakeBotError):
    """Performance-related errors"""
    def __init__(self, message: str, threshold: float, actual: float, **kwargs):
        super().__init__(
            f"Performance error: {message}",
            details={
                'threshold': threshold,
                'actual': actual,
                **kwargs
            }
        ) 