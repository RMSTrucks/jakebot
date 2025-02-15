import pytest
from ai_agents.patterns.validator import PatternValidator
from ai_agents.patterns.insurance_patterns import INSURANCE_PATTERNS
from ai_agents.patterns.crm_patterns import CRM_PATTERNS

@pytest.fixture
def validator():
    return PatternValidator()

class TestPatternValidator:
    def test_valid_pattern(self, validator):
        pattern = {
            "pattern": r"I(?:'ll| will) (?:send|email) (?:you )?(?:the )?(?P<what>.*?)(?P<when>today|tomorrow)(?:\s|$)",
            "system": "NowCerts",
            "requires_approval": False,
            "priority": "normal",
            "type": "document_sending"
        }
        
        assert validator.validate_pattern(pattern) == True
    
    def test_invalid_pattern_missing_fields(self, validator):
        pattern = {
            "pattern": r"I will send (?P<what>.*?)(?P<when>today)",
            "system": "NowCerts"
        }
        
        assert validator.validate_pattern(pattern) == False
    
    def test_invalid_system(self, validator):
        pattern = {
            "pattern": r"I will send (?P<what>.*?)(?P<when>today)",
            "system": "InvalidSystem",
            "requires_approval": False,
            "priority": "normal",
            "type": "test"
        }
        
        assert validator.validate_pattern(pattern) == False
    
    def test_pattern_conflicts(self, validator):
        patterns = [
            {
                "pattern": r"I will send (?P<what>.*?)(?P<when>today)",
                "system": "NowCerts",
                "requires_approval": False,
                "priority": "normal",
                "type": "test1"
            },
            {
                "pattern": r"I will send (?P<what>.*?)(?P<when>today)",
                "system": "NowCerts",
                "requires_approval": False,
                "priority": "normal",
                "type": "test2"
            }
        ]
        
        conflicts = validator.check_pattern_conflicts(patterns)
        assert len(conflicts) > 0
    
    def test_all_insurance_patterns_valid(self, validator):
        assert validator.validate_all_patterns(INSURANCE_PATTERNS) == True
    
    def test_all_crm_patterns_valid(self, validator):
        assert validator.validate_all_patterns(CRM_PATTERNS) == True 