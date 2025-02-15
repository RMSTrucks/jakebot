"""Tests for task status tracking"""
import pytest
from datetime import datetime, timedelta
from jakebot.workflow.task_status import TaskStatus, TaskStatusTracker

@pytest.fixture
def tracker():
    """Create a fresh task tracker for each test"""
    return TaskStatusTracker()

@pytest.fixture
def sample_task_data():
    """Sample task data for testing"""
    return {
        "commitment": {
            "description": "Send policy documents",
            "due_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "type": "document_sending"
        },
        "system": "NowCerts",
        "call_id": "call_123",
        "task_data": {
            "id": "task_123",
            "status": "pending"
        }
    }

class TestTaskStatusTracker:
    def test_add_task(self, tracker, sample_task_data):
        """Test adding a new task"""
        task_id = "task_123"
        tracker.add_task(task_id, sample_task_data)
        
        assert task_id in tracker.tasks
        assert tracker.tasks[task_id]["status"] == TaskStatus.PENDING
        assert "created_at" in tracker.tasks[task_id]
        assert len(tracker.tasks[task_id]["status_history"]) == 1
    
    def test_update_status(self, tracker, sample_task_data):
        """Test updating task status"""
        task_id = "task_123"
        tracker.add_task(task_id, sample_task_data)
        
        tracker.update_status(
            task_id, 
            TaskStatus.IN_PROGRESS, 
            notes="Started processing"
        )
        
        task = tracker.get_task_status(task_id)
        assert task["status"] == TaskStatus.IN_PROGRESS
        assert len(task["status_history"]) == 2
        assert task["status_history"][-1]["notes"] == "Started processing"
    
    def test_task_not_found(self, tracker):
        """Test error handling for non-existent tasks"""
        with pytest.raises(ValueError) as exc:
            tracker.get_task_status("nonexistent")
        assert "not found" in str(exc.value)
    
    def test_status_history(self, tracker, sample_task_data):
        """Test status history tracking"""
        task_id = "task_123"
        tracker.add_task(task_id, sample_task_data)
        
        # Simulate task lifecycle
        statuses = [
            (TaskStatus.IN_PROGRESS, "Started"),
            (TaskStatus.NEEDS_APPROVAL, "Needs manager review"),
            (TaskStatus.COMPLETED, "Approved and completed")
        ]
        
        for status, note in statuses:
            tracker.update_status(task_id, status, notes=note)
        
        task = tracker.get_task_status(task_id)
        history = task["status_history"]
        
        assert len(history) == 4  # Initial + 3 updates
        assert history[0]["status"] == TaskStatus.PENDING
        assert history[-1]["status"] == TaskStatus.COMPLETED
        assert history[-1]["notes"] == "Approved and completed" 