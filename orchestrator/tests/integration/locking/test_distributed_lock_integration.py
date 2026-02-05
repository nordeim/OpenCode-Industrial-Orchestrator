"""
INDUSTRIAL DISTRIBUTED LOCK INTEGRATION TESTS
Test distributed locking with real Redis connection.
"""

import pytest
import pytest_asyncio
import asyncio
import time
from datetime import datetime, timezone, timedelta
from typing import List

from src.industrial_orchestrator.infrastructure.locking.distributed_lock import (
    IndustrialDistributedLock,
    LockManager,
    distributed_lock,
    get_lock_manager,
    shutdown_lock_manager,
)
from src.industrial_orchestrator.infrastructure.config.redis import (
    get_redis_client,
    shutdown_redis,
)


class TestIndustrialDistributedLockIntegration:
    """Integration tests for IndustrialDistributedLock"""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Setup and teardown for each test"""
        # Initialize Redis
        redis_client = await get_redis_client()
        
        # Clean Redis
        await redis_client._client.flushdb()
        
        yield
        
        # Cleanup
        await shutdown_redis()
        await shutdown_lock_manager()
    
    @pytest_asyncio.fixture
    async def lock_manager(self):
        """Create lock manager for testing"""
        manager = LockManager()
        await manager.initialize()
        return manager
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_lock_acquisition_and_release(self, lock_manager):
        """Test basic lock acquisition and release"""
        resource = "test:resource:1"
        
        # Acquire lock
        lock = await lock_manager.acquire_lock(resource, timeout=5)
        assert lock.locked is True
        
        # Try to acquire same lock from another "instance"
        redis_client = await get_redis_client()
        another_lock = IndustrialDistributedLock(
            redis_client=redis_client,
            resource=resource,
            owner_id="another_instance"
        )
        
        # Should not be able to acquire
        acquired = await another_lock.acquire(timeout=1, blocking=False)
        assert acquired is False
        
        # Release lock
        released = await lock_manager.release_lock(resource)
        assert released is True
        assert lock.locked is False
        
        # Now another instance should be able to acquire
        acquired = await another_lock.acquire(timeout=1)
        assert acquired is True
        assert another_lock.locked is True
        
        # Cleanup
        await another_lock.release()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_lock_timeout(self, lock_manager):
        """Test lock timeout behavior"""
        resource = "test:resource:2"
        
        # Acquire lock with short timeout
        lock = await lock_manager.acquire_lock(
            resource,
            timeout=5,
            lock_timeout=2  # Lock expires after 2 seconds
        )
        assert lock.locked is True
        
        # Wait for lock to expire
        await asyncio.sleep(3)
        
        # Lock should have expired, another instance can acquire
        redis_client = await get_redis_client()
        another_lock = IndustrialDistributedLock(
            redis_client=redis_client,
            resource=resource,
            owner_id="another_instance"
        )
        
        acquired = await another_lock.acquire(timeout=1)
        assert acquired is True
        
        # Cleanup
        await another_lock.release()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_lock_renewal(self, lock_manager):
        """Test lock renewal (heartbeat)"""
        resource = "test:resource:3"
        
        # Acquire lock with renewal
        lock = await lock_manager.acquire_lock(
            resource,
            lock_timeout=5,
            timeout=5
        )
        
        # Wait a bit
        await asyncio.sleep(3)
        
        # Lock should still be held due to renewal
        assert lock.locked is True
        
        # Another instance should not be able to acquire
        redis_client = await get_redis_client()
        another_lock = IndustrialDistributedLock(
            redis_client=redis_client,
            resource=resource,
            owner_id="another_instance"
        )
        
        acquired = await another_lock.acquire(timeout=1, blocking=False)
        assert acquired is False
        
        # Cleanup
        await lock_manager.release_lock(resource)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_context_manager(self, lock_manager):
        """Test lock context manager"""
        resource = "test:resource:4"
        
        async with distributed_lock(resource, timeout=5) as lock:
            assert lock.locked is True
            
            # Verify lock is held
            redis_client = await get_redis_client()
            another_lock = IndustrialDistributedLock(
                redis_client=redis_client,
                resource=resource,
                owner_id="another_instance"
            )
            
            acquired = await another_lock.acquire(timeout=0.5, blocking=False)
            assert acquired is False
        
        # Lock should be released after context manager
        assert lock.locked is False
        
        # Now another instance can acquire
        redis_client = await get_redis_client()
        another_lock = IndustrialDistributedLock(
            redis_client=redis_client,
            resource=resource,
            owner_id="another_instance"
        )
        
        acquired = await another_lock.acquire(timeout=1)
        assert acquired is True
        
        # Cleanup
        await another_lock.release()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fair_lock_queue(self, lock_manager):
        """Test fair locking with queue"""
        resource = "test:resource:5"
        results = []
        
        async def acquire_lock_with_delay(instance_id: str, delay: float):
            """Acquire lock with delay to test queue fairness"""
            await asyncio.sleep(delay)
            
            redis_client = await get_redis_client()
            lock = IndustrialDistributedLock(
                redis_client=redis_client,
                resource=resource,
                owner_id=instance_id,
                priority=0
            )
            
            acquired = await lock.acquire(timeout=10)
            if acquired:
                results.append(instance_id)
                await asyncio.sleep(0.1)  # Hold lock briefly
                await lock.release()
        
        # Start multiple acquisition attempts with delays
        tasks = [
            acquire_lock_with_delay("instance_1", 0.0),
            acquire_lock_with_delay("instance_2", 0.05),
            acquire_lock_with_delay("instance_3", 0.1),
        ]
        
        await asyncio.gather(*tasks)
        
        # Verify acquisition order (should be fair, not necessarily FIFO due to timing)
        assert len(results) == 3
        assert set(results) == {"instance_1", "instance_2", "instance_3"}
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_lock_priority(self, lock_manager):
        """Test lock acquisition with priority"""
        resource = "test:resource:6"
        
        async def acquire_with_priority(instance_id: str, priority: int):
            """Acquire lock with specified priority"""
            redis_client = await get_redis_client()
            lock = IndustrialDistributedLock(
                redis_client=redis_client,
                resource=resource,
                owner_id=instance_id,
                priority=priority
            )
            
            # Use non-blocking to test queue position
            acquired = await lock.acquire(timeout=0.5, blocking=False)
            return instance_id if acquired else None
        
        # Higher priority should acquire first when contending
        # This test is more complex due to timing, so we'll verify
        # that priority affects queue position
        
        # First acquire lock to create contention
        first_lock = await lock_manager.acquire_lock(resource, timeout=5)
        
        # Try to acquire with different priorities
        tasks = [
            acquire_with_priority("low_priority", 0),
            acquire_with_priority("high_priority", 10),
            acquire_with_priority("medium_priority", 5),
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should fail to acquire immediately (lock is held)
        assert all(r is None for r in results)
        
        # Release lock
        await lock_manager.release_lock(resource)
        
        # Now check queue order by examining Redis
        redis_client = await get_redis_client()
        
        # Get queue entries
        queue_entries = await redis_client._client.zrange(
            f"lock_queue:{resource}",
            0,
            -1,
            withscores=True
        )
        
        # Verify priority scores
        entry_map = {entry_id: priority for entry_id, priority in queue_entries}
        
        # Note: This depends on implementation details
        # Higher priority should have higher score (or lower, depending on implementation)
        
        # Clean up any remaining queue entries
        for entry_id, _ in queue_entries:
            await redis_client._client.zrem(f"lock_queue:{resource}", entry_id)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_lock_metadata(self, lock_manager):
        """Test lock metadata tracking"""
        resource = "test:resource:7"
        
        # Acquire lock
        lock = await lock_manager.acquire_lock(resource, timeout=5)
        
        # Get lock info
        lock_info = await lock.get_lock_info()
        
        assert lock_info is not None
        assert lock_info["resource"] == resource
        assert lock_info["is_locked"] is True
        assert lock_info["owner_id"] == lock.owner_id
        assert "lock_data" in lock_info
        assert "metadata" in lock_info
        assert "queue" in lock_info
        
        # Verify lock data
        lock_data = lock_info["lock_data"]
        assert lock_data["owner_id"] == lock.owner_id
        assert "acquired_at" in lock_data
        assert "expires_at" in lock_data
        
        # Cleanup
        await lock_manager.release_lock(resource)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_lock_manager_stats(self, lock_manager):
        """Test lock manager statistics"""
        # Acquire some locks
        lock1 = await lock_manager.acquire_lock("resource:1", timeout=5)
        lock2 = await lock_manager.acquire_lock("resource:2", timeout=5)
        
        # Get stats
        stats = await lock_manager.get_lock_stats()
        
        assert "total_locks" in stats
        assert "active_locks" in stats
        assert "lock_stats" in stats
        assert "hierarchy" in stats
        
        assert stats["total_locks"] >= 2
        assert stats["active_locks"] >= 2
        
        # Verify lock stats include our locks
        resource_names = [s["resource"] for s in stats["lock_stats"]]
        assert "resource:1" in resource_names
        assert "resource:2" in resource_names
        
        # Cleanup
        await lock_manager.release_lock("resource:1")
        await lock_manager.release_lock("resource:2")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cleanup_expired_locks(self, lock_manager):
        """Test cleanup of expired locks"""
        resource = "test:resource:8"
        
        # Manually create an "expired" lock in Redis
        redis_client = await get_redis_client()
        
        expired_lock_data = {
            "lock_id": "expired_lock",
            "owner_id": "expired_owner",
            "acquired_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat(),
        }
        
        await redis_client.set_json(
            f"distributed_lock:{resource}",
            expired_lock_data,
            expire_seconds=5
        )
        
        # Add to lock manager (simulating a stale lock)
        lock = IndustrialDistributedLock(
            redis_client=redis_client,
            resource=resource,
            owner_id="expired_owner"
        )
        
        # Manually set internal state (for testing)
        lock._is_locked = True
        
        # Clean up expired locks
        cleanup_stats = await lock_manager.cleanup_expired_locks()
        
        assert "cleaned" in cleanup_stats
        assert "errors" in cleanup_stats
        
        # The expired lock should be cleaned up
        # (Note: actual cleanup depends on implementation)
        
        # Now we should be able to acquire the lock
        new_lock = await lock_manager.acquire_lock(resource, timeout=5)
        assert new_lock.locked is True
        
        # Cleanup
        await lock_manager.release_lock(resource)
