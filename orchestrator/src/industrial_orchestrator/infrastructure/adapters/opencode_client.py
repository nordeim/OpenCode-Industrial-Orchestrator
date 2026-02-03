"""
INDUSTRIAL OPENCODE API CLIENT
Robust HTTP client for OpenCode API with retry logic, circuit breaking, and monitoring.
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Union
from uuid import UUID
from enum import Enum

import httpx
from httpx import (
    AsyncClient,
    Timeout,
    Limits,
    HTTPStatusError,
    ConnectError,
    ReadTimeout,
)
from pydantic import BaseModel, Field, validator
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from ...domain.entities.session import SessionEntity, SessionType, SessionPriority
from ...domain.value_objects.session_status import SessionStatus
from ...infrastructure.config.redis import IndustrialRedisClient, get_redis_client
from ...infrastructure.exceptions.opencode_exceptions import (
    OpenCodeAPIError,
    OpenCodeConnectionError,
    OpenCodeTimeoutError,
    OpenCodeRateLimitError,
    OpenCodeSessionNotFoundError,
)


class OpenCodeCommand(str, Enum):
    """OpenCode API commands"""
    CREATE_SESSION = "create_session"
    GET_SESSION = "get_session"
    SEND_MESSAGE = "send_message"
    SEND_MESSAGE_ASYNC = "send_message_async"
    EXECUTE_COMMAND = "execute_command"
    RUN_SHELL = "run_shell"
    GET_SESSION_STATUS = "get_session_status"
    GET_SESSION_DIFF = "get_session_diff"
    FORK_SESSION = "fork_session"
    ABORT_SESSION = "abort_session"
    DELETE_SESSION = "delete_session"


class OpenCodeAPISettings(BaseModel):
    """OpenCode API configuration"""
    
    base_url: str = "http://localhost:4096"
    api_key: Optional[str] = None
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Rate limiting
    requests_per_minute: int = 60
    burst_limit: int = 10
    
    # Circuit breaker
    circuit_breaker_threshold: int = 10
    circuit_breaker_timeout: float = 60.0
    
    # Caching
    cache_ttl_seconds: int = 300  # 5 minutes
    session_cache_ttl: int = 600  # 10 minutes for session data
    
    class Config:
        env_prefix = "OPENCODE_"
        case_sensitive = False
    
    @validator('base_url')
    def validate_base_url(cls, v: str) -> str:
        """Ensure base URL ends without trailing slash"""
        return v.rstrip('/')


class OpenCodeRequest(BaseModel):
    """Industrial OpenCode API request"""
    
    command: OpenCodeCommand
    path: str
    method: str = "GET"
    params: Dict[str, Any] = Field(default_factory=dict)
    data: Optional[Dict[str, Any]] = None
    headers: Dict[str, str] = Field(default_factory=dict)
    requires_auth: bool = True
    cache_key: Optional[str] = None
    cache_ttl: Optional[int] = None
    
    class Config:
        arbitrary_types_allowed = True


class OpenCodeResponse(BaseModel):
    """Industrial OpenCode API response"""
    
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    latency_ms: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: Optional[str] = None
    
    @property
    def is_cached(self) -> bool:
        """Check if response came from cache"""
        return self.request_id is not None and self.request_id.startswith("cache:")


class RateLimiter:
    """Industrial rate limiter using Redis token bucket algorithm"""
    
    def __init__(self, redis_client: IndustrialRedisClient, key_prefix: str = "rate_limit"):
        self.redis = redis_client
        self.key_prefix = key_prefix
    
    async def acquire(self, resource: str, limit: int, window_seconds: int = 60) -> bool:
        """
        Try to acquire permission for API call
        
        Uses sliding window counter algorithm
        """
        now = datetime.now(timezone.utc)
        window_key = f"{self.key_prefix}:{resource}:{window_seconds}"
        
        # Use Redis sorted set for sliding window
        member = f"{now.timestamp()}:{UUID().hex[:8]}"
        
        pipe = self.redis._client.pipeline()
        pipe.zadd(window_key, {member: now.timestamp()})
        pipe.zremrangebyscore(window_key, 0, now.timestamp() - window_seconds)
        pipe.zcard(window_key)
        results = await pipe.execute()
        
        current_count = results[2]
        
        # Set expiration on the key
        await self.redis._client.expire(window_key, window_seconds + 1)
        
        return current_count <= limit
    
    async def get_usage(self, resource: str, window_seconds: int = 60) -> Dict[str, Any]:
        """Get current rate limit usage"""
        window_key = f"{self.key_prefix}:{resource}:{window_seconds}"
        
        now = datetime.now(timezone.utc)
        count = await self.redis._client.zcount(
            window_key,
            now.timestamp() - window_seconds,
            now.timestamp()
        )
        
        return {
            "resource": resource,
            "window_seconds": window_seconds,
            "current_usage": count,
            "timestamp": now.isoformat(),
        }


class CircuitBreakerState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class OpenCodeCircuitBreaker:
    """Circuit breaker for OpenCode API calls"""
    
    def __init__(
        self,
        failure_threshold: int = 10,
        recovery_timeout: float = 60.0,
        half_open_max_successes: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_successes = half_open_max_successes
        
        self.failures = 0
        self.last_failure: Optional[datetime] = None
        self.state = CircuitBreakerState.CLOSED
        self.half_open_successes = 0
        
    def record_success(self) -> None:
        """Record successful API call"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.half_open_successes += 1
            if self.half_open_successes >= self.half_open_max_successes:
                self._reset()
        elif self.state == CircuitBreakerState.CLOSED:
            self.failures = max(0, self.failures - 1)
    
    def record_failure(self) -> None:
        """Record failed API call"""
        self.failures += 1
        self.last_failure = datetime.now(timezone.utc)
        
        if self.state == CircuitBreakerState.CLOSED and self.failures >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            print(f"OpenCode circuit breaker OPENED after {self.failures} failures")
        
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            self.half_open_successes = 0
    
    def allow_request(self) -> bool:
        """Check if request is allowed based on circuit state"""
        if self.state == CircuitBreakerState.OPEN:
            if self.last_failure:
                elapsed = (datetime.now(timezone.utc) - self.last_failure).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.half_open_successes = 0
                    print("OpenCode circuit breaker transitioned to HALF_OPEN")
                    return True
            return False
        
        return True  # CLOSED or HALF_OPEN
    
    def _reset(self) -> None:
        """Reset circuit breaker"""
        self.failures = 0
        self.last_failure = None
        self.state = CircuitBreakerState.CLOSED
        self.half_open_successes = 0
        print("OpenCode circuit breaker RESET to CLOSED")
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return {
            "state": self.state,
            "failures": self.failures,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            "half_open_successes": self.half_open_successes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


class IndustrialOpenCodeClient:
    """
    Industrial-grade OpenCode API client
    
    Features:
    1. Automatic retry with exponential backoff
    2. Circuit breaker pattern
    3. Rate limiting
    4. Response caching
    5. Comprehensive monitoring
    6. Session management
    """
    
    def __init__(self, settings: OpenCodeAPISettings):
        self.settings = settings
        self._client: Optional[AsyncClient] = None
        self._rate_limiter: Optional[RateLimiter] = None
        self._circuit_breaker = OpenCodeCircuitBreaker(
            failure_threshold=settings.circuit_breaker_threshold,
            recovery_timeout=settings.circuit_breaker_timeout,
        )
        
        self._request_count = 0
        self._error_count = 0
        self._total_latency_ms = 0
        
        # Cache for session data
        self._session_cache: Dict[str, Dict[str, Any]] = {}
    
    async def initialize(self) -> None:
        """Initialize HTTP client and dependencies"""
        if self._client is not None:
            return
        
        # Create HTTP client with industrial settings
        timeout = Timeout(
            connect=10.0,
            read=self.settings.timeout_seconds,
            write=10.0,
            pool=10.0,
        )
        
        limits = Limits(
            max_connections=100,
            max_keepalive_connections=20,
            keepalive_expiry=30.0,
        )
        
        headers = {
            "User-Agent": "IndustrialOpenCodeClient/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
        if self.settings.api_key:
            headers["Authorization"] = f"Bearer {self.settings.api_key}"
        
        self._client = AsyncClient(
            base_url=self.settings.base_url,
            timeout=timeout,
            limits=limits,
            headers=headers,
            follow_redirects=True,
        )
        
        # Initialize rate limiter
        redis_client = await get_redis_client()
        self._rate_limiter = RateLimiter(redis_client, "opencode_api")
        
        # Test connection
        await self._test_connection()
        print("OpenCode client initialized")
    
    async def _test_connection(self) -> None:
        """Test API connection with retry logic"""
        for attempt in range(self.settings.max_retries):
            try:
                response = await self._client.get("/")
                response.raise_for_status()
                self._circuit_breaker.record_success()
                return
                
            except (ConnectError, ReadTimeout) as e:
                self._circuit_breaker.record_failure()
                
                if attempt == self.settings.max_retries - 1:
                    raise OpenCodeConnectionError(
                        f"Failed to connect to OpenCode API after {self.settings.max_retries} attempts: {e}"
                    )
                
                delay = self.settings.retry_delay * (2 ** attempt)
                print(f"OpenCode connection failed (attempt {attempt + 1}), retrying in {delay:.1f}s: {e}")
                await asyncio.sleep(delay)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectError, ReadTimeout, HTTPStatusError)),
        before_sleep=before_sleep_log(logger=None, log_level=30),
        reraise=True,
    )
    async def _make_request(self, request: OpenCodeRequest) -> OpenCodeResponse:
        """
        Make HTTP request with industrial resilience
        
        This is the core method that all API calls go through.
        """
        start_time = datetime.now(timezone.utc)
        
        # Check circuit breaker
        if not self._circuit_breaker.allow_request():
            raise OpenCodeAPIError("Circuit breaker is OPEN")
        
        # Check rate limiting
        if not await self._rate_limiter.acquire(
            resource="api_calls",
            limit=self.settings.requests_per_minute,
            window_seconds=60
        ):
            raise OpenCodeRateLimitError("Rate limit exceeded")
        
        # Check cache for GET requests
        if request.method == "GET" and request.cache_key:
            cached = await self._get_from_cache(request.cache_key)
            if cached is not None:
                return OpenCodeResponse(
                    success=True,
                    data=cached,
                    latency_ms=0.1,  # Minimal latency for cache hit
                    request_id=f"cache:{request.cache_key}",
                )
        
        try:
            # Make HTTP request
            response = await self._client.request(
                method=request.method,
                url=request.path,
                params=request.params,
                json=request.data,
                headers=request.headers,
            )
            
            # Calculate latency
            latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            # Handle response
            if response.status_code >= 400:
                self._circuit_breaker.record_failure()
                self._error_count += 1
                
                error_data = None
                try:
                    error_data = response.json()
                except:
                    error_data = {"detail": response.text}
                
                if response.status_code == 404:
                    raise OpenCodeSessionNotFoundError(f"Session not found: {error_data}")
                elif response.status_code == 429:
                    raise OpenCodeRateLimitError(f"Rate limited: {error_data}")
                else:
                    raise HTTPStatusError(
                        f"API error {response.status_code}: {error_data}",
                        request=response.request,
                        response=response,
                    )
            
            # Success
            self._circuit_breaker.record_success()
            self._request_count += 1
            self._total_latency_ms += latency_ms
            
            data = response.json() if response.content else None
            
            # Cache response if applicable
            if request.method == "GET" and request.cache_key and data:
                await self._set_cache(
                    request.cache_key,
                    data,
                    ttl=request.cache_ttl or self.settings.cache_ttl_seconds
                )
            
            return OpenCodeResponse(
                success=True,
                data=data,
                status_code=response.status_code,
                latency_ms=latency_ms,
            )
            
        except (ConnectError, ReadTimeout) as e:
            self._circuit_breaker.record_failure()
            self._error_count += 1
            raise OpenCodeConnectionError(f"Connection error: {e}")
            
        except HTTPStatusError as e:
            # Already handled above
            raise
            
        except Exception as e:
            self._circuit_breaker.record_failure()
            self._error_count += 1
            raise OpenCodeAPIError(f"Unexpected error: {e}")
    
    async def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from Redis cache"""
        try:
            redis_client = await get_redis_client()
            return await redis_client.get_json(f"opencode_cache:{key}")
        except:
            return None
    
    async def _set_cache(self, key: str, data: Dict[str, Any], ttl: int) -> None:
        """Set data in Redis cache"""
        try:
            redis_client = await get_redis_client()
            await redis_client.set_json(
                f"opencode_cache:{key}",
                data,
                expire_seconds=ttl
            )
        except:
            pass  # Cache failure shouldn't break API
    
    # High-level API methods
    
    async def create_session(
        self,
        title: str,
        parent_id: Optional[str] = None,
        agent: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create new OpenCode session"""
        request = OpenCodeRequest(
            command=OpenCodeCommand.CREATE_SESSION,
            path="/session",
            method="POST",
            data={
                "title": title,
                "parentID": parent_id,
                "agent": agent,
                "model": model,
            },
        )
        
        response = await self._make_request(request)
        return response.data
    
    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session details"""
        cache_key = f"session:{session_id}"
        
        request = OpenCodeRequest(
            command=OpenCodeCommand.GET_SESSION,
            path=f"/session/{session_id}",
            method="GET",
            cache_key=cache_key,
            cache_ttl=self.settings.session_cache_ttl,
        )
        
        response = await self._make_request(request)
        return response.data
    
    async def send_message(
        self,
        session_id: str,
        message: str,
        agent: Optional[str] = None,
        model: Optional[str] = None,
        files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send message to session (synchronous)"""
        data = {
            "parts": [{"type": "text", "text": message}],
        }
        
        if agent:
            data["agent"] = agent
        if model:
            data["model"] = model
        
        request = OpenCodeRequest(
            command=OpenCodeCommand.SEND_MESSAGE,
            path=f"/session/{session_id}/message",
            method="POST",
            data=data,
        )
        
        response = await self._make_request(request)
        return response.data
    
    async def send_message_async(
        self,
        session_id: str,
        message: str,
        agent: Optional[str] = None
    ) -> bool:
        """Send message to session (asynchronous)"""
        data = {
            "parts": [{"type": "text", "text": message}],
        }
        
        if agent:
            data["agent"] = agent
        
        request = OpenCodeRequest(
            command=OpenCodeCommand.SEND_MESSAGE_ASYNC,
            path=f"/session/{session_id}/prompt_async",
            method="POST",
            data=data,
        )
        
        response = await self._make_request(request)
        return response.status_code == 204  # No content for async
    
    async def execute_command(
        self,
        session_id: str,
        command: str,
        arguments: List[str],
        agent: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute slash command in session"""
        data = {
            "command": command,
            "arguments": arguments,
        }
        
        if agent:
            data["agent"] = agent
        if model:
            data["model"] = model
        
        request = OpenCodeRequest(
            command=OpenCodeCommand.EXECUTE_COMMAND,
            path=f"/session/{session_id}/command",
            method="POST",
            data=data,
        )
        
        response = await self._make_request(request)
        return response.data
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get session status"""
        request = OpenCodeRequest(
            command=OpenCodeCommand.GET_SESSION_STATUS,
            path=f"/session/{session_id}",
            method="GET",
        )
        
        response = await self._make_request(request)
        return response.data
    
    async def get_session_diff(self, session_id: str) -> Dict[str, Any]:
        """Get file changes from session"""
        request = OpenCodeRequest(
            command=OpenCodeCommand.GET_SESSION_DIFF,
            path=f"/session/{session_id}/diff",
            method="GET",
        )
        
        response = await self._make_request(request)
        return response.data
    
    async def fork_session(
        self,
        session_id: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fork existing session"""
        data = {}
        if title:
            data["title"] = title
        
        request = OpenCodeRequest(
            command=OpenCodeCommand.FORK_SESSION,
            path=f"/session/{session_id}/fork",
            method="POST",
            data=data,
        )
        
        response = await self._make_request(request)
        return response.data
    
    async def abort_session(self, session_id: str) -> bool:
        """Abort running session"""
        request = OpenCodeRequest(
            command=OpenCodeCommand.ABORT_SESSION,
            path=f"/session/{session_id}/abort",
            method="POST",
        )
        
        response = await self._make_request(request)
        return response.success
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        request = OpenCodeRequest(
            command=OpenCodeCommand.DELETE_SESSION,
            path=f"/session/{session_id}",
            method="DELETE",
        )
        
        response = await self._make_request(request)
        return response.success
    
    # Session management helpers
    
    async def create_session_from_entity(self, session_entity: SessionEntity) -> Dict[str, Any]:
        """Create OpenCode session from domain entity"""
        # Extract agent and model from entity
        agent_config = session_entity.agent_config
        agent = next(iter(agent_config.keys())) if agent_config else None
        model = session_entity.model_config
        
        return await self.create_session(
            title=session_entity.title,
            parent_id=str(session_entity.parent_id) if session_entity.parent_id else None,
            agent=agent,
            model=model,
        )
    
    async def execute_session_task(self, session_entity: SessionEntity) -> Dict[str, Any]:
        """Execute session task with entity configuration"""
        session_data = await self.create_session_from_entity(session_entity)
        session_id = session_data["id"]
        
        # Send initial prompt
        result = await self.send_message(
            session_id=session_id,
            message=session_entity.initial_prompt,
            agent=next(iter(session_entity.agent_config.keys())) if session_entity.agent_config else None,
            model=session_entity.model_config,
        )
        
        # Monitor session completion
        await self._monitor_session_completion(session_id)
        
        # Get final diff
        diff = await self.get_session_diff(session_id)
        
        return {
            "session_id": session_id,
            "result": result,
            "diff": diff,
            "metrics": {
                "api_calls": 3,  # create + send + diff
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
    
    async def _monitor_session_completion(self, session_id: str, timeout_seconds: int = 3600) -> None:
        """Monitor session until completion or timeout"""
        start_time = datetime.now(timezone.utc)
        poll_interval = 2.0
        
        while (datetime.now(timezone.utc) - start_time).total_seconds() < timeout_seconds:
            status = await self.get_session_status(session_id)
            
            if status.get("status") in ["idle", "completed", "failed"]:
                return
            
            await asyncio.sleep(poll_interval)
            poll_interval = min(poll_interval * 1.5, 30.0)  # Exponential backoff
        
        raise OpenCodeTimeoutError(f"Session {session_id} timeout after {timeout_seconds} seconds")
    
    # Health and metrics
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        try:
            start_time = datetime.now(timezone.utc)
            
            # Test basic API call
            await self._client.get("/")
            
            latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "latency_ms": latency_ms,
                "circuit_breaker": self._circuit_breaker.get_status(),
                "rate_limiting": await self._rate_limiter.get_usage("api_calls"),
                "operations": {
                    "total_requests": self._request_count,
                    "total_errors": self._error_count,
                    "error_rate": self._error_count / max(self._request_count, 1),
                    "avg_latency_ms": self._total_latency_ms / max(self._request_count, 1),
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
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics for monitoring"""
        return {
            "request_count": self._request_count,
            "error_count": self._error_count,
            "circuit_breaker": self._circuit_breaker.get_status(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Global OpenCode client instance
_opencode_client: Optional[IndustrialOpenCodeClient] = None


async def get_opencode_client() -> IndustrialOpenCodeClient:
    """Get or create global OpenCode client"""
    global _opencode_client
    
    if _opencode_client is None:
        settings = OpenCodeAPISettings()
        _opencode_client = IndustrialOpenCodeClient(settings)
        await _opencode_client.initialize()
    
    return _opencode_client


async def shutdown_opencode() -> None:
    """Shutdown OpenCode client"""
    global _opencode_client
    
    if _opencode_client:
        await _opencode_client.close()
        _opencode_client = None
