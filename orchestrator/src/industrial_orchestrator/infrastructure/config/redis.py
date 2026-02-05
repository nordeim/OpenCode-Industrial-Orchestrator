"""
INDUSTRIAL REDIS CONFIGURATION
Redis client with connection pooling, circuit breaker, and resilience patterns.
"""

import asyncio
import json
from typing import Optional, Any, Dict, List, Union
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from enum import Enum

import redis.asyncio as redis
from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import (
    RedisError,
    ConnectionError,
    TimeoutError,
    BusyLoadingError,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..exceptions.redis_exceptions import (
    RedisConnectionError,
    RedisTimeoutError,
    RedisCircuitOpenError,
)


class RedisCommand(str, Enum):
    """Redis commands for monitoring and circuit breaking"""
    GET = "GET"
    SET = "SET"
    HSET = "HSET"
    HGET = "HGET"
    DEL = "DEL"
    EXISTS = "EXISTS"
    EXPIRE = "EXPIRE"
    INCR = "INCR"
    DECR = "DECR"
    LPUSH = "LPUSH"
    RPUSH = "RPUSH"
    LPOP = "LPOP"
    RPOP = "RPOP"
    SADD = "SADD"
    SMEMBERS = "SMEMBERS"
    ZADD = "ZADD"
    ZRANGE = "ZRANGE"


class RedisSettings(BaseSettings):
    """Industrial Redis configuration settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="REDIS_",
        case_sensitive=False
    )
    
    # Connection settings
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    database: int = 0
    ssl: bool = False
    
    # Connection pooling
    max_connections: int = 50
    socket_connect_timeout: float = 5.0
    socket_timeout: float = 10.0
    socket_keepalive: bool = True
    retry_on_timeout: bool = True
    
    # Resilience
    max_retries: int = 3
    retry_delay: float = 0.1
    circuit_breaker_threshold: int = 10  # Failures before opening circuit
    circuit_breaker_timeout: float = 30.0  # Seconds circuit stays open
    
    # Serialization
    default_encoding: str = "utf-8"
    compress_threshold_bytes: int = 1024  # Compress values larger than this
    
    @property
    def connection_url(self) -> str:
        """Generate Redis connection URL"""
        auth = f":{self.password}@" if self.password else ""
        scheme = "rediss" if self.ssl else "redis"
        return f"{scheme}://{auth}{self.host}:{self.port}/{self.database}"


class CircuitBreaker:
    """Industrial circuit breaker pattern for Redis operations"""
    
    def __init__(
        self,
        failure_threshold: int = 10,
        recovery_timeout: float = 30.0,
        half_open_max_attempts: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_attempts = half_open_max_attempts
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.half_open_attempts = 0
        
    def record_success(self) -> None:
        """Record successful operation"""
        if self.state == "HALF_OPEN":
            self.half_open_attempts += 1
            if self.half_open_attempts >= self.half_open_max_attempts:
                self._reset()
        elif self.state == "CLOSED":
            self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self) -> None:
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)
        
        if self.state == "CLOSED" and self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            print(f"Circuit breaker OPENED after {self.failure_count} failures")
        
        elif self.state == "HALF_OPEN":
            self.state = "OPEN"
            self.half_open_attempts = 0
    
    def allow_request(self) -> bool:
        """Check if request is allowed based on circuit state"""
        now = datetime.now(timezone.utc)
        
        if self.state == "OPEN":
            if self.last_failure_time:
                elapsed = (now - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    self.half_open_attempts = 0
                    print("Circuit breaker transitioned to HALF_OPEN")
                    return True
            return False
        
        elif self.state == "HALF_OPEN":
            if self.half_open_attempts >= self.half_open_max_attempts:
                self._reset()
            return True
        
        return True  # CLOSED state
    
    def _reset(self) -> None:
        """Reset circuit breaker to CLOSED state"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
        self.half_open_attempts = 0
        print("Circuit breaker RESET to CLOSED")
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "half_open_attempts": self.half_open_attempts,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


class IndustrialRedisClient:
    """
    Industrial-grade Redis client with:
    1. Connection pooling and management
    2. Circuit breaker pattern
    3. Automatic retry with backoff
    4. Serialization/deserialization
    5. Compression for large values
    6. Comprehensive monitoring
    """
    
    def __init__(self, settings: RedisSettings):
        self.settings = settings
        self._client: Optional[Redis] = None
        self._pool: Optional[ConnectionPool] = None
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=settings.circuit_breaker_threshold,
            recovery_timeout=settings.circuit_breaker_timeout,
        )
        self._operation_count = 0
        self._error_count = 0
        self._total_latency_ms = 0
        
    async def initialize(self) -> None:
        """Initialize Redis connection pool"""
        if self._client is not None:
            return
        
        pool = ConnectionPool.from_url(
            self.settings.connection_url,
            max_connections=self.settings.max_connections,
            socket_connect_timeout=self.settings.socket_connect_timeout,
            socket_timeout=self.settings.socket_timeout,
            socket_keepalive=self.settings.socket_keepalive,
            retry_on_timeout=self.settings.retry_on_timeout,
            encoding=self.settings.default_encoding,
            decode_responses=True,
        )
        
        self._pool = pool
        self._client = Redis(connection_pool=pool)
        
        # Test connection
        await self._test_connection()
        print("Redis connection established")
    
    async def _test_connection(self) -> None:
        """Test Redis connection with retry logic"""
        for attempt in range(self.settings.max_retries):
            try:
                await self._client.ping()
                self._circuit_breaker.record_success()
                return
                
            except (ConnectionError, TimeoutError, BusyLoadingError) as e:
                self._circuit_breaker.record_failure()
                
                if attempt == self.settings.max_retries - 1:
                    raise RedisConnectionError(
                        f"Failed to connect to Redis after {self.settings.max_retries} attempts: {e}"
                    )
                
                delay = self.settings.retry_delay * (2 ** attempt)
                print(f"Redis connection failed (attempt {attempt + 1}), retrying in {delay:.1f}s: {e}")
                await asyncio.sleep(delay)
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize value to JSON string with optional compression"""
        if isinstance(value, (str, int, float, bool, type(None))):
            return json.dumps(value)
        
        # For complex objects, use JSON serialization
        serialized = json.dumps(value, default=str)
        
        # Compression for large values (simplified - in production use zlib)
        if len(serialized) > self.settings.compress_threshold_bytes:
            # In production: import zlib and compress
            # For now, just mark as compressible
            return f"COMPRESS:{serialized}"
        
        return serialized
    
    def _deserialize_value(self, value: str) -> Any:
        """Deserialize value from JSON string with decompression"""
        if not value:
            return None
        
        if value.startswith("COMPRESS:"):
            # In production: decompress with zlib
            value = value[9:]  # Remove COMPRESS: prefix
        
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            # Return as string if not valid JSON
            return value
    
    async def _execute_with_retry(
        self,
        command: RedisCommand,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute Redis command with retry logic and circuit breaking
        
        Design Principle: All operations go through this method for
        consistent error handling and monitoring.
        """
        start_time = datetime.now(timezone.utc)
        
        # Check circuit breaker
        if not self._circuit_breaker.allow_request():
            raise RedisCircuitOpenError(
                f"Circuit breaker is OPEN for command: {command}"
            )
        
        for attempt in range(self.settings.max_retries):
            try:
                if command == RedisCommand.GET:
                    result = await self._client.get(*args, **kwargs)
                elif command == RedisCommand.SET:
                    result = await self._client.set(*args, **kwargs)
                elif command == RedisCommand.HSET:
                    result = await self._client.hset(*args, **kwargs)
                elif command == RedisCommand.HGET:
                    result = await self._client.hget(*args, **kwargs)
                elif command == RedisCommand.DEL:
                    result = await self._client.delete(*args, **kwargs)
                elif command == RedisCommand.EXISTS:
                    result = await self._client.exists(*args, **kwargs)
                elif command == RedisCommand.EXPIRE:
                    result = await self._client.expire(*args, **kwargs)
                elif command == RedisCommand.INCR:
                    result = await self._client.incr(*args, **kwargs)
                elif command == RedisCommand.DECR:
                    result = await self._client.decr(*args, **kwargs)
                elif command == RedisCommand.LPUSH:
                    result = await self._client.lpush(*args, **kwargs)
                elif command == RedisCommand.RPUSH:
                    result = await self._client.rpush(*args, **kwargs)
                elif command == RedisCommand.LPOP:
                    result = await self._client.lpop(*args, **kwargs)
                elif command == RedisCommand.RPOP:
                    result = await self._client.rpop(*args, **kwargs)
                elif command == RedisCommand.SADD:
                    result = await self._client.sadd(*args, **kwargs)
                elif command == RedisCommand.SMEMBERS:
                    result = await self._client.smembers(*args, **kwargs)
                elif command == RedisCommand.ZADD:
                    result = await self._client.zadd(*args, **kwargs)
                elif command == RedisCommand.ZRANGE:
                    result = await self._client.zrange(*args, **kwargs)
                else:
                    raise ValueError(f"Unsupported Redis command: {command}")
                
                # Record success
                self._operation_count += 1
                self._circuit_breaker.record_success()
                
                # Calculate latency
                latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                self._total_latency_ms += latency_ms
                
                return result
                
            except (ConnectionError, TimeoutError, BusyLoadingError) as e:
                self._error_count += 1
                self._circuit_breaker.record_failure()
                
                if attempt == self.settings.max_retries - 1:
                    error_class = RedisTimeoutError if isinstance(e, TimeoutError) else RedisConnectionError
                    raise error_class(
                        f"Redis operation failed after {self.settings.max_retries} attempts "
                        f"(command: {command}, args: {args}): {e}"
                    )
                
                delay = self.settings.retry_delay * (2 ** attempt)
                await asyncio.sleep(delay)
                
            except RedisError as e:
                # Non-retryable errors
                self._error_count += 1
                raise RedisError(f"Redis error (command: {command}): {e}")
    
    # High-level operations with serialization
    
    async def set_json(
        self,
        key: str,
        value: Any,
        expire_seconds: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """Set JSON-serialized value with expiration"""
        serialized = self._serialize_value(value)
        
        result = await self._execute_with_retry(
            RedisCommand.SET,
            key,
            serialized,
            ex=expire_seconds,
            nx=nx,
            xx=xx
        )
        return bool(result)
    
    async def get_json(self, key: str) -> Any:
        """Get and deserialize JSON value"""
        result = await self._execute_with_retry(RedisCommand.GET, key)
        if result is None:
            return None
        return self._deserialize_value(result)
    
    async def hset_json(
        self,
        key: str,
        field: str,
        value: Any
    ) -> bool:
        """Set JSON-serialized value in hash"""
        serialized = self._serialize_value(value)
        result = await self._execute_with_retry(RedisCommand.HSET, key, field, serialized)
        return bool(result)
    
    async def hget_json(self, key: str, field: str) -> Any:
        """Get and deserialize JSON value from hash"""
        result = await self._execute_with_retry(RedisCommand.HGET, key, field)
        if result is None:
            return None
        return self._deserialize_value(result)
    
    async def acquire_lock(
        self,
        lock_key: str,
        lock_value: str,
        timeout_seconds: int = 30,
        retry_count: int = 3,
        retry_delay: float = 0.1
    ) -> bool:
        """
        Industrial distributed lock implementation
        
        Uses SET with NX and EX for atomic lock acquisition
        """
        for attempt in range(retry_count):
            result = await self._execute_with_retry(
                RedisCommand.SET,
                lock_key,
                lock_value,
                ex=timeout_seconds,
                nx=True
            )
            
            if result:
                return True
            
            if attempt < retry_count - 1:
                await asyncio.sleep(retry_delay)
        
        return False
    
    async def release_lock(self, lock_key: str, lock_value: str) -> bool:
        """Release distributed lock with value verification"""
        # Use Lua script for atomic check-and-delete
        lua_script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """
        
        try:
            result = await self._client.eval(lua_script, 1, lock_key, lock_value)
            return bool(result)
        except RedisError as e:
            print(f"Error releasing lock {lock_key}: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive Redis health check"""
        try:
            start_time = datetime.now(timezone.utc)
            
            # Test basic operations
            test_key = f"health_check:{datetime.now(timezone.utc).timestamp()}"
            test_value = {"status": "testing", "timestamp": start_time.isoformat()}
            
            await self.set_json(test_key, test_value, expire_seconds=10)
            retrieved = await self.get_json(test_key)
            
            latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            # Get Redis info
            info = await self._client.info()
            
            return {
                "status": "healthy",
                "latency_ms": latency_ms,
                "test_passed": retrieved == test_value,
                "info": {
                    "redis_version": info.get("redis_version"),
                    "used_memory_human": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients"),
                    "total_commands_processed": info.get("total_commands_processed"),
                },
                "circuit_breaker": self._circuit_breaker.get_status(),
                "operations": {
                    "total": self._operation_count,
                    "errors": self._error_count,
                    "error_rate": self._error_count / max(self._operation_count, 1),
                    "avg_latency_ms": self._total_latency_ms / max(self._operation_count, 1),
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "circuit_breaker": self._circuit_breaker.get_status(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
    
    async def close(self) -> None:
        """Close Redis connections"""
        if self._client:
            await self._client.close()
            self._client = None
        
        if self._pool:
            await self._pool.disconnect()
            self._pool = None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get Redis metrics for monitoring"""
        return {
            "operation_count": self._operation_count,
            "error_count": self._error_count,
            "circuit_breaker": self._circuit_breaker.get_status(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Global Redis client instance
_redis_client: Optional[IndustrialRedisClient] = None


async def get_redis_client() -> IndustrialRedisClient:
    """Get or create global Redis client"""
    global _redis_client
    
    if _redis_client is None:
        settings = RedisSettings()
        _redis_client = IndustrialRedisClient(settings)
        await _redis_client.initialize()
    
    return _redis_client


async def shutdown_redis() -> None:
    """Shutdown Redis connections"""
    global _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
