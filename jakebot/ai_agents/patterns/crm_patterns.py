"""CRM-specific commitment patterns"""
from typing import List, Dict, Any

CRM_PATTERNS: List[Dict[str, Any]] = [
    # Follow-up patterns
    {
        "pattern": r"I(?:'ll| will) (?:call|contact|follow up with) (?:you )?(?:about )?(?P<what>.*?)(?P<when>today|tomorrow|next week|soon|by .+?|within .+?)(?:\s|$)",
        "system": "CRM",
        "requires_approval": False,
        "priority": "normal",
        "type": "follow_up"
    },
    
    # Research patterns
    {
        "pattern": r"I(?:'ll| will) (?:look into|research|check on|verify) (?:the )?(?P<what>.*?)(?P<when>today|tomorrow|next week|soon|by .+?|within .+?)(?:\s|$)",
        "system": "CRM",
        "requires_approval": False,
        "priority": "normal",
        "type": "research"
    },
    
    # Review patterns
    {
        "pattern": r"I(?:'ll| will) (?:review|go over) (?:the )?(?P<what>.*?)(?P<when>today|tomorrow|next week|soon|by .+?|within .+?)(?:\s|$)",
        "system": "CRM",
        "requires_approval": False,
        "priority": "normal",
        "type": "review"
    }
] 