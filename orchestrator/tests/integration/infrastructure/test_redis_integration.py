"""
INDUSTRIAL REDIS INTEGRATION TESTS
Test Redis integration with real Redis connection.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from src.industrial_orchestrator.infrastructure.config.redis import (
    IndustrialRedisClient,
    RedisSettings,
    get_redis_client,
    shutdown_redis,
)


class TestIndustrialRedisClientIntegration:
    """Integration tests for IndustrialRedisClient"""
    
    @pytest.fixture
    async def redis_client(self):
        """Create Redis client for testing"""
        settings = RedisSettings(
            host="localhost",
            port=6379,
            database=1,  # Use separate database for tests
            socket_timeout=5.0,
            max_retries=3,
        )
        
        client = IndustrialRedisClient(settings)
        await client.initialize()
        
        # Clean test database
        await client._client.flushdb()
        
        yield client
        
        await client.close()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_connection_initialization(self, redis_client):
        """Test Redis connection initialization"""
        assert redis_client._client is not None
        assert redis_client._pool is not None
        
        # Verify connection works
        result = await redis_client._client.ping()
        assert result is True
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_json_serialization(self, redis_client):
        """Test JSON serialization/deserialization"""
        test_data = {
            "string": "test value",
            "number": 42,
            "float": 3.14159,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        # Set and get JSON
        await redis_client.set_json("test:json", test_data, expire_seconds=10)
        retrieved = await redis_client.get_json("test:json")
        
        assert retrieved == test_data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_hash_operations(self, redis_client):
        """Test hash operations with JSON"""
        test_data = {
            "user": "industrial",
            "score": 100,
            "metadata": {"level": "expert", "active": True},
        }
        
        # Set in hash
        await redis_client.hset_json("test:hash", "field1", test_data)
        
        # Get from hash
        retrieved = await redis_client.hget_json("test:hash", "field1")
        assert retrieved == test_data
        
        # Test non-existent field
        missing = await redis_client.hget_json("test:hash", "nonexistent")
        assert missing is None
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_distributed_lock(self, redis_client):
        """Test distributed lock mechanism"""
        lock_key = "test:lock"
        lock_value = "test-process"
        
        # Acquire lock
        acquired = await redis_client.acquire_lock(
            lock_key,
            lock_value,
            timeout_seconds=5,
            retry_count=1,
        )
        assert acquired is True
        
        # Try to acquire again (should fail)
        acquired2 = await redis_client.acquire_lock(
            lock_key,
            "another-process",
            timeout_seconds=1,
            retry_count=1,
        )
        assert acquired2 is False
        
        # Release lock
        released = await redis_client.release_lock(lock_key, lock_value)
        assert released is True
        
        # Verify lock is released
        acquired3 = await redis_client.acquire_lock(
            lock_key,
            "third-process",
            timeout_seconds=1,
        )
        assert acquired3 is True
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_circuit_breaker(self, redis_client):
        """Test circuit breaker functionality"""
        # Initially should be CLOSED
        status = redis_client._circuit_breaker.get_status()
        assert status["state"] == "CLOSED"
        
        # Record some failures
        for _ in range(5):
            redis_client._circuit_breaker.record_failure()
        
        status = redis_client._circuit_breaker.get_status()
        assert status["failures"] == 5
        
        # Record success to reduce failure count
        redis_client._circuit_breaker.record_success()
        status = redis_client._circuit_breaker.get_status()
        assert status["failures"] == 4  # Should decrease by 1
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_check(self, redis_client):
        """Test Redis health check"""
        health = await redis_client.health_check()
        
        assert "status" in health
        assert "latency_ms" in health
        assert "circuit_breaker" in health
        assert "operations" in health
        
        if health["status"] == "healthy":
            assert health["test_passed"] is True
            assert "redis_version" in health["info"]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_retry_logic(self, redis_client):
        """Test retry logic with failing operation"""
        # Mock a failing operation
        original_execute = redis_client._execute_with_retry
        
        call_count = 0
        
        async def failing_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count < 3:
                raise ConnectionError("Simulated connection error")
            
            return "success"
        
        redis_client._execute_with_retry = failing_execute
        
        try:
            # Should retry and eventually succeed
            result = await redis_client.set_json("test:retry", {"test": "data"})
            assert result is True
            assert call_count == 3
        finally:
            redis_client._execute_with_retry = original_execute
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_metrics_collection(self, redis_client):
        """Test metrics collection"""
        # Perform some operations
        await redis_client.set_json("test:metrics1", {"data": "test"})
        await redis_client.get_json("test:metrics1")
        await redis_client.set_json("test:metrics2", {"more": "data"})
        
        metrics = redis_client.get_metrics()
        
        assert "operation_count" in metrics
        assert "error_count" in metrics
        assert "circuit_breaker" in metrics
        assert metrics["operation_count"] >= 3


class TestGlobalRedisFunctions:
    """Test global Redis functions"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_redis_client(self):
        """Test global Redis client singleton"""
        client1 = await get_redis_client()
        client2 = await get_redis_client()
        
        assert client1 is client2  # Should be same instance
        
        await shutdown_redis()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_shutdown_redis(self):
        """Test Redis shutdown"""
        client = await get_redis_client()
        
        # Verify client exists
        assert client is not None
        
        # Shutdown
        await shutdown_redis()
        
        # Verify client is cleared
        with pytest.raises(RuntimeError):
            await get_redis_client()
