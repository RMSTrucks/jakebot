"""Configuration management for JakeBot"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class JakeBotConfig:
    """Central configuration for JakeBot"""
    # API Keys & Endpoints
    CLOSE_API_KEY: str = os.getenv('CLOSE_API_KEY', '')
    NOWCERTS_API_KEY: str = os.getenv('NOWCERTS_API_KEY', '')
    
    # Feature Flags
    ENABLE_PII_DETECTION: bool = os.getenv('ENABLE_PII_DETECTION', 'true').lower() == 'true'
    REQUIRE_APPROVAL: bool = os.getenv('REQUIRE_APPROVAL', 'true').lower() == 'true'
    
    # Operational Settings
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))
    
    def validate(self) -> bool:
        """Validate required configuration"""
        if not self.CLOSE_API_KEY:
            raise ValueError("CLOSE_API_KEY is required")
        return True 