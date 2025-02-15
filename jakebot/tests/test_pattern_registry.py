import pytest
from datetime import datetime, timedelta
from ai_agents.patterns.registry import PatternRegistry, PatternStats

@pytest.fixture
def registry():
    return PatternRegistry()

class TestPatternRegistry:
    def test_initial_patterns_loaded(self, registry):
        """Test that core patterns are loaded on initialization"""
        insurance_patterns = registry.get_patterns("insurance")
        crm_patterns = registry.get_patterns("crm")
        
        assert len(insurance_patterns) > 0
        assert len(crm_patterns) > 0
    
    def test_pattern_stats_recording(self, registry):
        """Test recording and retrieving pattern statistics"""
        # Record some matches
        registry.record_match(
            system="insurance",
            pattern_type="document_sending",
            confidence=0.9,
            processing_time=100
        )
        
        registry.record_match(
            system="insurance",
            pattern_type="document_sending",
            confidence=0.8,
            processing_time=150,
            is_false_positive=True
        )
        
        # Get stats
        stats = registry.get_pattern_stats("insurance")
        doc_stats = stats["insurance:document_sending"]
        
        assert doc_stats.matches == 1
        assert doc_stats.false_positives == 1
        assert 0.8 <= doc_stats.avg_confidence <= 0.9
        assert len(doc_stats.processing_time_ms) == 2
    
    def test_underperforming_patterns(self, registry):
        """Test identification of problematic patterns"""
        # Record poor performance for a pattern
        for _ in range(10):
            registry.record_match(
                system="insurance",
                pattern_type="test_pattern",
                confidence=0.6,
                processing_time=100,
                is_false_positive=True
            )
        
        problematic = registry.get_underperforming_patterns(
            min_confidence=0.7,
            max_false_positive_rate=0.1
        )
        
        assert "insurance:test_pattern" in problematic 