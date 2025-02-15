"""Pattern validation utilities"""
import re
from typing import Dict, List, Set
import logging

logger = logging.getLogger(__name__)

class PatternValidator:
    """Validates commitment patterns for correctness and conflicts"""
    
    REQUIRED_FIELDS = {'pattern', 'system', 'requires_approval', 'priority', 'type'}
    VALID_SYSTEMS = {'CRM', 'NowCerts'}
    VALID_PRIORITIES = {'low', 'normal', 'high'}
    
    def __init__(self):
        self.validated_patterns: List[Dict] = []
    
    def validate_pattern(self, pattern: Dict) -> bool:
        """Validate a single pattern"""
        try:
            # Check required fields
            missing_fields = self.REQUIRED_FIELDS - set(pattern.keys())
            if missing_fields:
                logger.error(f"Missing required fields: {missing_fields}")
                return False
            
            # Validate system
            if pattern['system'] not in self.VALID_SYSTEMS:
                logger.error(f"Invalid system: {pattern['system']}")
                return False
            
            # Validate priority
            if pattern['priority'] not in self.VALID_PRIORITIES:
                logger.error(f"Invalid priority: {pattern['priority']}")
                return False
            
            # Validate regex pattern
            try:
                re.compile(pattern['pattern'])
            except re.error as e:
                logger.error(f"Invalid regex pattern: {e}")
                return False
            
            # Check for required capture groups
            if not all(group in pattern['pattern'] for group in ['(?P<what>', '(?P<when>']):
                logger.error("Pattern missing required capture groups (what/when)")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating pattern: {e}")
            return False
    
    def check_pattern_conflicts(self, patterns: List[Dict]) -> List[str]:
        """Check for potential conflicts between patterns"""
        conflicts = []
        
        for i, pattern1 in enumerate(patterns):
            for j, pattern2 in enumerate(patterns[i+1:], i+1):
                # Check for identical patterns
                if pattern1['pattern'] == pattern2['pattern']:
                    conflicts.append(f"Identical patterns found: {pattern1['type']} and {pattern2['type']}")
                    continue
                
                # Check for overlapping patterns that might cause confusion
                if self._patterns_overlap(pattern1['pattern'], pattern2['pattern']):
                    conflicts.append(
                        f"Potentially overlapping patterns found: "
                        f"{pattern1['type']} and {pattern2['type']}"
                    )
        
        return conflicts
    
    def _patterns_overlap(self, pattern1: str, pattern2: str) -> bool:
        """Check if two patterns might match the same text"""
        # This is a simplified check - could be made more sophisticated
        p1_words = set(re.findall(r'\w+', pattern1))
        p2_words = set(re.findall(r'\w+', pattern2))
        
        # If patterns share many words, they might overlap
        overlap = len(p1_words & p2_words) / len(p1_words | p2_words)
        return overlap > 0.7

    def validate_all_patterns(self, patterns: List[Dict]) -> bool:
        """Validate all patterns and check for conflicts"""
        valid_patterns = []
        
        for pattern in patterns:
            if self.validate_pattern(pattern):
                valid_patterns.append(pattern)
            else:
                logger.warning(f"Invalid pattern found: {pattern['type']}")
        
        conflicts = self.check_pattern_conflicts(valid_patterns)
        if conflicts:
            for conflict in conflicts:
                logger.warning(f"Pattern conflict: {conflict}")
        
        self.validated_patterns = valid_patterns
        return len(valid_patterns) == len(patterns) and not conflicts 