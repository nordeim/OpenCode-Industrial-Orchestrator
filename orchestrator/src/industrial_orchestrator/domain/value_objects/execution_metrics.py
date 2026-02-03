"""
INDUSTRIAL EXECUTION METRICS
Precise telemetry for performance analysis and optimization.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field, validator


class ExecutionMetrics(BaseModel):
    """
    Industrial-grade execution metrics collection
    
    Design Principles:
    1. Immutable timestamps for audit trail
    2. Resource utilization tracking
    3. Performance benchmarking
    4. Failure analysis data
    """
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    
    # Duration metrics
    queue_duration_seconds: Optional[float] = None
    execution_duration_seconds: Optional[float] = None
    total_duration_seconds: Optional[float] = None
    
    # Resource utilization
    cpu_usage_percent: Optional[float] = Field(None, ge=0, le=1000)  # Can exceed 100% for multi-core
    memory_usage_mb: Optional[float] = Field(None, ge=0)
    disk_usage_mb: Optional[float] = Field(None, ge=0)
    network_bytes_sent: Optional[int] = Field(None, ge=0)
    network_bytes_received: Optional[int] = Field(None, ge=0)
    
    # Performance counters
    total_tokens_used: Optional[int] = Field(None, ge=0)
    api_calls_count: int = Field(default=0, ge=0)
    api_errors_count: int = Field(default=0, ge=0)
    retry_count: int = Field(default=0, ge=0)
    
    # Quality metrics
    success_rate: Optional[float] = Field(None, ge=0, le=1)
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    code_quality_score: Optional[float] = Field(None, ge=0, le=1)
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Checkpointing
    checkpoint_count: int = Field(default=0, ge=0)
    last_checkpoint_at: Optional[datetime] = None
    
    # Cost tracking (for cloud resources)
    estimated_cost_usd: Optional[float] = Field(None, ge=0)
    
    model_config = {"arbitrary_types_allowed": True}
    
    @validator('success_rate', 'confidence_score', 'code_quality_score')
    def validate_percentage_range(cls, v: Optional[float]) -> Optional[float]:
        """Ensure percentage values are between 0 and 1"""
        if v is not None and not 0 <= v <= 1:
            raise ValueError(f"Value must be between 0 and 1, got {v}")
        return v
    
    def start_timing(self) -> None:
        """Record execution start time"""
        if not self.started_at:
            self.started_at = datetime.utcnow()
            
            # Calculate queue duration
            if self.created_at:
                self.queue_duration_seconds = (
                    self.started_at - self.created_at
                ).total_seconds()
    
    def complete_timing(self) -> None:
        """Record execution completion time"""
        if self.started_at and not self.completed_at:
            self.completed_at = datetime.utcnow()
            self.execution_duration_seconds = (
                self.completed_at - self.started_at
            ).total_seconds()
            
            # Calculate total duration
            if self.created_at:
                self.total_duration_seconds = (
                    self.completed_at - self.created_at
                ).total_seconds()
    
    def fail_timing(self) -> None:
        """Record failure time"""
        if self.started_at and not self.failed_at:
            self.failed_at = datetime.utcnow()
            self.execution_duration_seconds = (
                self.failed_at - self.started_at
            ).total_seconds()
    
    def increment_api_calls(self, count: int = 1) -> None:
        """Increment API call counter"""
        self.api_calls_count += count
    
    def increment_api_errors(self, count: int = 1) -> None:
        """Increment API error counter"""
        self.api_errors_count += count
    
    def increment_retry_count(self) -> None:
        """Increment retry counter"""
        self.retry_count += 1
    
    def record_checkpoint(self) -> None:
        """Record checkpoint event"""
        self.checkpoint_count += 1
        self.last_checkpoint_at = datetime.utcnow()
    
    def calculate_success_rate(self, successful_tasks: int, total_tasks: int) -> None:
        """Calculate and set success rate"""
        if total_tasks > 0:
            self.success_rate = successful_tasks / total_tasks
    
    def add_warning(self, warning_type: str, message: str, context: Dict[str, Any] = None) -> None:
        """Add warning to metrics"""
        warning = {
            'type': warning_type,
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'context': context or {}
        }
        self.warnings.append(warning)
    
    def get_api_error_rate(self) -> float:
        """Calculate API error rate"""
        if self.api_calls_count == 0:
            return 0.0
        return self.api_errors_count / self.api_calls_count
    
    def is_healthy(self) -> bool:
        """Determine if metrics indicate healthy execution"""
        if self.api_errors_count > 0 and self.get_api_error_rate() > 0.1:
            return False  # More than 10% API errors
        
        if self.retry_count > 5:
            return False  # Excessive retries
        
        if self.warnings and len(self.warnings) > 10:
            return False  # Too many warnings
        
        return True
    
    def to_telemetry_dict(self) -> Dict[str, Any]:
        """Convert metrics to telemetry-friendly dictionary"""
        return {
            'durations': {
                'queue_seconds': self.queue_duration_seconds,
                'execution_seconds': self.execution_duration_seconds,
                'total_seconds': self.total_duration_seconds,
            },
            'resources': {
                'cpu_percent': self.cpu_usage_percent,
                'memory_mb': self.memory_usage_mb,
                'disk_mb': self.disk_usage_mb,
                'network_sent_bytes': self.network_bytes_sent,
                'network_received_bytes': self.network_bytes_received,
            },
            'performance': {
                'api_calls': self.api_calls_count,
                'api_errors': self.api_errors_count,
                'error_rate': self.get_api_error_rate(),
                'retries': self.retry_count,
                'tokens_used': self.total_tokens_used,
            },
            'quality': {
                'success_rate': self.success_rate,
                'confidence': self.confidence_score,
                'code_quality': self.code_quality_score,
            },
            'cost': {
                'estimated_usd': self.estimated_cost_usd,
            }
        }
