import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from ai_agents.time_parser import TimeParser, ParsedTime

@pytest.fixture
def parser():
    return TimeParser()

@pytest.fixture
def reference_date():
    return datetime(2024, 1, 1, 10, 0, tzinfo=ZoneInfo("America/New_York"))

class TestTimeParser:
    def test_specific_times(self, parser, reference_date):
        """Test parsing of specific times"""
        cases = [
            ("3:30 pm", 15, 30),
            ("3 pm", 15, 0),
            ("10 am", 10, 0),
            ("noon", 12, 0),
            ("3 o'clock", 15, 0),
        ]
        
        for text, expected_hour, expected_minute in cases:
            result = parser.parse_time(text, reference_date)
            assert result.due_date.hour == expected_hour
            assert result.due_date.minute == expected_minute
            assert result.is_specific == True

    def test_business_terms(self, parser, reference_date):
        """Test parsing of business-related terms"""
        cases = [
            ("end of day", 17, 0),
            ("close of business", 17, 0),
            ("eod", 17, 0),
            ("cob", 17, 0),
        ]
        
        for text, expected_hour, expected_minute in cases:
            result = parser.parse_time(text, reference_date)
            assert result.due_date.hour == expected_hour
            assert result.due_date.minute == expected_minute
            assert result.business_hours == True

    def test_relative_times(self, parser, reference_date):
        """Test parsing of relative times"""
        cases = [
            ("tomorrow morning", 1, 9),
            ("next week", 7, 9),
            ("this afternoon", 0, 14),
            ("this evening", 0, 16),
        ]
        
        for text, days_offset, expected_hour in cases:
            result = parser.parse_time(text, reference_date)
            expected_date = reference_date + timedelta(days=days_offset)
            assert result.due_date.day == expected_date.day
            assert result.due_date.hour == expected_hour

    def test_confidence_levels(self, parser):
        """Test confidence scoring"""
        cases = [
            ("3:30 pm tomorrow", 0.9),
            ("sometime next week", 0.8),
            ("soon", 0.4),
            ("when possible", 0.3),
        ]
        
        for text, expected_confidence in cases:
            result = parser.parse_time(text)
            assert result.confidence == pytest.approx(expected_confidence, abs=0.1)

    def test_business_hours_detection(self, parser, reference_date):
        """Test business hours detection"""
        cases = [
            ("3 pm", True),
            ("6 pm", False),
            ("8 am", False),
            ("10 am", True),
        ]
        
        for text, expected_business_hours in cases:
            result = parser.parse_time(text, reference_date)
            assert result.business_hours == expected_business_hours 

    def test_business_day_handling(self, parser, reference_date):
        """Test business day specific parsing"""
        cases = [
            ("first thing in the morning", 9, 0),
            ("before lunch", 11, 30),
            ("after lunch", 13, 0),
            ("within 2 business days", 2, 17),  # Should skip weekend
            ("next business day", 1, 9),
        ]
        
        for text, days_offset, expected_hour in cases:
            result = parser.parse_time(text, reference_date)
            if days_offset:
                expected_date = parser._adjust_for_business_days(reference_date, days_offset)
                assert result.due_date.day == expected_date.day
            assert result.due_date.hour == expected_hour

    def test_insurance_specific_times(self, parser, reference_date):
        """Test insurance-related time parsing"""
        cases = [
            ("before the policy expires", True),
            ("before coverage ends", True),
            ("before the renewal date", True),
            ("before policy starts", True),
        ]
        
        for text, expected_business_hours in cases:
            result = parser.parse_time(text, reference_date)
            assert result.business_hours == expected_business_hours
            assert result.confidence >= 0.8

    def test_weekend_handling(self, parser):
        """Test handling of weekend dates"""
        # Create a Saturday reference date
        saturday = datetime(2024, 1, 6, 10, 0, tzinfo=ZoneInfo("America/New_York"))
        
        result = parser.parse_time("next business day", saturday)
        # Should be Monday
        assert result.due_date.weekday() == 0  # Monday
        assert result.due_date.hour == 9  # Start of business day

    def test_within_timeframes(self, parser, reference_date):
        """Test parsing of 'within X time' phrases"""
        cases = [
            ("within the hour", 1, "hour"),
            ("within 2 hours", 2, "hour"),
            ("in the next 30 minutes", 30, "minute"),
        ]
        
        for text, amount, unit in cases:
            result = parser.parse_time(text, reference_date)
            if unit == "hour":
                expected_time = reference_date + timedelta(hours=amount)
            else:
                expected_time = reference_date + timedelta(minutes=amount)
            assert result.due_date <= expected_time
            assert result.confidence >= 0.8 