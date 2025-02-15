"""Configuration validation"""
from typing import Dict, Any, List
import os
import json

class ConfigValidator:
    """Validate system configuration"""
    
    REQUIRED_ENV_VARS = {
        'NOWCERTS_API_KEY',
        'CLOSE_API_KEY',
        'LOG_LEVEL',
        'ENVIRONMENT'
    }
    
    def validate_env_vars(self) -> List[str]:
        """Validate required environment variables"""
        missing = []
        for var in self.REQUIRED_ENV_VARS:
            if not os.getenv(var):
                missing.append(var)
        return missing
    
    def validate_config_file(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration file"""
        errors = []
        
        # Check required sections
        required_sections = {'api', 'logging', 'performance'}
        missing_sections = required_sections - set(config.keys())
        if missing_sections:
            errors.append(f"Missing config sections: {missing_sections}")
            
        return errors 