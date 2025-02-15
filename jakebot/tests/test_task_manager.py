"""Tests for task management"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from jakebot.workflow.task_manager import TaskManager
from jakebot.workflow.task_status import TaskStatus
from jakebot.exceptions import TaskCreationError, TaskUpdateError
from jakebot.config import JakeBotConfig

@pytest.fixture
def mock_nowcerts():
    """Mock NowCerts client"""
    mock = Mock()
    mock.create_task.return_value = {
        "id": "nowcerts_123",
        "status": "pending"
    }
    return mock

@pytest.fixture
def mock_close():
    """Mock Close client"""
    mock = Mock()
    mock.create_task.return_value = {
        "id": "close_123",
        "status": "open"
    }
    return mock

@pytest.fixture
def task_manager(mock_nowcerts, mock_close):
    """Create TaskManager with mocked dependencies"""
    config = JakeBotConfig()
    manager = TaskManager(config)
    manager.nowcerts_client = mock_nowcerts
    manager.close_client = mock_close
    return manager

@pytest.fixture
def sample_commitment():
    """Sample commitment for testing"""
    return Mock(
        id="comm_123",
        system="NowCerts",
        type="policy_update",
        description="Update vehicle coverage",
        due_date=datetime.now() + timedelta(days=1),
        priority="high",
        requires_approval=True,
        to_dict=lambda: {
            "id": "comm_123",
            "type": "policy_update",
            "description": "Update vehicle coverage"
        }
    )

class TestTaskManager:
    async def test_create_nowcerts_task(self, task_manager, sample_commitment):
        """Test creating a task in NowCerts"""
        call_data = {
            "id": "call_123",
            "date": datetime.now().isoformat()
        }
        
        task = await task_manager.create_task_from_commitment(
            sample_commitment, 
            call_data
        )
        
        assert task["id"] == "nowcerts_123"
        assert task_manager.nowcerts_client.create_task.called
        
        # Verify task is tracked
        tracked_task = task_manager.status_tracker.get_task_status(task["id"])
        assert tracked_task["system"] == "NowCerts"
        assert tracked_task["call_id"] == call_data["id"]
    
    async def test_create_task_failure(self, task_manager, sample_commitment):
        """Test handling of task creation failure"""
        task_manager.nowcerts_client.create_task.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            await task_manager.create_task_from_commitment(
                sample_commitment,
                {"id": "call_123"}
            )
    
    async def test_update_task_status(self, task_manager):
        """Test updating task status"""
        # First create a task
        task_id = "task_123"
        task_manager.status_tracker.add_task(task_id, {
            "system": "NowCerts",
            "commitment": {"id": "comm_123"},
            "task_data": {"id": task_id}
        })
        
        # Update status
        await task_manager.update_task_status(
            task_id,
            TaskStatus.IN_PROGRESS,
            notes="Processing"
        )
        
        # Verify status update
        task = task_manager.status_tracker.get_task_status(task_id)
        assert task["status"] == TaskStatus.IN_PROGRESS
        assert task["status_history"][-1]["notes"] == "Processing"
        assert task_manager.nowcerts_client.update_task.called
    
    async def test_system_specific_handling(self, task_manager, sample_commitment):
        """Test handling of different systems"""
        # Test NowCerts task
        sample_commitment.system = "NowCerts"
        await task_manager.create_task_from_commitment(
            sample_commitment,
            {"id": "call_123"}
        )
        assert task_manager.nowcerts_client.create_task.called
        
        # Test Close task
        sample_commitment.system = "CRM"
        await task_manager.create_task_from_commitment(
            sample_commitment,
            {"id": "call_123"}
        )
        assert task_manager.close_client.create_task.called 