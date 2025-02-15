"""Data validation for JakeBot"""
from typing import Dict, Any, List
from datetime import datetime
from jakebot.exceptions import ValidationError

class TaskValidator:
    """Validate task data"""
    
    @staticmethod
    def validate_task(task_data: Dict[str, Any]) -> bool:
        """Validate task data"""
        required_fields = {
            'description': str,
            'due_date': datetime,
            'type': str,
            'system': str
        }
        
        for field, expected_type in required_fields.items():
            if field not in task_data:
                raise ValidationError(f"Missing required field: {field}")
            if not isinstance(task_data[field], expected_type):
                raise ValidationError(
                    f"Invalid type for {field}",
                    field=field,
                    value=task_data[field]
                )
        
        # Add business rules validation
        if task_data.get('priority') == 'high':
            if not task_data.get('approval_required'):
                raise ValidationError(
                    "High priority tasks require approval",
                    field='approval_required'
                )
        
        # Add data sanitization
        task_data['description'] = self.sanitize_text(task_data['description'])
        
        # Add size limits
        if len(task_data['description']) > 1000:
            raise ValidationError(
                "Description too long",
                field='description',
                max_length=1000
            )
        
        return True

class CommitmentValidator:
    """Validate commitment data"""
    
    VALID_SYSTEMS = {'NowCerts', 'CRM'}
    VALID_PRIORITIES = {'low', 'medium', 'high', 'urgent'}
    
    @staticmethod
    def validate_commitment(commitment_data: Dict[str, Any]) -> bool:
        """Validate commitment data"""
        # Basic field validation
        required_fields = {
            'description': str,
            'due_date': datetime,
            'system': str,
            'priority': str
        }
        
        for field, expected_type in required_fields.items():
            if field not in commitment_data:
                raise ValidationError(f"Missing required field: {field}")
            if not isinstance(commitment_data[field], expected_type):
                raise ValidationError(
                    f"Invalid type for {field}",
                    field=field,
                    value=commitment_data[field]
                )
        
        # System validation
        if commitment_data['system'] not in CommitmentValidator.VALID_SYSTEMS:
            raise ValidationError(
                f"Invalid system: {commitment_data['system']}",
                field='system',
                value=commitment_data['system']
            )
        
        # Priority validation
        if commitment_data['priority'].lower() not in CommitmentValidator.VALID_PRIORITIES:
            raise ValidationError(
                f"Invalid priority: {commitment_data['priority']}",
                field='priority',
                value=commitment_data['priority']
            )
        
        return True 