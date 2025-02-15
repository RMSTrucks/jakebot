from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Commitment:
    """Represents a commitment made during a call"""
    description: str
    due_date: datetime = None
    assignee: str = None
    requires_approval: bool = False
    system: str = "CRM"  # Can be "CRM" or "NowCerts"

class BaseAgent:
    """Base class for AI agents that process call transcripts"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.model_name = model_name
    
    def extract_commitments(self, transcript: str) -> List[Commitment]:
        """Extract commitments from call transcript"""
        raise NotImplementedError("Subclasses must implement extract_commitments") 