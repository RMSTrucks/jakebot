"""Task status tracking"""
from enum import Enum
from typing import Dict, Optional
from datetime import datetime

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_APPROVAL = "needs_approval"
    REJECTED = "rejected"

class TaskStatusTracker:
    """Track status of tasks across systems"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        
    def add_task(self, task_id: str, task_data: Dict):
        """Add a new task to tracking"""
        self.tasks[task_id] = {
            **task_data,
            "status": TaskStatus.PENDING,
            "created_at": datetime.now(),
            "last_updated": datetime.now(),
            "status_history": [{
                "status": TaskStatus.PENDING,
                "timestamp": datetime.now()
            }]
        }
    
    def update_status(self, task_id: str, status: TaskStatus, 
                     notes: Optional[str] = None):
        """Update task status"""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
            
        self.tasks[task_id]["status"] = status
        self.tasks[task_id]["last_updated"] = datetime.now()
        self.tasks[task_id]["status_history"].append({
            "status": status,
            "timestamp": datetime.now(),
            "notes": notes
        })
    
    def get_task_status(self, task_id: str) -> Dict:
        """Get current task status"""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        return self.tasks[task_id] 