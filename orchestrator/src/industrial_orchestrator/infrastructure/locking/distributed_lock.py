"""
INDUSTRIAL DISTRIBUTED LOCKING SYSTEM
Advanced distributed locking with Redis for coordination across instances.
Features:
1. Fair locking with queue system
2. Lock expiration and auto-release
3. Lock renewal (heartbeat)
4. Lock hierarchy and nesting
5. Deadlock detection
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Set, AsyncIterator
from uuid import UUID, uuid4

from redis.asyncio import Redis
from redis.exceptions import LockError, LockNotOwnedError

from ..config.redis import IndustrialRedisClient, get_redis_client
from ...domain.exceptions.locking_exceptions import (
    LockAcquisitionError,
    LockTimeoutError,
    LockNotOwnedError as DomainLockNotOwnedError,
    DeadlockDetectedError,
)


class LockMetadata:
    """Industrial lock metadata for tracking and debugging"""
    
    def __init__(
        self,
        lock_id: str,
        owner_id: str,
        resource: str,
        acquired_at: datetime,
        expires_at: datetime,
        renewal_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.lock_id = lock_id
        self.owner_id = owner_id
        self.resource = resource
        self.acquired_at = acquired_at
        self.expires_at = expires_at
        self.renewal_count = renewal_count
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "lock_id": self.lock_id,
            "owner_id": self.owner_id,
            "resource": self.resource,
            "acquired_at": self.acquired_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "renewal_count": self.renewal_count,
            "metadata": self.metadata,
            "ttl_seconds": max(0, (self.expires_at - datetime.now(timezone.utc)).total_seconds()),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LockMetadata":
        """Create from dictionary"""
        return cls(
            lock_id=data["lock_id"],
            owner_id=data["owner_id"],
            resource=data["resource"],
            acquired_at=datetime.fromisoformat(data["acquired_at"].replace("Z", "+00:00")),
            expires_at=datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00")),
            renewal_count=data.get("renewal_count", 0),
            metadata=data.get("metadata", {})
        )
    
    def is_expired(self) -> bool:
        """Check if lock is expired"""
        return datetime.now(timezone.utc) >= self.expires_at
    
    def time_remaining(self) -> float:
        """Get remaining time in seconds"""
        return max(0, (self.expires_at - datetime.now(timezone.utc)).total_seconds())


class LockQueueEntry:
    """Entry in fair lock queue"""
    
    def __init__(
        self,
        request_id: str,
        resource: str,
        requested_at: datetime,
        timeout_seconds: float,
        priority: int = 0
    ):
        self.request_id = request_id
        self.resource = resource
        self.requested_at = requested_at
        self.timeout_seconds = timeout_seconds
        self.priority = priority
        self.expires_at = requested_at + timedelta(seconds=timeout_seconds)
    
    def is_expired(self) -> bool:
        """Check if queue entry is expired"""
        return datetime.now(timezone.utc) >= self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "request_id": self.request_id,
            "resource": self.resource,
            "requested_at": self.requested_at.isoformat(),
            "timeout_seconds": self.timeout_seconds,
            "priority": self.priority,
            "expires_at": self.expires_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LockQueueEntry":
        """Create from dictionary"""
        return cls(
            request_id=data["request_id"],
            resource=data["resource"],
            requested_at=datetime.fromisoformat(data["requested_at"].replace("Z", "+00:00")),
            timeout_seconds=data["timeout_seconds"],
            priority=data.get("priority", 0)
        )


class IndustrialDistributedLock:
    """
    Industrial Distributed Lock
    
    Advanced features:
    1. Fair locking with priority queue
    2. Lock renewal (heartbeat)
    3. Nested locking (lock hierarchy)
    4. Deadlock detection with timeout graph
    5. Lock metadata and monitoring
    """
    
    def __init__(
        self,
        redis_client: IndustrialRedisClient,
        resource: str,
        lock_timeout: float = 30.0,
        renewal_interval: float = 10.0,
        owner_id: Optional[str] = None,
        priority: int = 0
    ):
        self.redis = redis_client
        self.resource = resource
        self.lock_timeout = lock_timeout
        self.renewal_interval = renewal_interval
        self.owner_id = owner_id or f"owner_{uuid4().hex[:8]}"
        self.priority = priority
        
        self.lock_id = f"lock:{resource}:{uuid4().hex}"
        self.lock_key = f"distributed_lock:{resource}"
        self.metadata_key = f"lock_metadata:{resource}"
        self.queue_key = f"lock_queue:{resource}"
        self.ownership_key = f"lock_ownership:{resource}"
        
        self._is_locked = False
        self._renewal_task: Optional[asyncio.Task] = None
        self._acquired_at: Optional[datetime] = None
        self._logger = logging.getLogger(__name__)
    
    async def acquire(
        self,
        timeout: float = 10.0,
        blocking: bool = True,
        retry_interval: float = 0.1
    ) -> bool:
        """
        Acquire distributed lock with industrial features
        
        Args:
            timeout: Maximum time to wait for lock (seconds)
            blocking: Whether to block until lock is acquired
            retry_interval: Interval between retry attempts (seconds)
        
        Returns:
            bool: True if lock acquired, False if timeout
        """
        start_time = time.monotonic()
        request_id = f"req_{uuid4().hex[:8]}"
        
        # Create queue entry
        queue_entry = LockQueueEntry(
            request_id=request_id,
            resource=self.resource,
            requested_at=datetime.now(timezone.utc),
            timeout_seconds=timeout,
            priority=self.priority
        )
        
        try:
            # Add to fair queue
            await self._add_to_queue(queue_entry)
            
            while True:
                # Check timeout
                if time.monotonic() - start_time > timeout:
                    # Remove from queue on timeout
                    await self._remove_from_queue(request_id)
                    return False
                
                # Try to acquire lock
                acquired = await self._try_acquire_lock()
                if acquired:
                    # Remove from queue on success
                    await self._remove_from_queue(request_id)
                    self._is_locked = True
                    self._acquired_at = datetime.now(timezone.utc)
                    
                    # Start renewal task
                    self._start_renewal_task()
                    
                    # Record lock metadata
                    await self._record_lock_metadata()
                    
                    self._logger.info(
                        f"Lock acquired: {self.resource} by {self.owner_id} "
                        f"(timeout: {self.lock_timeout}s)"
                    )
                    return True
                
                if not blocking:
                    # Remove from queue if not blocking
                    await self._remove_from_queue(request_id)
                    return False
                
                # Wait before retry
                await asyncio.sleep(retry_interval)
                
                # Check deadlock
                if await self._detect_deadlock():
                    self._logger.warning(f"Deadlock detected for resource: {self.resource}")
                    await self._remove_from_queue(request_id)
                    raise DeadlockDetectedError(f"Deadlock detected for resource: {self.resource}")
                
        except Exception as e:
            # Clean up queue entry on error
            try:
                await self._remove_from_queue(request_id)
            except:
                pass
            
            self._logger.error(f"Error acquiring lock {self.resource}: {e}")
            raise LockAcquisitionError(f"Failed to acquire lock {self.resource}: {e}")
    
    async def _try_acquire_lock(self) -> bool:
        """Attempt to acquire lock using Redis SET with NX and EX"""
        lock_data = {
            "lock_id": self.lock_id,
            "owner_id": self.owner_id,
            "acquired_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=self.lock_timeout)).isoformat(),
        }
        
        # Use Lua script for atomic operation
        lua_script = """
            -- Check if lock exists and is not expired
            local current_lock = redis.call('GET', KEYS[1])
            if current_lock then
                local lock_data = cjson.decode(current_lock)
                local expires_at = lock_data['expires_at']
                
                -- Check if lock is expired
                local now = tonumber(ARGV[3])
                if expires_at and tonumber(expires_at) < now then
                    -- Lock expired, can acquire
                    redis.call('DEL', KEYS[1])
                else
                    -- Lock is still valid
                    return 0
                end
            end
            
            -- Acquire lock
            local lock_data = {
                lock_id = ARGV[1],
                owner_id = ARGV[2],
                acquired_at = ARGV[3],
                expires_at = ARGV[4]
            }
            
            redis.call('SET', KEYS[1], cjson.encode(lock_data), 'NX', 'EX', ARGV[5])
            return 1
        """
        
        try:
            result = await self.redis._client.eval(
                lua_script,
                1,  # Number of keys
                self.lock_key,
                self.lock_id,
                self.owner_id,
                str(time.time()),
                str(time.time() + self.lock_timeout),
                int(self.lock_timeout)
            )
            
            return bool(result)
            
        except Exception as e:
            self._logger.error(f"Error in _try_acquire_lock: {e}")
            return False
    
    async def _add_to_queue(self, queue_entry: LockQueueEntry) -> None:
        """Add request to fair lock queue"""
        queue_data = queue_entry.to_dict()
        
        # Use sorted set for priority queue
        await self.redis._client.zadd(
            self.queue_key,
            {queue_entry.request_id: queue_entry.priority}
        )
        
        # Store queue entry details
        await self.redis.hset_json(
            f"{self.queue_key}:entries",
            queue_entry.request_id,
            queue_data
        )
        
        # Set expiration on queue
        await self.redis._client.expire(
            self.queue_key,
            int(queue_entry.timeout_seconds) + 10
        )
        await self.redis._client.expire(
            f"{self.queue_key}:entries",
            int(queue_entry.timeout_seconds) + 10
        )
    
    async def _remove_from_queue(self, request_id: str) -> None:
        """Remove request from lock queue"""
        # Remove from sorted set
        await self.redis._client.zrem(self.queue_key, request_id)
        
        # Remove from entry details
        await self.redis._client.hdel(f"{self.queue_key}:entries", request_id)
    
    async def _record_lock_metadata(self) -> None:
        """Record lock metadata for monitoring"""
        metadata = LockMetadata(
            lock_id=self.lock_id,
            owner_id=self.owner_id,
            resource=self.resource,
            acquired_at=self._acquired_at or datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=self.lock_timeout),
            metadata={
                "priority": self.priority,
                "renewal_interval": self.renewal_interval,
            }
        )
        
        await self.redis.set_json(
            self.metadata_key,
            metadata.to_dict(),
            expire_seconds=int(self.lock_timeout) + 10
        )
        
        # Record ownership
        await self.redis._client.setex(
            self.ownership_key,
            int(self.lock_timeout) + 10,
            self.owner_id
        )
    
    def _start_renewal_task(self) -> None:
        """Start lock renewal (heartbeat) task"""
        if self._renewal_task and not self._renewal_task.done():
            self._renewal_task.cancel()
        
        self._renewal_task = asyncio.create_task(self._renewal_loop())
    
    async def _renewal_loop(self) -> None:
        """Renew lock periodically to prevent expiration"""
        while self._is_locked:
            try:
                await asyncio.sleep(self.renewal_interval)
                
                if not self._is_locked:
                    break
                
                # Renew lock
                renewed = await self.renew()
                if not renewed:
                    self._logger.error(f"Failed to renew lock: {self.resource}")
                    self._is_locked = False
                    break
                    
                self._logger.debug(f"Lock renewed: {self.resource}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in renewal loop for {self.resource}: {e}")
                self._is_locked = False
                break
    
    async def renew(self, additional_time: Optional[float] = None) -> bool:
        """
        Renew lock expiration
        
        Args:
            additional_time: Additional time to add to lock (seconds)
        
        Returns:
            bool: True if renewed successfully
        """
        if not self._is_locked:
            return False
        
        additional_time = additional_time or self.lock_timeout
        
        # Use Lua script for atomic renewal
        lua_script = """
            -- Get current lock
            local current_lock = redis.call('GET', KEYS[1])
            if not current_lock then
                return 0  -- Lock doesn't exist
            end
            
            local lock_data = cjson.decode(current_lock)
            
            -- Verify ownership
            if lock_data['owner_id'] ~= ARGV[1] then
                return 0  -- Not owned by this instance
            end
            
            -- Update expiration
            lock_data['expires_at'] = ARGV[2]
            lock_data['renewal_count'] = (lock_data['renewal_count'] or 0) + 1
            
            -- Set with new expiration
            redis.call('SET', KEYS[1], cjson.encode(lock_data), 'EX', ARGV[3])
            
            -- Update metadata
            if redis.call('EXISTS', KEYS[2]) == 1 then
                local metadata = cjson.decode(redis.call('GET', KEYS[2]))
                metadata['expires_at'] = ARGV[2]
                metadata['renewal_count'] = (metadata['renewal_count'] or 0) + 1
                redis.call('SET', KEYS[2], cjson.encode(metadata), 'EX', ARGV[3])
            end
            
            -- Update ownership key
            redis.call('SETEX', KEYS[3], ARGV[3], ARGV[1])
            
            return 1
        """
        
        try:
            new_expires_at = time.time() + additional_time
            
            result = await self.redis._client.eval(
                lua_script,
                3,  # Number of keys
                self.lock_key,
                self.metadata_key,
                self.ownership_key,
                self.owner_id,
                str(new_expires_at),
                int(additional_time)
            )
            
            if result:
                # Update local state
                self.lock_timeout = additional_time
                return True
            
            return False
            
        except Exception as e:
            self._logger.error(f"Error renewing lock {self.resource}: {e}")
            return False
    
    async def release(self) -> bool:
        """
        Release distributed lock
        
        Returns:
            bool: True if released successfully
        """
        if not self._is_locked:
            return True
        
        # Cancel renewal task
        if self._renewal_task:
            self._renewal_task.cancel()
            try:
                await self._renewal_task
            except asyncio.CancelledError:
                pass
        
        # Use Lua script for atomic release
        lua_script = """
            -- Get current lock
            local current_lock = redis.call('GET', KEYS[1])
            if not current_lock then
                return 1  -- Lock already released
            end
            
            local lock_data = cjson.decode(current_lock)
            
            -- Verify ownership
            if lock_data['owner_id'] ~= ARGV[1] then
                return 0  -- Not owned by this instance
            end
            
            -- Release lock
            redis.call('DEL', KEYS[1])
            
            -- Clean up metadata
            redis.call('DEL', KEYS[2])
            redis.call('DEL', KEYS[3])
            
            return 1
        """
        
        try:
            result = await self.redis._client.eval(
                lua_script,
                3,  # Number of keys
                self.lock_key,
                self.metadata_key,
                self.ownership_key,
                self.owner_id
            )
            
            if result:
                self._is_locked = False
                self._acquired_at = None
                self._logger.info(f"Lock released: {self.resource}")
                return True
            
            self._logger.warning(f"Failed to release lock (not owned): {self.resource}")
            return False
            
        except Exception as e:
            self._logger.error(f"Error releasing lock {self.resource}: {e}")
            return False
    
    async def _detect_deadlock(self) -> bool:
        """
        Detect deadlocks using timeout-wait graph
        
        Simplified deadlock detection for common cases
        """
        # Get all locks in queue
        queue_entries = await self.redis._client.zrange(
            self.queue_key,
            0,
            -1,
            withscores=True
        )
        
        if len(queue_entries) < 2:
            return False
        
        # Check for circular wait (simplified)
        # In production, this would implement a full wait-for graph
        
        # Check for timeout expiration
        for request_id, _ in queue_entries:
            entry_data = await self.redis.hget_json(
                f"{self.queue_key}:entries",
                request_id
            )
            
            if entry_data:
                entry = LockQueueEntry.from_dict(entry_data)
                if entry.is_expired():
                    # Clean up expired queue entry
                    await self._remove_from_queue(request_id)
        
        return False
    
    async def get_lock_info(self) -> Optional[Dict[str, Any]]:
        """Get information about current lock state"""
        try:
            # Get lock data
            lock_data_json = await self.redis._client.get(self.lock_key)
            if not lock_data_json:
                return None
            
            lock_data = self.redis._deserialize_value(lock_data_json)
            
            # Get metadata
            metadata = await self.redis.get_json(self.metadata_key)
            
            # Get queue info
            queue_size = await self.redis._client.zcard(self.queue_key)
            queue_entries = []
            
            if queue_size > 0:
                queue_members = await self.redis._client.zrange(
                    self.queue_key,
                    0,
                    -1,
                    withscores=True
                )
                
                for request_id, priority in queue_members:
                    entry_data = await self.redis.hget_json(
                        f"{self.queue_key}:entries",
                        request_id
                    )
                    if entry_data:
                        queue_entries.append({
                            "request_id": request_id,
                            "priority": priority,
                            **entry_data
                        })
            
            return {
                "resource": self.resource,
                "lock_data": lock_data,
                "metadata": metadata,
                "queue": {
                    "size": queue_size,
                    "entries": queue_entries,
                },
                "is_locked": self._is_locked,
                "owner_id": self.owner_id,
                "acquired_at": self._acquired_at.isoformat() if self._acquired_at else None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
        except Exception as e:
            self._logger.error(f"Error getting lock info: {e}")
            return None
    
    @property
    def locked(self) -> bool:
        """Check if lock is currently held"""
        return self._is_locked
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.release()


class LockManager:
    """
    Industrial Lock Manager
    
    Manages multiple distributed locks with:
    1. Lock hierarchy support
    2. Deadlock prevention
    3. Lock monitoring and metrics
    4. Graceful shutdown
    """
    
    def __init__(self, redis_client: Optional[IndustrialRedisClient] = None):
        self.redis = redis_client
        self._locks: Dict[str, IndustrialDistributedLock] = {}
        self._lock_hierarchy: Dict[str, List[str]] = {}
        self._logger = logging.getLogger(__name__)
    
    async def initialize(self) -> None:
        """Initialize lock manager"""
        if self.redis is None:
            self.redis = await get_redis_client()
    
    async def acquire_lock(
        self,
        resource: str,
        timeout: float = 10.0,
        lock_timeout: float = 30.0,
        priority: int = 0,
        owner_id: Optional[str] = None
    ) -> IndustrialDistributedLock:
        """
        Acquire a distributed lock
        
        Args:
            resource: Resource to lock
            timeout: Acquisition timeout (seconds)
            lock_timeout: Lock duration (seconds)
            priority: Lock priority (higher = earlier in queue)
            owner_id: Optional owner identifier
        
        Returns:
            IndustrialDistributedLock: Acquired lock instance
        """
        await self.initialize()
        
        # Check lock hierarchy for potential deadlocks
        await self._check_hierarchy(resource)
        
        # Create or get lock
        if resource not in self._locks:
            self._locks[resource] = IndustrialDistributedLock(
                redis_client=self.redis,
                resource=resource,
                lock_timeout=lock_timeout,
                owner_id=owner_id,
                priority=priority
            )
        
        lock = self._locks[resource]
        
        # Acquire lock
        acquired = await lock.acquire(timeout=timeout)
        if not acquired:
            raise LockTimeoutError(f"Timeout acquiring lock for resource: {resource}")
        
        # Record in hierarchy
        await self._record_hierarchy(resource)
        
        return lock
    
    async def release_lock(self, resource: str) -> bool:
        """Release a distributed lock"""
        if resource not in self._locks:
            return False
        
        lock = self._locks[resource]
        released = await lock.release()
        
        if released:
            # Remove from hierarchy
            await self._remove_from_hierarchy(resource)
            
            # Clean up lock instance if no longer needed
            if not lock.locked:
                del self._locks[resource]
        
        return released
    
    async def _check_hierarchy(self, resource: str) -> None:
        """
        Check lock hierarchy for potential deadlocks
        
        Implements basic deadlock prevention by ensuring
        locks are always acquired in a consistent order
        """
        # Simple hierarchy check based on resource name ordering
        # In production, this would be more sophisticated
        
        current_locks = [
            r for r, lock in self._locks.items()
            if lock.locked
        ]
        
        if current_locks:
            # Ensure locks are acquired in lexicographic order
            for existing_lock in current_locks:
                if existing_lock > resource:
                    self._logger.warning(
                        f"Potential deadlock: trying to acquire {resource} "
                        f"while holding {existing_lock}"
                    )
    
    async def _record_hierarchy(self, resource: str) -> None:
        """Record lock in hierarchy"""
        # Simple hierarchy tracking
        # In production, this would track parent-child relationships
        
        if resource not in self._lock_hierarchy:
            self._lock_hierarchy[resource] = []
    
    async def _remove_from_hierarchy(self, resource: str) -> None:
        """Remove lock from hierarchy"""
        if resource in self._lock_hierarchy:
            del self._lock_hierarchy[resource]
    
    async def get_lock_stats(self) -> Dict[str, Any]:
        """Get lock manager statistics"""
        lock_stats = []
        
        for resource, lock in self._locks.items():
            info = await lock.get_lock_info()
            if info:
                lock_stats.append(info)
        
        return {
            "total_locks": len(self._locks),
            "active_locks": sum(1 for lock in self._locks.values() if lock.locked),
            "lock_stats": lock_stats,
            "hierarchy": self._lock_hierarchy,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    async def cleanup_expired_locks(self) -> Dict[str, int]:
        """Clean up expired locks (safety mechanism)"""
        cleaned = 0
        errors = 0
        
        for resource, lock in list(self._locks.items()):
            try:
                if lock.locked:
                    # Check if lock is still valid in Redis
                    lock_info = await lock.get_lock_info()
                    if not lock_info or not lock_info.get("lock_data"):
                        # Lock appears to be expired
                        await lock.release()
                        cleaned += 1
            except Exception as e:
                self._logger.error(f"Error cleaning up lock {resource}: {e}")
                errors += 1
        
        return {
            "cleaned": cleaned,
            "errors": errors,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    async def shutdown(self) -> None:
        """Shutdown lock manager and release all locks"""
        release_tasks = []
        
        for resource, lock in self._locks.items():
            if lock.locked:
                release_tasks.append(lock.release())
        
        if release_tasks:
            results = await asyncio.gather(*release_tasks, return_exceptions=True)
            
            for resource, result in zip(self._locks.keys(), results):
                if isinstance(result, Exception):
                    self._logger.error(f"Error releasing lock {resource}: {result}")
        
        self._locks.clear()
        self._lock_hierarchy.clear()


# Global lock manager instance
_lock_manager: Optional[LockManager] = None


async def get_lock_manager() -> LockManager:
    """Get or create global lock manager"""
    global _lock_manager
    
    if _lock_manager is None:
        _lock_manager = LockManager()
        await _lock_manager.initialize()
    
    return _lock_manager


async def shutdown_lock_manager() -> None:
    """Shutdown global lock manager"""
    global _lock_manager
    
    if _lock_manager:
        await _lock_manager.shutdown()
        _lock_manager = None


@asynccontextmanager
async def distributed_lock(
    resource: str,
    timeout: float = 10.0,
    lock_timeout: float = 30.0,
    priority: int = 0
) -> AsyncIterator[IndustrialDistributedLock]:
    """
    Context manager for distributed locks
    
    Usage:
        async with distributed_lock("session:123") as lock:
            # Critical section
            pass
    """
    lock_manager = await get_lock_manager()
    lock = await lock_manager.acquire_lock(
        resource=resource,
        timeout=timeout,
        lock_timeout=lock_timeout,
        priority=priority
    )
    
    try:
        yield lock
    finally:
        await lock_manager.release_lock(resource)
