"""Transaction management for multi-system operations"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class TransactionStep:
    operation: str
    system: str
    data: Dict[str, Any]
    rollback_fn: Optional[callable] = None

class TransactionManager:
    """Manage multi-system transactions with rollback"""
    
    def __init__(self):
        self.completed_steps: List[TransactionStep] = []
        
    async def execute_step(self, step: TransactionStep) -> Dict[str, Any]:
        """Execute a transaction step with rollback capability"""
        try:
            logger.info(f"Executing step: {step.operation} on {step.system}")
            result = await step.operation(**step.data)
            self.completed_steps.append(step)
            return result
            
        except Exception as e:
            logger.error(f"Transaction step failed: {str(e)}")
            await self.rollback()
            raise TransactionError(
                str(e),
                step=step.operation,
                completed_steps=[s.operation for s in self.completed_steps]
            )
    
    async def rollback(self):
        """Rollback completed steps in reverse order"""
        for step in reversed(self.completed_steps):
            if step.rollback_fn:
                try:
                    await step.rollback_fn(step.data)
                except Exception as e:
                    logger.error(f"Rollback failed for {step.operation}: {str(e)}") 