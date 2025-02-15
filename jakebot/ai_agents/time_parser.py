from typing import Optional, Tuple
from datetime import datetime, timedelta
import re
import logging
from dataclasses import dataclass
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

@dataclass
class ParsedTime:
    """Represents a parsed time commitment"""
    due_date: datetime
    confidence: float  # 0.0 to 1.0
    is_specific: bool  # Whether the time was specifically mentioned
    original_text: str
    business_hours: bool = True  # Whether it's during business hours

class TimeParser:
    """Advanced time parsing for commitments"""
    
    def __init__(self, timezone: str = "America/New_York"):
        self.timezone = ZoneInfo(timezone)
        self.business_hours = {
            'start': 9,  # 9 AM
            'end': 17    # 5 PM
        }
        
        # Time pattern definitions
        self.time_patterns = [
            # Specific times
            (r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', 0.9),  # "3:30 pm", "3 pm"
            (r'(\d{1,2})(?::(\d{2}))?\s*o[\'']clock', 0.9),  # "3 o'clock"
            
            # Time ranges
            (r'between\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*and\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)', 0.8),
            
            # Time periods
            (r'morning', 0.7),
            (r'afternoon', 0.7),
            (r'evening', 0.7),
            (r'noon', 0.9),
            (r'midnight', 0.9),
            
            # Business terms
            (r'end of (?:the )?day', 0.8),
            (r'close of business', 0.8),
            (r'eod', 0.8),
            (r'cob', 0.8),
        ]
        
        # Date pattern definitions
        self.date_patterns = [
            # Specific dates
            (r'(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?', 0.9),  # "3/15", "3/15/24"
            
            # Relative dates
            (r'today', 0.9),
            (r'tomorrow', 0.9),
            (r'next (?:week|month)', 0.8),
            (r'in (\d+) (?:day|week|month)s?', 0.8),
            
            # Day names
            (r'(?:this|next) (monday|tuesday|wednesday|thursday|friday)', 0.8),
            
            # Fuzzy dates
            (r'soon', 0.4),
            (r'later', 0.3),
            (r'when possible', 0.3),
        ]

        # Enhanced time patterns
        self.time_patterns.extend([
            # Specific business phrases
            (r'first thing (?:in the )?morning', 0.9),
            (r'start of (?:the )?day', 0.9),
            (r'before lunch', 0.8),
            (r'after lunch', 0.8),
            (r'before (?:I|we) leave', 0.7),
            
            # Specific insurance-related times
            (r'before the policy expires', 0.9),
            (r'before coverage ends', 0.9),
            (r'before renewal', 0.9),
            
            # More precise time ranges
            (r'within the hour', 0.9),
            (r'within (\d+) hours?', 0.9),
            (r'in the next (\d+) minutes?', 0.9),
        ])
        
        # Enhanced date patterns
        self.date_patterns.extend([
            # Insurance-specific dates
            (r'before (?:the )?renewal date', 0.9),
            (r'before (?:the )?policy starts?', 0.9),
            (r'before (?:the )?coverage begins?', 0.9),
            
            # More specific relative dates
            (r'early next week', 0.8),
            (r'middle of next week', 0.8),
            (r'end of (?:the )?week', 0.8),
            (r'beginning of next month', 0.8),
            
            # Business day references
            (r'next business day', 0.9),
            (r'within (\d+) business days?', 0.9),
        ])
        
        # Add business day awareness
        self.business_days = {
            0: 'monday',
            1: 'tuesday',
            2: 'wednesday',
            3: 'thursday',
            4: 'friday'
        }

    def parse_time(self, text: str, reference_date: Optional[datetime] = None) -> ParsedTime:
        """
        Parse time from text with confidence scoring
        
        Args:
            text: Text containing time information
            reference_date: Optional reference date (defaults to now)
            
        Returns:
            ParsedTime object with due date and confidence
        """
        if reference_date is None:
            reference_date = datetime.now(self.timezone)

        text = text.lower().strip()
        
        # Try to extract specific time first
        time_match = self._extract_specific_time(text)
        if time_match:
            due_date, confidence = time_match
            return ParsedTime(
                due_date=due_date,
                confidence=confidence,
                is_specific=True,
                original_text=text,
                business_hours=self._is_business_hours(due_date)
            )
        
        # Fall back to relative time parsing
        due_date, confidence = self._parse_relative_time(text, reference_date)
        
        return ParsedTime(
            due_date=due_date,
            confidence=confidence,
            is_specific=False,
            original_text=text,
            business_hours=self._is_business_hours(due_date)
        )

    def _extract_specific_time(self, text: str) -> Optional[Tuple[datetime, float]]:
        """Extract specific time mentions from text"""
        for pattern, base_confidence in self.time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if 'noon' in text:
                        time = datetime.now(self.timezone).replace(
                            hour=12, minute=0, second=0, microsecond=0
                        )
                        return time, base_confidence
                    
                    if 'end of day' in text or 'eod' in text:
                        time = datetime.now(self.timezone).replace(
                            hour=self.business_hours['end'],
                            minute=0, second=0, microsecond=0
                        )
                        return time, base_confidence
                    
                    # Handle AM/PM times
                    if match.groups() and match.group(1):
                        hour = int(match.group(1))
                        minute = int(match.group(2)) if match.group(2) else 0
                        
                        if match.group(3) and match.group(3).lower() == 'pm' and hour < 12:
                            hour += 12
                            
                        time = datetime.now(self.timezone).replace(
                            hour=hour, minute=minute,
                            second=0, microsecond=0
                        )
                        return time, base_confidence
                        
                except ValueError as e:
                    logger.warning(f"Error parsing specific time: {e}")
                    continue
        
        return None

    def _parse_relative_time(self, text: str, reference_date: datetime) -> Tuple[datetime, float]:
        """Parse relative time references"""
        # Default to end of day if no specific time
        default_time = reference_date.replace(
            hour=self.business_hours['end'],
            minute=0, second=0, microsecond=0
        )
        
        # Common relative time mappings
        relative_times = {
            'morning': (9, 0, 0.7),
            'afternoon': (14, 0, 0.7),
            'evening': (16, 0, 0.7),
            'tonight': (18, 0, 0.7),
        }
        
        for term, (hour, minute, confidence) in relative_times.items():
            if term in text:
                return reference_date.replace(
                    hour=hour, minute=minute,
                    second=0, microsecond=0
                ), confidence
        
        # Handle relative dates
        if 'tomorrow' in text:
            next_day = reference_date + timedelta(days=1)
            return next_day.replace(
                hour=self.business_hours['start'],
                minute=0, second=0, microsecond=0
            ), 0.9
            
        if 'next week' in text:
            next_week = reference_date + timedelta(days=7)
            return next_week.replace(
                hour=self.business_hours['start'],
                minute=0, second=0, microsecond=0
            ), 0.8
            
        if 'soon' in text:
            return reference_date + timedelta(days=3), 0.4
            
        # Default to end of current day
        return default_time, 0.6

    def _is_business_hours(self, dt: datetime) -> bool:
        """Check if time is during business hours"""
        return self.business_hours['start'] <= dt.hour < self.business_hours['end']

    def _adjust_for_business_days(self, dt: datetime, days: int) -> datetime:
        """Adjust date to account for business days only"""
        current_day = dt
        remaining_days = days
        
        while remaining_days > 0:
            current_day += timedelta(days=1)
            # Skip weekends
            if current_day.weekday() < 5:  # Monday = 0, Sunday = 6
                remaining_days -= 1
        
        return current_day

    def _parse_business_time(self, text: str, reference_date: datetime) -> Optional[Tuple[datetime, float]]:
        """Parse business-specific time references"""
        
        # First thing in the morning
        if 'first thing' in text or 'start of day' in text:
            return reference_date.replace(
                hour=self.business_hours['start'],
                minute=0, second=0, microsecond=0
            ), 0.9
        
        # Before lunch
        if 'before lunch' in text:
            return reference_date.replace(
                hour=11, minute=30,
                second=0, microsecond=0
            ), 0.8
        
        # After lunch
        if 'after lunch' in text:
            return reference_date.replace(
                hour=13, minute=0,
                second=0, microsecond=0
            ), 0.8
        
        # Business day references
        match = re.search(r'within (\d+) business days?', text)
        if match:
            days = int(match.group(1))
            due_date = self._adjust_for_business_days(reference_date, days)
            return due_date.replace(
                hour=self.business_hours['end'],
                minute=0, second=0, microsecond=0
            ), 0.9
        
        # Next business day
        if 'next business day' in text:
            next_day = self._adjust_for_business_days(reference_date, 1)
            return next_day.replace(
                hour=self.business_hours['start'],
                minute=0, second=0, microsecond=0
            ), 0.9
        
        return None

    def _parse_insurance_specific_time(self, text: str, reference_date: datetime) -> Optional[Tuple[datetime, float]]:
        """Parse insurance-specific time references"""
        
        # Before policy/coverage deadlines
        if any(phrase in text for phrase in ['before policy expires', 'before coverage ends', 'before renewal']):
            # Default to end of current day if no specific policy date is known
            return reference_date.replace(
                hour=self.business_hours['end'],
                minute=0, second=0, microsecond=0
            ), 0.9
        
        # Before policy starts
        if any(phrase in text for phrase in ['before policy starts', 'before coverage begins']):
            # Default to start of next business day if no specific policy date is known
            next_day = self._adjust_for_business_days(reference_date, 1)
            return next_day.replace(
                hour=self.business_hours['start'],
                minute=0, second=0, microsecond=0
            ), 0.9
        
        return None 