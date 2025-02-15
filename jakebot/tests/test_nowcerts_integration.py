"""Integration tests for NowCerts API with error scenarios"""
import pytest
import os
from datetime import datetime, timedelta
import aiohttp
import json
from unittest.mock import patch, MagicMock
import asyncio

from jakebot.config import JakeBotConfig
from jakebot.integrations.nowcerts.client import NowCertsClient
from jakebot.exceptions import NowCertsError, RetryableError, ValidationError

@pytest.mark.asyncio
class TestNowCertsIntegration:
    """Test NowCerts API integration"""
    
    @pytest.fixture
    def mock_response(self):
        """Mock aiohttp response"""
        mock = MagicMock()
        mock.status = 200
        mock.json = MagicMock()
        return mock
    
    @pytest.fixture
    def client(self):
        """Create NowCerts client with test config"""
        config = JakeBotConfig()
        return NowCertsClient(config)
    
    async def test_network_timeout(self, mock_response, client):
        """Test network timeout handling"""
        mock_response.side_effect = aiohttp.ClientTimeout("Request timed out")
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(NowCertsError) as exc:
                await client.create_task({})
                assert "Request timed out" in str(exc.value)
    
    async def test_malformed_json_response(self, mock_response, client):
        """Test handling of invalid JSON responses"""
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = MagicMock(return_value="Invalid response")
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(NowCertsError) as exc:
                await client.create_task({})
                assert "Invalid JSON response" in str(exc.value)
    
    async def test_policy_not_found(self, mock_response, client):
        """Test policy not found scenario"""
        mock_response.status = 404
        mock_response.json.return_value = {
            'message': 'Policy not found',
            'code': 'POL001'
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(NowCertsError) as exc:
                await client.find_policy("NONEXISTENT-001")
                assert exc.value.error_code == 'POL001'
    
    async def test_concurrent_requests(self, client):
        """Test handling multiple concurrent requests"""
        tasks = []
        for i in range(5):
            task_data = {
                "type": f"Test Task {i}",
                "description": f"Concurrent test task {i}",
                "due_date": (datetime.now() + timedelta(days=1)).isoformat(),
                "priority": "Medium"
            }
            tasks.append(client.create_task(task_data))
        
        # Should handle concurrent requests without issues
        results = await asyncio.gather(*tasks, return_exceptions=True)
        assert len([r for r in results if not isinstance(r, Exception)]) > 0
    
    async def test_large_policy_update(self, client):
        """Test updating policy with large data payload"""
        large_policy_data = {
            "policy_number": "TEST-001",
            "vehicles": [
                {
                    "vin": f"VIN{i}",
                    "make": "Test Make",
                    "model": "Test Model",
                    "year": 2024
                }
                for i in range(50)  # Large number of vehicles
            ],
            "drivers": [
                {
                    "name": f"Driver {i}",
                    "license": f"LIC{i}"
                }
                for i in range(20)  # Multiple drivers
            ]
        }
        
        response = await client.update_policy(large_policy_data)
        assert response.get('success') == True
    
    async def test_retry_with_backoff(self, mock_response, client):
        """Test retry behavior with exponential backoff"""
        mock_response.status = 429
        mock_response.headers = {'Retry-After': '2'}
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            start_time = datetime.now()
            with pytest.raises(RetryableError):
                await client.create_task({})
            duration = (datetime.now() - start_time).total_seconds()
            
            # Should have attempted retries with exponential backoff
            assert duration >= 2
            assert mock_post.call_count > 1
    
    async def test_policy_file_download(self, mock_response, client):
        """Test downloading policy files"""
        mock_response.status = 200
        mock_response.json.return_value = {
            'files': [
                {
                    'id': 'file1',
                    'name': 'policy.pdf',
                    'url': 'https://example.com/file1'
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value = mock_response
            
            response = await client.get_policy_files("INS-001", "POL-001")
            assert 'files' in response
            assert len(response['files']) > 0
    
    @pytest.mark.parametrize("error_status,error_code", [
        (400, 'VAL001'),
        (401, 'AUTH001'),
        (403, 'AUTH002'),
        (404, 'POL001'),
        (500, 'SRV001'),
    ])
    async def test_error_status_codes(self, mock_response, client, error_status, error_code):
        """Test various error status codes"""
        mock_response.status = error_status
        mock_response.json.return_value = {
            'message': f'Test error {error_status}',
            'code': error_code
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(NowCertsError) as exc:
                await client.create_task({})
                assert exc.value.error_code == error_code
                assert exc.value.status_code == error_status

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 