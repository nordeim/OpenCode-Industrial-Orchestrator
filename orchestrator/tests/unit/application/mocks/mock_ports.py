"""
MOCK SERVICE PORT IMPLEMENTATIONS
Mock implementations of service ports for unit testing.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone
from dataclasses import dataclass, field

from src.industrial_orchestrator.application.ports.service_ports import (
    OpenCodeClientPort,
    DistributedLockPort,
    ExecutionResult,
    HealthCheckResult,
    ServiceHealth,
)


class MockDistributedLock(DistributedLockPort):
    """
    Mock distributed lock for testing.
    
    By default, all lock operations succeed immediately.
    Can be configured to simulate contention or failures.
    """

    def __init__(self):
        self._locks: Dict[str, Dict[str, Any]] = {}
        self._fail_on_acquire: bool = False
        self._acquisition_count: int = 0

    def reset(self):
        """Clear all locks and reset configuration."""
        self._locks.clear()
        self._fail_on_acquire = False
        self._acquisition_count = 0

    def set_fail_on_acquire(self, fail: bool):
        """Configure lock to fail on acquire attempts."""
        self._fail_on_acquire = fail

    @property
    def acquisition_count(self) -> int:
        """Number of successful acquisitions."""
        return self._acquisition_count

    def acquire(
        self,
        resource: str,
        timeout: float = 30.0,
        blocking: bool = True
    ) -> bool:
        """Acquire lock (always succeeds unless configured to fail)."""
        if self._fail_on_acquire:
            return False
        
        self._locks[resource] = {
            "owner": "test",
            "acquired_at": datetime.now(timezone.utc),
            "timeout": timeout,
        }
        self._acquisition_count += 1
        return True

    def release(self, resource: str) -> bool:
        """Release lock."""
        if resource in self._locks:
            del self._locks[resource]
            return True
        return False

    def renew(self, resource: str, additional_time: float = 30.0) -> bool:
        """Renew lock."""
        if resource in self._locks:
            self._locks[resource]["timeout"] += additional_time
            return True
        return False

    def is_locked(self, resource: str) -> bool:
        """Check if resource is locked."""
        return resource in self._locks

    def get_lock_info(self, resource: str) -> Optional[Dict[str, Any]]:
        """Get lock metadata."""
        return self._locks.get(resource)

    def force_release(self, resource: str) -> bool:
        """Force release lock."""
        return self.release(resource)


@dataclass
class MockOpenCodeConfig:
    """Configuration for MockOpenCodeClient behavior."""
    
    # Default success response
    default_success: bool = True
    default_output: str = "Task completed successfully"
    default_tokens: int = 1000
    default_execution_time: float = 5.0
    
    # Failure configuration
    fail_on_prompt_contains: Optional[str] = None
    error_message: str = "Execution failed"
    
    # Health status
    health_status: ServiceHealth = ServiceHealth.HEALTHY


class MockOpenCodeClient(OpenCodeClientPort):
    """
    Mock OpenCode client for testing.
    
    Configurable to return success/failure based on prompt content.
    """

    def __init__(self, config: Optional[MockOpenCodeConfig] = None):
        self.config = config or MockOpenCodeConfig()
        self._execution_count: int = 0
        self._last_prompt: Optional[str] = None
        self._cancelled_executions: set = set()

    def reset(self):
        """Reset client state."""
        self._execution_count = 0
        self._last_prompt = None
        self._cancelled_executions.clear()

    @property
    def execution_count(self) -> int:
        """Number of executions performed."""
        return self._execution_count

    @property
    def last_prompt(self) -> Optional[str]:
        """Last prompt executed."""
        return self._last_prompt

    async def execute_prompt(
        self,
        prompt: str,
        config: Optional[Dict[str, Any]] = None,
        timeout_seconds: float = 300.0
    ) -> ExecutionResult:
        """Execute prompt and return configurable result."""
        self._execution_count += 1
        self._last_prompt = prompt
        
        # Check if should fail based on prompt content
        if (self.config.fail_on_prompt_contains and 
            self.config.fail_on_prompt_contains in prompt):
            return ExecutionResult(
                success=False,
                output="",
                error=self.config.error_message,
                tokens_used=0,
                execution_time_seconds=0.0,
            )
        
        # Return success
        return ExecutionResult(
            success=self.config.default_success,
            output=self.config.default_output,
            error=None if self.config.default_success else self.config.error_message,
            tokens_used=self.config.default_tokens,
            execution_time_seconds=self.config.default_execution_time,
            metadata={"prompt_length": len(prompt)},
        )

    async def get_status(self) -> HealthCheckResult:
        """Return configured health status."""
        return HealthCheckResult(
            status=self.config.health_status,
            latency_ms=10.0,
            details={"mock": True},
        )

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel execution."""
        self._cancelled_executions.add(execution_id)
        return True

    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get execution status."""
        if execution_id in self._cancelled_executions:
            return {"status": "cancelled", "execution_id": execution_id}
        return {"status": "completed", "execution_id": execution_id}
