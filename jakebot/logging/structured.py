"""Structured logging configuration"""
import logging
import json
from datetime import datetime
from typing import Dict, Any

class StructuredLogger:
    """Structured logging with context"""
    
    def __init__(self):
        self.logger = logging.getLogger('jakebot')
        self.context = {}
    
    def set_context(self, **kwargs):
        """Set context for all subsequent logs"""
        self.context.update(kwargs)
    
    def log(self, level: int, message: str, **kwargs):
        """Log with structured data"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            **self.context,
            **kwargs
        }
        
        self.logger.log(
            level,
            json.dumps(log_data, default=str)
        )

logger = StructuredLogger() 