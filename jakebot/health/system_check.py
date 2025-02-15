"""System health monitoring"""
import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

class SystemHealthCheck:
    """Monitor system health and dependencies"""
    
    def __init__(self, config, clients):
        self.config = config
        self.clients = clients
        
    async def check_all_systems(self) -> Dict[str, bool]:
        """Check all system dependencies"""
        results = {}
        
        # Check Close.com
        results['close'] = await self.check_close()
        
        # Check NowCerts
        results['nowcerts'] = await self.check_nowcerts()
        
        # Check task sync
        results['sync'] = await self.check_sync()
        
        return results
    
    async def check_close(self) -> bool:
        """Check Close.com API health"""
        try:
            await self.clients['close'].get_status()
            return True
        except Exception as e:
            logger.error(f"Close.com health check failed: {str(e)}")
            return False
            
    async def check_nowcerts(self) -> bool:
        """Check NowCerts API health"""
        try:
            await self.clients['nowcerts'].get_status()
            return True
        except Exception as e:
            logger.error(f"NowCerts health check failed: {str(e)}")
            return False
    
    async def check_sync(self) -> bool:
        """Check system synchronization"""
        try:
            # Create test task
            task = await self.clients['nowcerts'].create_task({
                'type': 'test',
                'description': 'Health check'
            })
            
            # Verify sync
            synced = await self.clients['sync'].verify_sync(task['id'])
            
            # Cleanup
            await self.clients['nowcerts'].delete_task(task['id'])
            
            return synced
            
        except Exception as e:
            logger.error(f"Sync health check failed: {str(e)}")
            return False 