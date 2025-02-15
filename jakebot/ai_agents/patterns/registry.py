"""Pattern registry for managing and validating commitment patterns"""
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass
from datetime import datetime

from .validator import PatternValidator
from .insurance_patterns import INSURANCE_PATTERNS
from .crm_patterns import CRM_PATTERNS

logger = logging.getLogger(__name__)

@dataclass
class PatternStats:
    """Statistics for a single pattern"""
    matches: int = 0
    false_positives: int = 0
    avg_confidence: float = 0.0
    last_matched: Optional[datetime] = None
    processing_time_ms: List[int] = None
    
    def __post_init__(self):
        self.processing_time_ms = []

class PatternRegistry:
    """Central registry for managing commitment patterns"""
    
    def __init__(self):
        self.validator = PatternValidator()
        self._patterns: Dict[str, List[Dict]] = {}
        self._stats: Dict[str, PatternStats] = {}
        
        # Initialize with our core patterns
        self.register_patterns("insurance", INSURANCE_PATTERNS)
        self.register_patterns("crm", CRM_PATTERNS)
    
    def register_patterns(self, system: str, patterns: List[Dict]) -> bool:
        """Register patterns for a system after validation"""
        try:
            if self.validator.validate_all_patterns(patterns):
                self._patterns[system] = patterns
                # Initialize stats for new patterns
                for pattern in patterns:
                    pattern_id = f"{system}:{pattern['type']}"
                    if pattern_id not in self._stats:
                        self._stats[pattern_id] = PatternStats()
                logger.info(f"Successfully registered {len(patterns)} patterns for {system}")
                return True
            else:
                logger.error(f"Failed to validate patterns for {system}")
                return False
        except Exception as e:
            logger.error(f"Error registering patterns for {system}: {str(e)}")
            return False
    
    def get_patterns(self, system: Optional[str] = None) -> List[Dict]:
        """Get all patterns or patterns for a specific system"""
        if system:
            return self._patterns.get(system, [])
        return [p for patterns in self._patterns.values() for p in patterns]
    
    def record_match(self, system: str, pattern_type: str, confidence: float, 
                    processing_time: int, is_false_positive: bool = False):
        """Record pattern match statistics"""
        pattern_id = f"{system}:{pattern_type}"
        if pattern_id not in self._stats:
            self._stats[pattern_id] = PatternStats()
        
        stats = self._stats[pattern_id]
        if is_false_positive:
            stats.false_positives += 1
        else:
            stats.matches += 1
            stats.last_matched = datetime.now()
        
        # Update running average confidence
        total_matches = stats.matches + stats.false_positives
        stats.avg_confidence = (
            (stats.avg_confidence * (total_matches - 1) + confidence) / total_matches
        )
        
        stats.processing_time_ms.append(processing_time)
        # Keep only last 1000 processing times
        if len(stats.processing_time_ms) > 1000:
            stats.processing_time_ms = stats.processing_time_ms[-1000:]
    
    def get_pattern_stats(self, system: Optional[str] = None) -> Dict[str, PatternStats]:
        """Get statistics for all patterns or patterns in a specific system"""
        if system:
            return {
                k: v for k, v in self._stats.items() 
                if k.startswith(f"{system}:")
            }
        return self._stats
    
    def get_underperforming_patterns(self, 
                                   min_confidence: float = 0.7,
                                   max_false_positive_rate: float = 0.1) -> List[str]:
        """Identify patterns that might need improvement"""
        problematic = []
        for pattern_id, stats in self._stats.items():
            total_matches = stats.matches + stats.false_positives
            if total_matches < 10:  # Skip patterns with too few matches
                continue
                
            false_positive_rate = stats.false_positives / total_matches
            if (stats.avg_confidence < min_confidence or 
                false_positive_rate > max_false_positive_rate):
                problematic.append(pattern_id)
        
        return problematic 