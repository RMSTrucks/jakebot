"""Integration tests for system synchronization"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from jakebot.sync.system_sync import SystemSynchronizer
from jakebot.workflow.task_status import TaskStatus
from jakebot.exceptions import SyncError

@pytest.fixture
def mock_clients():
    """Create mock clients"""
    nowcerts = Mock()
    close = Mock()
    
    # Setup mock responses
    nowcerts.get_task.return_value = {
        "id": "nowcerts_123",
        "type": "policy_update",
        "description": "Update vehicle coverage",
        "status": "pending",
        "due_date": datetime.now().isoformat()
    }
    
    close.get_task.return_value = {
        "id": "close_123",
        "type": "policy_update",
        "description": "Update vehicle coverage",
        "status": "open",
        "due_date": datetime.now().isoformat()
    }
    
    return {
        "nowcerts": nowcerts,
        "close": close
    }

@pytest.fixture
def synchronizer(mock_clients):
    """Create system synchronizer"""
    return SystemSynchronizer(
        mock_clients["nowcerts"],
        mock_clients["close"]
    )

class TestSystemSync:
    async def test_initial_sync(self, synchronizer, mock_clients):
        """Test initial task synchronization"""
        # Setup
        task_id = "nowcerts_123"
        
        # Sync task
        result = await synchronizer.sync_task(task_id, "NowCerts")
        
        # Verify
        assert result["primary_system"] == "NowCerts"
        assert result["primary_task_id"] == task_id
        assert "secondary_task_id" in result
        assert mock_clients["close"].create_task.called
    
    async def test_update_sync(self, synchronizer, mock_clients):
        """Test syncing updates"""
        # Create initial sync
        task_id = "nowcerts_123"
        await synchronizer.sync_task(task_id, "NowCerts")
        
        # Update primary task
        mock_clients["nowcerts"].get_task.return_value["status"] = "completed"
        
        # Sync again
        result = await synchronizer.sync_task(task_id, "NowCerts")
        
        # Verify update was synced
        assert mock_clients["close"].update_task.called
        update_args = mock_clients["close"].update_task.call_args[0][1]
        assert update_args["status"] == "completed"
    
    async def test_sync_error_handling(self, synchronizer, mock_clients):
        """Test error handling during sync"""
        # Setup error condition
        mock_clients["close"].create_task.side_effect = Exception("API Error")
        
        # Attempt sync
        with pytest.raises(SyncError):
            await synchronizer.sync_task("nowcerts_123", "NowCerts")
    
    async def test_verify_sync(self, synchronizer, mock_clients):
        """Test sync verification"""
        # Setup
        task_id = "nowcerts_123"
        await synchronizer.sync_task(task_id, "NowCerts")
        
        # Verify matching tasks
        assert await synchronizer.verify_sync(task_id)
        
        # Test mismatch
        mock_clients["close"].get_task.return_value["status"] = "different_status"
        assert not await synchronizer.verify_sync(task_id) 