from typing import List, Optional, Tuple
from datetime import datetime
import re
import logging
import time
from dataclasses import dataclass

from .time_parser import TimeParser, ParsedTime
from .patterns.insurance_patterns import INSURANCE_PATTERNS
from .patterns.crm_patterns import CRM_PATTERNS
from .patterns.registry import PatternRegistry

logger = logging.getLogger(__name__)

@dataclass
class Commitment:
    """Represents a commitment made during a call"""
    description: str
    system: str  # "CRM", "NowCerts", etc.
    due_date: Optional[datetime] = None
    assignee: Optional[str] = None
    requires_approval: bool = False
    priority: str = "normal"
    source_text: str = ""  # Original text that generated this commitment
    confidence: float = 1.0  # Confidence in the commitment detection

class CommitmentDetector:
    """Enhanced commitment detection with pattern registry and metrics"""
    
    def __init__(self):
        self.time_parser = TimeParser()
        self.pattern_registry = PatternRegistry()
        self.commitment_patterns = [
            *INSURANCE_PATTERNS,
            *CRM_PATTERNS
        ]

    def detect_commitments(self, transcript: str) -> List[Commitment]:
        """Detect commitments with performance tracking"""
        commitments = []
        
        # Clean up transcript
        transcript = transcript.replace("\r", "\n")
        lines = transcript.split("\n")
        
        for line in lines:
            if not line.strip().lower().startswith("agent:"):
                continue
                
            message = line.split(":", 1)[1].strip()
            
            # Process each system's patterns
            for system in ["insurance", "crm"]:
                for pattern_dict in self.pattern_registry.get_patterns(system):
                    start_time = time.time()
                    matches = re.finditer(pattern_dict["pattern"], message, re.IGNORECASE)
                    
                    for match in matches:
                        try:
                            commitment = self._process_match(
                                match, pattern_dict, message, system
                            )
                            if commitment:
                                commitments.append(commitment)
                                
                            # Record pattern performance
                            processing_time = int((time.time() - start_time) * 1000)
                            self.pattern_registry.record_match(
                                system=system,
                                pattern_type=pattern_dict["type"],
                                confidence=commitment.confidence if commitment else 0.0,
                                processing_time=processing_time,
                                is_false_positive=not commitment
                            )
                            
                        except Exception as e:
                            logger.error(f"Error processing match: {str(e)}")
                            continue
        
        # Log underperforming patterns
        problematic = self.pattern_registry.get_underperforming_patterns()
        if problematic:
            logger.warning(f"Underperforming patterns detected: {problematic}")
            
        return commitments
    
    def _process_match(self, match, pattern_dict: dict, 
                      message: str, system: str) -> Optional[Commitment]:
        """Process a single pattern match with validation"""
        try:
            what = match.group("what").strip() if "what" in match.groupdict() else ""
            when = match.group("when").strip() if "when" in match.groupdict() else ""
            
            # Parse time with confidence
            parsed_time = self.time_parser.parse_time(when)
            
            # Basic validation
            if not what or not parsed_time.due_date:
                return None
                
            # Create commitment
            commitment = Commitment(
                description=what,
                system=system,
                due_date=parsed_time.due_date,
                requires_approval=pattern_dict["requires_approval"],
                priority=self._determine_priority(
                    pattern_dict["priority"], 
                    what, 
                    parsed_time
                ),
                source_text=message,
                confidence=parsed_time.confidence
            )
            
            return commitment
            
        except Exception as e:
            logger.error(f"Error creating commitment: {str(e)}")
            return None

    def _determine_priority(self, base_priority: str, description: str, parsed_time: ParsedTime) -> str:
        """Determine final priority based on multiple factors"""
        
        # Start with base priority
        if base_priority == "high":
            priority_score = 3
        elif base_priority == "normal":
            priority_score = 2
        else:
            priority_score = 1
            
        # Adjust for time urgency
        if parsed_time.due_date and (parsed_time.due_date - datetime.now()).days < 1:
            priority_score += 1
            
        # Adjust for specific keywords
        urgent_keywords = ["urgent", "asap", "immediately", "emergency"]
        if any(keyword in description.lower() for keyword in urgent_keywords):
            priority_score += 1
            
        # Convert score back to priority level
        if priority_score >= 4:
            return "high"
        elif priority_score >= 2:
            return "normal"
        else:
            return "low" 