"""Insurance-specific commitment patterns"""
from typing import List, Dict, Any

INSURANCE_PATTERNS: List[Dict[str, Any]] = [
    # Document handling
    {
        "pattern": r"I(?:'ll| will) (?:send|email|forward) (?:you )?(?:the )?(?P<what>.*?)(?P<when>today|tomorrow|next week|soon|by .+?|within .+?)(?:\s|$)",
        "system": "NowCerts",
        "requires_approval": False,
        "priority": "normal",
        "type": "document_sending"
    },
    
    # Policy updates
    {
        "pattern": r"I(?:'ll| will) (?:update|modify|change) (?:the )?(?P<what>policy|coverage|limits?|deductible).*?(?P<when>today|tomorrow|next week|soon|by .+?|within .+?)(?:\s|$)",
        "system": "NowCerts",
        "requires_approval": True,
        "priority": "high",
        "type": "policy_update"
    },
    
    # Vehicle updates
    {
        "pattern": r"I(?:'ll| will) (?:add|remove|update) (?:the )?(?P<what>vehicle|car|truck|auto).*?(?P<when>today|tomorrow|next week|soon|by .+?|within .+?)(?:\s|$)",
        "system": "NowCerts",
        "requires_approval": True,
        "priority": "high",
        "type": "vehicle_update"
    },
    
    # Coverage adjustments
    {
        "pattern": r"I(?:'ll| will) (?:increase|decrease|adjust) (?:the )?(?P<what>coverage limits?|liability limits?|deductible amounts?).*?(?P<when>today|tomorrow|next week|soon|by .+?|within .+?)(?:\s|$)",
        "system": "NowCerts",
        "requires_approval": True,
        "priority": "high",
        "type": "coverage_adjustment"
    },
    
    # Endorsements
    {
        "pattern": r"I(?:'ll| will) (?:add|process) (?:the )?(?P<what>endorsement|policy change|rider).*?(?P<when>today|tomorrow|next week|soon|by .+?|within .+?)(?:\s|$)",
        "system": "NowCerts",
        "requires_approval": True,
        "priority": "high",
        "type": "endorsement"
    },
    
    # Certificates
    {
        "pattern": r"I(?:'ll| will) (?:send|prepare|issue) (?:the |a )?(?P<what>certificate of insurance|COI|proof of insurance).*?(?P<when>today|tomorrow|next week|soon|by .+?|within .+?)(?:\s|$)",
        "system": "NowCerts",
        "requires_approval": False,
        "priority": "high",
        "type": "certificate"
    }
] 