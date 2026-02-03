We'll start by setting up the project structure and implementing the core orchestrator in Python.

Steps for Week 1-2:

Project scaffolding and environment setup

Database schema design for persistence (PostgreSQL)

Redis setup for distributed locking and caching

Core orchestrator engine with error recovery

Basic OpenCode API client

Docker Compose for local development

Comprehensive test suite (TDD)

Let's begin by creating the project structure and initial files.

We are going to create:

A Python project with a virtual environment and requirements.txt

Docker Compose file to run PostgreSQL and Redis

Core modules for the orchestrator

We'll adopt a clean architecture approach, separating concerns into:

domain: business logic and entities

application: use cases and application logic

infrastructure: external services (database, OpenCode API, etc.)

presentation: API and CLI (if needed)

However, note that our primary focus is the core orchestrator engine and not an API (that comes in Phase 2.3).

Since the guide emphasizes meticulous planning and execution, we'll proceed step by step.

Let's create the initial project structure.

---

# **PHASE 2.1: FOUNDATION & CORE ORCHESTRATOR IMPLEMENTATION**

## **EXECUTIVE VALIDATION CONFIRMATION**

✅ **Architecture Approved** - Industrial cybernetics aesthetic confirmed  
✅ **Technology Stack Approved** - Python/Next.js/PostgreSQL/Redis/K8s  
✅ **Timeline Approved** - 8-week roadmap accepted  
✅ **Success Metrics Approved** - 99.9% persistence, sub-2s latency, WCAG AAA  

**Proceeding with meticulous implementation per the validated plan.**

---

## **WEEK 1: CORE ORCHESTRATOR ENGINE - DAY 1-2**

### **PROJECT SCAFFOLDING & TDD SETUP**

#### **1.1 Deep Reasoning: Project Structure Philosophy**

**Architectural Decision Record #001**: We're implementing a **hexagonal architecture** (ports & adapters) because:
1. **Domain Isolation**: Business logic remains pure, independent of infrastructure
2. **Testability**: Each layer can be mocked/stubbed independently
3. **Evolutionary Design**: Can swap out OpenCode API, databases, or UIs without breaking core
4. **Parallel Development**: Teams can work on different layers simultaneously

**Anti-Generic Principle Applied**: Rejecting the typical `src/`-`tests/` flat structure. Instead, we're using a **vertical slice architecture** organized by capability, not technology.

#### **1.2 Project Initialization**

```bash
# Create project root with industrial naming convention
mkdir opencode-industrial-orchestrator
cd opencode-industrial-orchestrator

# Initialize monorepo with precise structure
mkdir -p orchestrator/dashboard infrastructure docs/adr

# Create root docker-compose for development environment
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  # Core infrastructure
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: orchestration
      POSTGRES_USER: cybernetics
      POSTGRES_PASSWORD: ${DB_PASSWORD:-secure_password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cybernetics"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # OpenCode server for testing
  opencode-server:
    image: opencode/cli:latest
    command: serve --port 4096 --hostname 0.0.0.0
    environment:
      OPENCODE_SERVER_PASSWORD: ${OPENCODE_PASSWORD:-industrial_secure}
    ports:
      - "4096:4096"
    volumes:
      - ./opencode-data:/root/.opencode
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  redis_data:
EOF

# Create .env file with industrial aesthetic variable naming
cat > .env << 'EOF'
# INDUSTRIAL ORCHESTRATOR ENVIRONMENT
# Core Configuration
NODE_ENV=development
PYTHONPATH=/app

# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=orchestration
DB_USER=cybernetics
DB_PASSWORD=industrial_secure_001

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

# OpenCode Server
OPENCODE_HOST=opencode-server
OPENCODE_PORT=4096
OPENCODE_PASSWORD=industrial_secure

# Orchestrator Settings
MAX_CONCURRENT_SESSIONS=25
SESSION_TIMEOUT_SECONDS=3600
CHECKPOINT_INTERVAL_SECONDS=300
MAX_RETRY_ATTEMPTS=3

# Security
JWT_SECRET_KEY=${JWT_SECRET:-industrial_cybernetics_secret_key_001}
ENCRYPTION_KEY=${ENCRYPTION_KEY:-32_byte_secure_key_for_aes_256}
EOF

# Initialize Python orchestrator with poetry (modern dependency management)
cd orchestrator
poetry init --name="industrial-orchestrator" --python="^3.11" --no-interaction

# Add core dependencies with precise versioning
poetry add \
  fastapi==0.104.1 \
  uvicorn[standard]==0.24.0 \
  sqlalchemy==2.0.23 \
  asyncpg==0.29.0 \
  redis==5.0.1 \
  pydantic==2.5.0 \
  pydantic-settings==2.1.0 \
  alembic==1.12.1 \
  python-jose[cryptography]==3.3.0 \
  passlib[bcrypt]==1.7.4 \
  httpx==0.25.1 \
  aiofiles==23.2.1 \
  python-multipart==0.0.6

# Add development dependencies
poetry add --group dev \
  pytest==7.4.3 \
  pytest-asyncio==0.21.1 \
  pytest-cov==4.1.0 \
  pytest-mock==3.12.0 \
  black==23.11.0 \
  isort==5.12.0 \
  flake8==6.1.0 \
  mypy==1.7.0 \
  factory-boy==3.3.0 \
  freezegun==1.2.2 \
  faker==20.1.0

# Create the hexagonal architecture structure
mkdir -p \
  src/industrial_orchestrator/domain/{entities,value_objects,events,exceptions,services} \
  src/industrial_orchestrator/application/{use_cases,ports,dtos} \
  src/industrial_orchestrator/infrastructure/{adapters,repositories,config,message_bus} \
  src/industrial_orchestrator/presentation/{api,rpc,cli} \
  tests/{unit,integration,acceptance}/{domain,application,infrastructure,presentation}

# Create foundational domain entities
cat > src/industrial_orchestrator/domain/entities/session.py << 'EOF'
"""
INDUSTRIAL-GRADE SESSION ENTITY
Core business entity representing an OpenCode execution session.
Designed for resilience, auditability, and precise state management.
"""

from datetime import datetime, timezone
from enum import Enum, auto
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

from ..value_objects.session_status import SessionStatus
from ..value_objects.execution_metrics import ExecutionMetrics
from ..events.session_events import SessionCreated, SessionStatusChanged
from ..exceptions.session_exceptions import InvalidSessionTransition


class SessionType(str, Enum):
    """Type of orchestration session"""
    PLANNING = "planning"
    EXECUTION = "execution"
    REVIEW = "review"
    DEBUG = "debug"
    INTEGRATION = "integration"


class SessionPriority(int, Enum):
    """Execution priority level"""
    CRITICAL = 0    # Blocking failures, immediate attention
    HIGH = 1        # Core path, user-blocking
    MEDIUM = 2      # Important but can wait
    LOW = 3         # Background, non-urgent
    DEFERRED = 4    # Can be scheduled later


class SessionEntity(BaseModel):
    """
    Industrial Session Entity
    
    Key Design Principles:
    1. Immutable core fields (id, created_at)
    2. State machine enforcement via status transitions
    3. Audit trail through events
    4. Metrics-driven performance tracking
    5. Resource isolation via execution_context
    """
    
    # Immutable identifiers
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Business identity
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    session_type: SessionType = Field(default=SessionType.EXECUTION)
    priority: SessionPriority = Field(default=SessionPriority.MEDIUM)
    
    # State management
    status: SessionStatus = Field(default=SessionStatus.PENDING)
    status_updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    parent_id: Optional[UUID] = None
    child_ids: List[UUID] = Field(default_factory=list)
    
    # Execution context
    agent_config: Dict[str, Any] = Field(default_factory=dict)
    model_config: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+$")
    initial_prompt: str = Field(..., min_length=1, max_length=10000)
    
    # Resource allocation
    max_duration_seconds: int = Field(default=3600, ge=60, le=86400)
    cpu_limit: Optional[float] = Field(None, ge=0.1, le=8.0)
    memory_limit_mb: Optional[int] = Field(None, ge=100, le=8192)
    
    # Metrics & telemetry
    metrics: ExecutionMetrics = Field(default_factory=ExecutionMetrics)
    checkpoints: List[Dict[str, Any]] = Field(default_factory=list)
    
    # System metadata
    created_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Domain events (not persisted, for CQRS)
    _events: List[Any] = []
    
    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True
    
    @validator('title')
    def validate_title_format(cls, v: str) -> str:
        """Enforce industrial naming convention"""
        if not v.strip():
            raise ValueError("Session title cannot be empty")
        
        # Reject generic AI-generated titles
        generic_patterns = [
            'test session', 'new session', 'untitled',
            'coding task', 'development session'
        ]
        
        if v.lower() in generic_patterns:
            raise ValueError(f"Title '{v}' is too generic. Use descriptive, industrial naming")
        
        return v.strip()
    
    @validator('agent_config')
    def validate_agent_config(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure agent configuration follows industrial standards"""
        if not v:
            return {'default_agent': 'industrial-coder'}
        
        # Validate agent name format
        for agent_name in v.keys():
            if not agent_name.replace('_', '').replace('-', '').isalnum():
                raise ValueError(f"Invalid agent name: {agent_name}. Use alphanumeric with underscores/hyphens")
        
        return v
    
    def transition_to(self, new_status: SessionStatus) -> None:
        """
        Industrial-grade state transition with validation
        
        Design Principle: State changes are explicit, validated events
        """
        if not self.status.can_transition_to(new_status):
            raise InvalidSessionTransition(
                current_status=self.status,
                target_status=new_status,
                session_id=self.id
            )
        
        old_status = self.status
        self.status = new_status
        self.status_updated_at = datetime.now(timezone.utc)
        
        # Record state transition event
        event = SessionStatusChanged(
            session_id=self.id,
            old_status=old_status,
            new_status=new_status,
            timestamp=self.status_updated_at
        )
        self._events.append(event)
    
    def start_execution(self) -> None:
        """Begin session execution with validation"""
        if self.status != SessionStatus.PENDING:
            raise InvalidSessionTransition(
                current_status=self.status,
                target_status=SessionStatus.RUNNING,
                session_id=self.id,
                reason="Can only start from PENDING state"
            )
        
        self.transition_to(SessionStatus.RUNNING)
        self.metrics.started_at = datetime.now(timezone.utc)
    
    def complete_with_result(self, result: Dict[str, Any]) -> None:
        """Mark session as completed with execution results"""
        self.transition_to(SessionStatus.COMPLETED)
        self.metrics.completed_at = datetime.now(timezone.utc)
        self.metrics.result = result
        
        # Calculate duration
        if self.metrics.started_at:
            duration = (self.metrics.completed_at - self.metrics.started_at).total_seconds()
            self.metrics.execution_duration_seconds = duration
    
    def fail_with_error(self, error: Exception, error_context: Dict[str, Any] = None) -> None:
        """Handle session failure with detailed error context"""
        self.transition_to(SessionStatus.FAILED)
        self.metrics.failed_at = datetime.now(timezone.utc)
        self.metrics.error = {
            'type': error.__class__.__name__,
            'message': str(error),
            'context': error_context or {}
        }
    
    def add_checkpoint(self, data: Dict[str, Any]) -> None:
        """Add execution checkpoint for recovery"""
        checkpoint = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': data,
            'sequence': len(self.checkpoints) + 1
        }
        self.checkpoints.append(checkpoint)
        
        # Limit checkpoint history
        if len(self.checkpoints) > 100:
            self.checkpoints = self.checkpoints[-100:]
    
    def get_latest_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Retrieve most recent checkpoint for recovery"""
        if not self.checkpoints:
            return None
        return self.checkpoints[-1]
    
    def collect_events(self) -> List[Any]:
        """Collect and clear domain events for publishing"""
        events = self._events.copy()
        self._events.clear()
        return events
    
    def calculate_health_score(self) -> float:
        """Calculate session health score (0.0 to 1.0)"""
        if self.status == SessionStatus.COMPLETED:
            return 1.0
        
        if self.status == SessionStatus.FAILED:
            return 0.0
        
        # Calculate based on duration vs limit
        if self.status == SessionStatus.RUNNING and self.metrics.started_at:
            elapsed = (datetime.now(timezone.utc) - self.metrics.started_at).total_seconds()
            progress_ratio = min(elapsed / self.max_duration_seconds, 1.0)
            
            # Penalize long-running sessions
            if progress_ratio > 0.9:
                return 0.3  # At risk
            elif progress_ratio > 0.7:
                return 0.7  # Warning
            else:
                return 0.9  # Healthy
        
        return 0.8  # Default for other states
    
    def is_recoverable(self) -> bool:
        """Determine if session can be recovered from failure"""
        recoverable_statuses = {
            SessionStatus.FAILED,
            SessionStatus.TIMEOUT,
            SessionStatus.STOPPED
        }
        
        return (
            self.status in recoverable_statuses and
            len(self.checkpoints) > 0 and
            self.metrics.retry_count < 3
        )
EOF

# Create value objects with industrial precision
cat > src/industrial_orchestrator/domain/value_objects/session_status.py << 'EOF'
"""
INDUSTRIAL SESSION STATUS STATE MACHINE
Precise state transitions with validation for resilient orchestration.
"""

from enum import Enum
from typing import Set, Dict


class SessionStatus(str, Enum):
    """
    Industrial-grade session status enumeration
    
    Design Principles:
    1. Terminal states are clearly defined
    2. Transitions are validated via can_transition_to
    3. Each state has clear business meaning
    """
    
    # Initial state
    PENDING = "pending"            # Created, awaiting execution
    
    # Active states
    QUEUED = "queued"              # In execution queue
    RUNNING = "running"            # Actively executing
    PAUSED = "paused"              # Manually paused
    
    # Terminal success states
    COMPLETED = "completed"        # Successfully finished
    PARTIALLY_COMPLETED = "partially_completed"  # Some sub-tasks succeeded
    
    # Terminal failure states
    FAILED = "failed"              # Execution failed
    TIMEOUT = "timeout"            # Exceeded max duration
    STOPPED = "stopped"            # Manually stopped
    CANCELLED = "cancelled"        # Cancelled before execution
    
    # System states
    ORPHANED = "orphaned"          # Lost parent/child relationship
    DEGRADED = "degraded"          # Running with reduced capacity
    
    @classmethod
    def get_terminal_states(cls) -> Set["SessionStatus"]:
        """States from which no further transitions are allowed"""
        return {
            cls.COMPLETED,
            cls.PARTIALLY_COMPLETED,
            cls.FAILED,
            cls.TIMEOUT,
            cls.STOPPED,
            cls.CANCELLED,
            cls.ORPHANED,
        }
    
    @classmethod
    def get_active_states(cls) -> Set["SessionStatus"]:
        """States where session is actively being processed"""
        return {
            cls.QUEUED,
            cls.RUNNING,
            cls.PAUSED,
            cls.DEGRADED,
        }
    
    @classmethod
    def get_error_states(cls) -> Set["SessionStatus"]:
        """States indicating some form of failure"""
        return {
            cls.FAILED,
            cls.TIMEOUT,
            cls.STOPPED,
            cls.CANCELLED,
            cls.ORPHANED,
            cls.DEGRADED,
        }
    
    def can_transition_to(self, target_status: "SessionStatus") -> bool:
        """
        Industrial-grade state transition validation
        
        Returns True if transition from current to target is valid
        """
        transition_map: Dict[SessionStatus, Set[SessionStatus]] = {
            # From PENDING
            SessionStatus.PENDING: {
                SessionStatus.QUEUED,     # Scheduled for execution
                SessionStatus.CANCELLED,  # Cancelled before queueing
                SessionStatus.FAILED,     # Immediate failure (e.g., validation)
            },
            
            # From QUEUED
            SessionStatus.QUEUED: {
                SessionStatus.RUNNING,    # Execution started
                SessionStatus.CANCELLED,  # Cancelled while queued
                SessionStatus.FAILED,     # Pre-execution failure
            },
            
            # From RUNNING
            SessionStatus.RUNNING: {
                SessionStatus.COMPLETED,          # Successful completion
                SessionStatus.PARTIALLY_COMPLETED, # Partial success
                SessionStatus.FAILED,             # Execution failure
                SessionStatus.TIMEOUT,            # Exceeded time limit
                SessionStatus.PAUSED,             # Manually paused
                SessionStatus.STOPPED,            # Manually stopped
                SessionStatus.DEGRADED,           # Running with issues
            },
            
            # From PAUSED
            SessionStatus.PAUSED: {
                SessionStatus.RUNNING,    # Resumed execution
                SessionStatus.STOPPED,    # Stopped while paused
                SessionStatus.CANCELLED,  # Cancelled while paused
            },
            
            # From DEGRADED
            SessionStatus.DEGRADED: {
                SessionStatus.RUNNING,    # Recovered to normal
                SessionStatus.FAILED,     # Degraded further to failure
                SessionStatus.COMPLETED,  # Managed to complete despite issues
                SessionStatus.STOPPED,    # Manually stopped
            },
            
            # From PARTIALLY_COMPLETED (can sometimes be recovered)
            SessionStatus.PARTIALLY_COMPLETED: {
                SessionStatus.RUNNING,    # Retry failed sub-tasks
                SessionStatus.COMPLETED,  # All sub-tasks eventually succeeded
            },
            
            # Terminal states - no transitions allowed
            **{state: set() for state in cls.get_terminal_states()},
        }
        
        return target_status in transition_map.get(self, set())
    
    def is_terminal(self) -> bool:
        """Check if status is terminal (no further transitions)"""
        return self in self.get_terminal_states()
    
    def is_active(self) -> bool:
        """Check if status indicates active processing"""
        return self in self.get_active_states()
    
    def is_error(self) -> bool:
        """Check if status indicates an error condition"""
        return self in self.get_error_states()
    
    def get_emoji(self) -> str:
        """Industrial visualization via emoji (for dashboard)"""
        emoji_map = {
            SessionStatus.PENDING: "⏳",
            SessionStatus.QUEUED: "📋",
            SessionStatus.RUNNING: "⚙️",
            SessionStatus.PAUSED: "⏸️",
            SessionStatus.COMPLETED: "✅",
            SessionStatus.PARTIALLY_COMPLETED: "⚠️",
            SessionStatus.FAILED: "❌",
            SessionStatus.TIMEOUT: "⏰",
            SessionStatus.STOPPED: "🛑",
            SessionStatus.CANCELLED: "🚫",
            SessionStatus.ORPHANED: "🧩",
            SessionStatus.DEGRADED: "🔻",
        }
        return emoji_map.get(self, "❓")
    
    def get_color_code(self) -> str:
        """Color coding for industrial dashboard"""
        color_map = {
            SessionStatus.PENDING: "#6B7280",      # Gray
            SessionStatus.QUEUED: "#3B82F6",       # Blue
            SessionStatus.RUNNING: "#10B981",      # Green
            SessionStatus.PAUSED: "#F59E0B",       # Yellow
            SessionStatus.COMPLETED: "#059669",    # Dark green
            SessionStatus.PARTIALLY_COMPLETED: "#D97706", # Amber
            SessionStatus.FAILED: "#DC2626",       # Red
            SessionStatus.TIMEOUT: "#7C3AED",      # Purple
            SessionStatus.STOPPED: "#4B5563",      # Dark gray
            SessionStatus.CANCELLED: "#374151",    # Darker gray
            SessionStatus.ORPHANED: "#9333EA",     # Violet
            SessionStatus.DEGRADED: "#F97316",     # Orange
        }
        return color_map.get(self, "#000000")
EOF

# Create execution metrics value object
cat > src/industrial_orchestrator/domain/value_objects/execution_metrics.py << 'EOF'
"""
INDUSTRIAL EXECUTION METRICS
Precise telemetry for performance analysis and optimization.
"""

from datetime import datetime
from typing import Optional, Dict, Any
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
    
    class Config:
        arbitrary_types_allowed = True
    
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
EOF

#### **1.3 TDD Setup with Industrial-Grade Test Factories**

```bash
# Create test factory for domain entities
cat > tests/unit/domain/factories/session_factory.py << 'EOF'
"""
INDUSTRIAL TEST FACTORY PATTERN
Generates realistic, varied test data for comprehensive testing.
"""

from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4
from typing import Optional, Dict, Any, List

import factory
from factory import Faker, LazyFunction, LazyAttribute, SubFactory
import faker

from src.industrial_orchestrator.domain.entities.session import (
    SessionEntity, SessionType, SessionPriority
)
from src.industrial_orchestrator.domain.value_objects.session_status import SessionStatus
from src.industrial_orchestrator.domain.value_objects.execution_metrics import ExecutionMetrics


class IndustrialFaker(faker.Faker):
    """Extended Faker with industrial-specific data"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_provider(IndustrialProvider)
    
    def industrial_title(self) -> str:
        """Generate industrial-style session titles"""
        prefixes = ['CYBERNETIC', 'INDUSTRIAL', 'AUTONOMOUS', 'ROBUST', 'RESILIENT']
        components = ['ORCHESTRATION', 'EXECUTION', 'PIPELINE', 'WORKFLOW', 'AUTOMATION']
        suffixes = ['SESSION', 'TASK', 'JOB', 'PROCESS', 'OPERATION']
        
        return f"{self.random_element(prefixes)} {self.random_element(components)} {self.random_element(suffixes)}"
    
    def agent_config(self) -> Dict[str, Any]:
        """Generate realistic agent configurations"""
        agents = {
            'industrial-architect': {
                'model': 'anthropic/claude-sonnet-4.5',
                'temperature': 0.1,
                'max_tokens': 4000
            },
            'precision-coder': {
                'model': 'openai/gpt-4o',
                'temperature': 0.3,
                'max_tokens': 8000
            },
            'meticulous-reviewer': {
                'model': 'anthropic/claude-sonnet-4.5',
                'temperature': 0.05,
                'max_tokens': 2000
            }
        }
        return {self.random_element(list(agents.keys())): agents[self.random_element(list(agents.keys()))]}
    
    def execution_metrics(self) -> Dict[str, Any]:
        """Generate realistic execution metrics"""
        return {
            'api_calls_count': self.random_int(min=1, max=50),
            'execution_duration_seconds': self.random_int(min=10, max=3600),
            'cpu_usage_percent': self.random_int(min=10, max=90),
            'success_rate': self.random.uniform(0.7, 1.0)
        }


class IndustrialProvider(faker.providers.BaseProvider):
    """Custom industrial data provider"""
    
    def session_type(self) -> SessionType:
        return self.random_element(list(SessionType))
    
    def session_priority(self) -> SessionPriority:
        return self.random_element(list(SessionPriority))
    
    def session_status(self) -> SessionStatus:
        return self.random_element(list(SessionStatus))


# Register the industrial faker
Faker.add_provider(IndustrialProvider)


class ExecutionMetricsFactory(factory.Factory):
    """Factory for ExecutionMetrics value object"""
    
    class Meta:
        model = ExecutionMetrics
    
    # Timestamps with realistic relationships
    created_at = LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(hours=1))
    started_at = LazyAttribute(lambda o: o.created_at + timedelta(seconds=30))
    completed_at = LazyAttribute(lambda o: o.started_at + timedelta(seconds=o.execution_duration_seconds))
    
    # Performance metrics
    queue_duration_seconds = LazyAttribute(lambda o: (o.started_at - o.created_at).total_seconds())
    execution_duration_seconds = factory.Faker('random_int', min=60, max=1800)
    total_duration_seconds = LazyAttribute(lambda o: o.queue_duration_seconds + o.execution_duration_seconds)
    
    # Resource usage
    cpu_usage_percent = factory.Faker('random_int', min=10, max=80)
    memory_usage_mb = factory.Faker('random_int', min=100, max=2048)
    disk_usage_mb = factory.Faker('random_int', min=10, max=500)
    
    # API metrics
    api_calls_count = factory.Faker('random_int', min=1, max=20)
    api_errors_count = factory.LazyAttribute(lambda o: o.api_calls_count // 10)  # 10% error rate
    retry_count = factory.Faker('random_int', min=0, max=2)
    
    # Quality metrics
    success_rate = factory.Faker('pyfloat', left_digits=1, right_digits=2, positive=True, min_value=0.8, max_value=1.0)
    confidence_score = factory.Faker('pyfloat', left_digits=1, right_digits=2, positive=True, min_value=0.7, max_value=0.95)
    
    @factory.post_generation
    def add_warnings(self, create, extracted, **kwargs):
        """Add random warnings if needed"""
        if extracted is not None:
            self.warnings = extracted
        elif factory.Faker('boolean', chance_of_getting_true=30):
            self.warnings = [{
                'type': factory.Faker('random_element', elements=['performance', 'resource', 'quality']),
                'message': factory.Faker('sentence'),
                'timestamp': datetime.now(timezone.utc).isoformat()
            } for _ in range(factory.Faker('random_int', min=1, max=3))]


class SessionEntityFactory(factory.Factory):
    """Industrial-grade factory for SessionEntity"""
    
    class Meta:
        model = SessionEntity
    
    # Identity
    title = factory.LazyFunction(lambda: IndustrialFaker().industrial_title())
    description = factory.Faker('paragraph', nb_sentences=3)
    session_type = factory.Faker('session_type')
    priority = factory.Faker('session_priority')
    
    # State
    status = SessionStatus.PENDING
    status_updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    
    # Execution context
    agent_config = factory.LazyFunction(lambda: IndustrialFaker().agent_config())
    model_config = factory.LazyAttribute(lambda o: next(iter(o.agent_config.values()))['model'])
    initial_prompt = factory.Faker('text', max_nb_chars=500)
    
    # Resource allocation
    max_duration_seconds = factory.Faker('random_int', min=300, max=7200)
    cpu_limit = factory.Faker('pyfloat', left_digits=1, right_digits=1, positive=True, min_value=0.5, max_value=4.0)
    memory_limit_mb = factory.Faker('random_int', min=512, max=4096)
    
    # Metrics
    metrics = SubFactory(ExecutionMetricsFactory)
    
    # Metadata
    tags = factory.LazyFunction(lambda: [IndustrialFaker().word() for _ in range(3)])
    metadata = factory.Dict({
        'source': 'factory',
        'test_id': factory.LazyFunction(lambda: str(uuid4())),
        'environment': 'testing'
    })
    
    class Params:
        """Factory variants for different test scenarios"""
        
        # Completed session variant
        completed = factory.Trait(
            status=SessionStatus.COMPLETED,
            metrics=factory.SubFactory(
                ExecutionMetricsFactory,
                completed_at=factory.LazyAttribute(
                    lambda o: o.started_at + timedelta(seconds=o.execution_duration_seconds)
                ),
                success_rate=1.0,
                confidence_score=0.95
            )
        )
        
        # Failed session variant
        failed = factory.Trait(
            status=SessionStatus.FAILED,
            metrics=factory.SubFactory(
                ExecutionMetricsFactory,
                failed_at=factory.LazyAttribute(
                    lambda o: o.started_at + timedelta(seconds=o.execution_duration_seconds / 2)
                ),
                success_rate=0.0,
                error={
                    'type': 'TimeoutError',
                    'message': 'Execution timeout exceeded',
                    'context': {'timeout_seconds': 1800}
                }
            )
        )
        
        # Running session variant
        running = factory.Trait(
            status=SessionStatus.RUNNING,
            metrics=factory.SubFactory(
                ExecutionMetricsFactory,
                started_at=factory.LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(minutes=5)),
                execution_duration_seconds=300
            )
        )
        
        # Degraded session variant
        degraded = factory.Trait(
            status=SessionStatus.DEGRADED,
            metrics=factory.SubFactory(
                ExecutionMetricsFactory,
                api_errors_count=5,
                warnings=[
                    {
                        'type': 'performance',
                        'message': 'High API latency detected',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                ]
            )
        )
    
    @factory.post_generation
    def add_checkpoints(self, create, extracted, **kwargs):
        """Add realistic checkpoints based on session state"""
        if extracted is not None:
            self.checkpoints = extracted
        elif self.status.is_active():
            # Add checkpoints for active sessions
            checkpoint_count = factory.Faker('random_int', min=1, max=5).generate()
            self.checkpoints = [
                {
                    'timestamp': (datetime.now(timezone.utc) - timedelta(minutes=i)).isoformat(),
                    'data': {
                        'progress': i / checkpoint_count,
                        'step': f'step_{i}',
                        'state': 'processing'
                    },
                    'sequence': i + 1
                }
                for i in range(checkpoint_count)
            ]


# Utility functions for test scenarios
def create_session_with_dependencies(
    parent_session: Optional[SessionEntity] = None,
    child_count: int = 0
) -> SessionEntity:
    """Create session with parent/child relationships"""
    session = SessionEntityFactory()
    
    if parent_session:
        session.parent_id = parent_session.id
        parent_session.child_ids.append(session.id)
    
    if child_count > 0:
        session.child_ids = [
            SessionEntityFactory(parent_id=session.id).id
            for _ in range(child_count)
        ]
    
    return session


def create_session_batch(
    count: int,
    status_distribution: Optional[Dict[SessionStatus, float]] = None
) -> List[SessionEntity]:
    """Create batch of sessions with specified status distribution"""
    if status_distribution is None:
        status_distribution = {
            SessionStatus.PENDING: 0.2,
            SessionStatus.RUNNING: 0.3,
            SessionStatus.COMPLETED: 0.4,
            SessionStatus.FAILED: 0.1
        }
    
    sessions = []
    for i in range(count):
        # Determine status based on distribution
        rand = factory.Faker('pyfloat', min_value=0, max_value=1).generate()
        cumulative = 0
        selected_status = SessionStatus.PENDING
        
        for status, probability in status_distribution.items():
            cumulative += probability
            if rand <= cumulative:
                selected_status = status
                break
        
        # Create session with selected status
        if selected_status == SessionStatus.COMPLETED:
            session = SessionEntityFactory(completed=True)
        elif selected_status == SessionStatus.FAILED:
            session = SessionEntityFactory(failed=True)
        elif selected_status == SessionStatus.RUNNING:
            session = SessionEntityFactory(running=True)
        else:
            session = SessionEntityFactory(status=selected_status)
        
        sessions.append(session)
    
    return sessions
EOF

# Create comprehensive test suite with TDD approach
cat > tests/unit/domain/test_session_entity.py << 'EOF'
"""
INDUSTRIAL-GRADE SESSION ENTITY TESTS
Test-driven development with comprehensive edge case coverage.
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import Mock, patch

from src.industrial_orchestrator.domain.entities.session import SessionEntity, SessionType, SessionPriority
from src.industrial_orchestrator.domain.value_objects.session_status import SessionStatus
from src.industrial_orchestrator.domain.exceptions.session_exceptions import InvalidSessionTransition

from ..factories.session_factory import SessionEntityFactory, create_session_batch


class TestSessionEntityCreation:
    """Test session entity creation and validation"""
    
    def test_create_minimal_session(self):
        """Test creating session with minimal required fields"""
        session = SessionEntity(
            title="CYBERNETIC EXECUTION SESSION",
            initial_prompt="Implement resilient authentication system"
        )
        
        assert session.id is not None
        assert session.title == "CYBERNETIC EXECUTION SESSION"
        assert session.status == SessionStatus.PENDING
        assert session.session_type == SessionType.EXECUTION
        assert session.priority == SessionPriority.MEDIUM
        assert session.created_at is not None
    
    def test_create_full_session(self):
        """Test creating session with all fields"""
        session_id = uuid4()
        created_at = datetime.now(timezone.utc)
        
        session = SessionEntity(
            id=session_id,
            created_at=created_at,
            title="INDUSTRIAL ORCHESTRATION PIPELINE",
            description="Multi-stage code generation pipeline with validation",
            session_type=SessionType.PLANNING,
            priority=SessionPriority.HIGH,
            agent_config={
                "industrial-architect": {
                    "model": "anthropic/claude-sonnet-4.5",
                    "temperature": 0.1
                }
            },
            initial_prompt="Design microservices architecture for e-commerce",
            max_duration_seconds=7200,
            cpu_limit=2.0,
            memory_limit_mb=4096,
            tags=["architecture", "microservices", "planning"],
            metadata={"project": "ecommerce", "phase": "design"}
        )
        
        assert session.id == session_id
        assert session.created_at == created_at
        assert session.title == "INDUSTRIAL ORCHESTRATION PIPELINE"
        assert session.session_type == SessionType.PLANNING
        assert session.priority == SessionPriority.HIGH
        assert "industrial-architect" in session.agent_config
        assert len(session.tags) == 3
    
    @pytest.mark.parametrize("invalid_title", [
        "",
        "   ",
        "test session",  # Too generic
        "new session",
        "untitled",
    ])
    def test_invalid_titles_rejected(self, invalid_title):
        """Test that generic/invalid titles are rejected"""
        with pytest.raises(ValueError, match="generic"):
            SessionEntity(
                title=invalid_title,
                initial_prompt="test"
            )
    
    def test_agent_config_validation(self):
        """Test agent configuration validation"""
        # Valid config
        session = SessionEntity(
            title="VALID AGENT TEST",
            initial_prompt="test",
            agent_config={
                "valid_agent_1": {"model": "openai/gpt-4o"},
                "valid-agent-2": {"model": "anthropic/claude"}
            }
        )
        assert len(session.agent_config) == 2
        
        # Invalid agent name
        with pytest.raises(ValueError, match="Invalid agent name"):
            SessionEntity(
                title="INVALID AGENT TEST",
                initial_prompt="test",
                agent_config={"invalid agent!": {"model": "test"}}
            )
    
    def test_default_agent_config_when_empty(self):
        """Test default agent config is provided when empty"""
        session = SessionEntity(
            title="DEFAULT AGENT TEST",
            initial_prompt="test"
        )
        assert "default_agent" in session.agent_config
        assert session.agent_config["default_agent"] == "industrial-coder"


class TestSessionStateTransitions:
    """Test industrial-grade state machine transitions"""
    
    def test_valid_transitions(self):
        """Test valid state transitions"""
        session = SessionEntityFactory(status=SessionStatus.PENDING)
        
        # PENDING -> QUEUED
        session.transition_to(SessionStatus.QUEUED)
        assert session.status == SessionStatus.QUEUED
        
        # QUEUED -> RUNNING
        session.transition_to(SessionStatus.RUNNING)
        assert session.status == SessionStatus.RUNNING
        
        # RUNNING -> COMPLETED
        session.transition_to(SessionStatus.COMPLETED)
        assert session.status == SessionStatus.COMPLETED
    
    def test_invalid_transitions(self):
        """Test invalid state transitions raise exceptions"""
        session = SessionEntityFactory(status=SessionStatus.PENDING)
        
        # PENDING -> COMPLETED (invalid)
        with pytest.raises(InvalidSessionTransition):
            session.transition_to(SessionStatus.COMPLETED)
        
        # Set to terminal state
        session.transition_to(SessionStatus.CANCELLED)
        
        # COMPLETED -> RUNNING (invalid - terminal state)
        with pytest.raises(InvalidSessionTransition):
            session.transition_to(SessionStatus.RUNNING)
    
    @pytest.mark.parametrize("start_status,target_status,should_succeed", [
        (SessionStatus.PENDING, SessionStatus.QUEUED, True),
        (SessionStatus.PENDING, SessionStatus.CANCELLED, True),
        (SessionStatus.PENDING, SessionStatus.RUNNING, False),
        (SessionStatus.RUNNING, SessionStatus.COMPLETED, True),
        (SessionStatus.RUNNING, SessionStatus.FAILED, True),
        (SessionStatus.RUNNING, SessionStatus.PENDING, False),
        (SessionStatus.COMPLETED, SessionStatus.RUNNING, False),
        (SessionStatus.FAILED, SessionStatus.RUNNING, False),
    ])
    def test_transition_matrix(self, start_status, target_status, should_succeed):
        """Comprehensive transition matrix testing"""
        session = SessionEntityFactory(status=start_status)
        
        if should_succeed:
            session.transition_to(target_status)
            assert session.status == target_status
        else:
            with pytest.raises(InvalidSessionTransition):
                session.transition_to(target_status)
    
    def test_start_execution_method(self):
        """Test dedicated start_execution method"""
        session = SessionEntityFactory(status=SessionStatus.PENDING)
        
        session.start_execution()
        
        assert session.status == SessionStatus.RUNNING
        assert session.metrics.started_at is not None
        assert session.metrics.queue_duration_seconds is not None
        
        # Cannot start execution from non-pending state
        with pytest.raises(InvalidSessionTransition):
            session.start_execution()
    
    def test_complete_with_result(self):
        """Test completion with results"""
        session = SessionEntityFactory(status=SessionStatus.RUNNING)
        session.metrics.start_timing()
        
        result = {
            "files_created": ["auth.py", "models.py"],
            "tests_passed": 15,
            "coverage_percent": 92.5
        }
        
        session.complete_with_result(result)
        
        assert session.status == SessionStatus.COMPLETED
        assert session.metrics.completed_at is not None
        assert session.metrics.result == result
        assert session.metrics.execution_duration_seconds > 0
    
    def test_fail_with_error(self):
        """Test failure with error context"""
        session = SessionEntityFactory(status=SessionStatus.RUNNING)
        session.metrics.start_timing()
        
        error = TimeoutError("Execution timeout exceeded")
        error_context = {"timeout_seconds": 1800, "attempts": 3}
        
        session.fail_with_error(error, error_context)
        
        assert session.status == SessionStatus.FAILED
        assert session.metrics.failed_at is not None
        assert session.metrics.error["type"] == "TimeoutError"
        assert session.metrics.error["context"] == error_context


class TestSessionCheckpointing:
    """Test industrial checkpointing system"""
    
    def test_add_checkpoint(self):
        """Test adding execution checkpoints"""
        session = SessionEntityFactory()
        
        checkpoint_data = {
            "progress": 0.5,
            "files_processed": ["main.py", "utils.py"],
            "current_step": "code_generation"
        }
        
        session.add_checkpoint(checkpoint_data)
        
        assert len(session.checkpoints) == 1
        checkpoint = session.checkpoints[0]
        
        assert checkpoint["sequence"] == 1
        assert checkpoint["data"] == checkpoint_data
        assert "timestamp" in checkpoint
    
    def test_checkpoint_sequence(self):
        """Test checkpoint sequencing"""
        session = SessionEntityFactory()
        
        for i in range(1, 6):
            session.add_checkpoint({"step": f"step_{i}"})
            assert session.checkpoints[-1]["sequence"] == i
        
        assert len(session.checkpoints) == 5
    
    def test_checkpoint_rotation(self):
        """Test checkpoint list rotation at limit"""
        session = SessionEntityFactory()
        
        # Add more checkpoints than limit
        for i in range(1, 151):
            session.add_checkpoint({"step": f"step_{i}"})
        
        # Should keep only last 100
        assert len(session.checkpoints) == 100
        assert session.checkpoints[0]["sequence"] == 51  # First kept checkpoint
        assert session.checkpoints[-1]["sequence"] == 150  # Last checkpoint
    
    def test_get_latest_checkpoint(self):
        """Test retrieving latest checkpoint"""
        session = SessionEntityFactory()
        
        assert session.get_latest_checkpoint() is None
        
        checkpoint1 = {"step": "analysis"}
        checkpoint2 = {"step": "generation"}
        
        session.add_checkpoint(checkpoint1)
        assert session.get_latest_checkpoint()["data"] == checkpoint1
        
        session.add_checkpoint(checkpoint2)
        assert session.get_latest_checkpoint()["data"] == checkpoint2


class TestSessionHealthScoring:
    """Test session health calculation"""
    
    def test_health_score_completed(self):
        """Test health score for completed session"""
        session = SessionEntityFactory(completed=True)
        assert session.calculate_health_score() == 1.0
    
    def test_health_score_failed(self):
        """Test health score for failed session"""
        session = SessionEntityFactory(failed=True)
        assert session.calculate_health_score() == 0.0
    
    def test_health_score_running_healthy(self):
        """Test health score for healthy running session"""
        session = SessionEntityFactory(running=True)
        session.metrics.started_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        session.max_duration_seconds = 600  # 10 minutes
        
        # 1 minute into 10-minute session = 10% progress
        assert session.calculate_health_score() == 0.9
    
    def test_health_score_running_at_risk(self):
        """Test health score for at-risk running session"""
        session = SessionEntityFactory(running=True)
        session.metrics.started_at = datetime.now(timezone.utc) - timedelta(minutes=9)
        session.max_duration_seconds = 600  # 10 minutes
        
        # 9 minutes into 10-minute session = 90% progress
        assert session.calculate_health_score() == 0.3
    
    def test_health_score_default(self):
        """Test default health score for non-running sessions"""
        session = SessionEntityFactory(status=SessionStatus.PENDING)
        assert session.calculate_health_score() == 0.8


class TestSessionRecoverability:
    """Test session recoverability determination"""
    
    def test_recoverable_failed_with_checkpoints(self):
        """Test failed session with checkpoints is recoverable"""
        session = SessionEntityFactory(failed=True)
        session.add_checkpoint({"progress": 0.7})
        
        assert session.is_recoverable() is True
    
    def test_unrecoverable_failed_no_checkpoints(self):
        """Test failed session without checkpoints is not recoverable"""
        session = SessionEntityFactory(failed=True)
        # No checkpoints added
        
        assert session.is_recoverable() is False
    
    def test_unrecoverable_excessive_retries(self):
        """Test session with excessive retries is not recoverable"""
        session = SessionEntityFactory(failed=True)
        session.add_checkpoint({"progress": 0.7})
        session.metrics.retry_count = 5  # Exceeds threshold
        
        assert session.is_recoverable() is False
    
    def test_unrecoverable_completed(self):
        """Test completed session is not recoverable"""
        session = SessionEntityFactory(completed=True)
        session.add_checkpoint({"progress": 1.0})
        
        assert session.is_recoverable() is False


class TestSessionEventCollection:
    """Test domain event collection"""
    
    def test_event_collection_on_transition(self):
        """Test events are collected on state transitions"""
        session = SessionEntityFactory(status=SessionStatus.PENDING)
        
        # Initially no events
        assert len(session.collect_events()) == 0
        
        # Transition creates event
        session.transition_to(SessionStatus.QUEUED)
        
        events = session.collect_events()
        assert len(events) == 1
        assert events[0].old_status == SessionStatus.PENDING
        assert events[0].new_status == SessionStatus.QUEUED
        
        # Events cleared after collection
        assert len(session.collect_events()) == 0
    
    def test_multiple_events_collection(self):
        """Test multiple events are collected"""
        session = SessionEntityFactory(status=SessionStatus.PENDING)
        
        session.transition_to(SessionStatus.QUEUED)
        session.transition_to(SessionStatus.RUNNING)
        
        events = session.collect_events()
        assert len(events) == 2
        assert events[0].new_status == SessionStatus.QUEUED
        assert events[1].new_status == SessionStatus.RUNNING


class TestSessionFactoryIntegration:
    """Test integration with factory pattern"""
    
    def test_factory_creates_valid_sessions(self):
        """Test factory creates valid session entities"""
        session = SessionEntityFactory()
        
        assert isinstance(session, SessionEntity)
        assert session.id is not None
        assert session.title is not None
        assert session.initial_prompt is not None
        assert session.metrics is not None
    
    def test_factory_variants(self):
        """Test factory variants create appropriate sessions"""
        completed_session = SessionEntityFactory(completed=True)
        assert completed_session.status == SessionStatus.COMPLETED
        assert completed_session.metrics.success_rate == 1.0
        
        failed_session = SessionEntityFactory(failed=True)
        assert failed_session.status == SessionStatus.FAILED
        assert failed_session.metrics.error is not None
        
        running_session = SessionEntityFactory(running=True)
        assert running_session.status == SessionStatus.RUNNING
        assert running_session.metrics.started_at is not None
    
    def test_create_session_batch(self):
        """Test batch session creation"""
        sessions = create_session_batch(10)
        
        assert len(sessions) == 10
        assert all(isinstance(s, SessionEntity) for s in sessions)
        
        # Check distribution (default)
        statuses = [s.status for s in sessions]
        assert SessionStatus.PENDING in statuses
        assert SessionStatus.RUNNING in statuses
        assert SessionStatus.COMPLETED in statuses
        assert SessionStatus.FAILED in statuses
    
    def test_create_session_with_dependencies(self):
        """Test session creation with parent/child relationships"""
        parent = SessionEntityFactory()
        child = create_session_with_dependencies(parent_session=parent)
        
        assert child.parent_id == parent.id
        assert child.id in parent.child_ids


class TestSessionEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_extreme_duration_limits(self):
        """Test session with extreme duration limits"""
        # Minimum duration
        session = SessionEntity(
            title="MIN DURATION TEST",
            initial_prompt="test",
            max_duration_seconds=60
        )
        assert session.max_duration_seconds == 60
        
        # Maximum duration
        session = SessionEntity(
            title="MAX DURATION TEST",
            initial_prompt="test",
            max_duration_seconds=86400
        )
        assert session.max_duration_seconds == 86400
        
        # Below minimum (should fail validation)
        with pytest.raises(ValueError):
            SessionEntity(
                title="INVALID DURATION",
                initial_prompt="test",
                max_duration_seconds=59
            )
    
    def test_large_prompt_handling(self):
        """Test handling of large prompts"""
        large_prompt = "A" * 10000  # Maximum allowed
        
        session = SessionEntity(
            title="LARGE PROMPT TEST",
            initial_prompt=large_prompt
        )
        assert len(session.initial_prompt) == 10000
        
        # Exceeds maximum (should fail validation)
        with pytest.raises(ValueError):
            SessionEntity(
                title="TOO LARGE PROMPT",
                initial_prompt="A" * 10001
            )
    
    def test_concurrent_state_transitions(self):
        """Test behavior with concurrent state transitions"""
        session = SessionEntityFactory(status=SessionStatus.PENDING)
        
        # Simulate concurrent transition attempts
        def attempt_transition(target_status):
            try:
                session.transition_to(target_status)
                return True
            except InvalidSessionTransition:
                return False
        
        # First transition should succeed
        assert attempt_transition(SessionStatus.QUEUED) is True
        assert session.status == SessionStatus.QUEUED
        
        # Second concurrent attempt to different state should fail
        assert attempt_transition(SessionStatus.RUNNING) is False
        assert session.status == SessionStatus.QUEUED  # Unchanged
    
    def test_metrics_integration(self):
        """Test integration with execution metrics"""
        session = SessionEntityFactory()
        
        # Start timing updates metrics
        session.start_execution()
        assert session.metrics.started_at is not None
        assert session.metrics.queue_duration_seconds is not None
        
        # Checkpoint updates metrics
        initial_checkpoint_count = session.metrics.checkpoint_count
        session.add_checkpoint({"step": "test"})
        assert session.metrics.checkpoint_count == initial_checkpoint_count + 1
        
        # Completion updates metrics
        result = {"status": "success"}
        session.complete_with_result(result)
        assert session.metrics.completed_at is not None
        assert session.metrics.result == result
EOF

#### **1.4 Infrastructure Setup & Configuration**

```bash
# Create PostgreSQL database configuration with industrial resilience
cat > orchestrator/src/industrial_orchestrator/infrastructure/config/database.py << 'EOF'
"""
INDUSTRIAL DATABASE CONFIGURATION
PostgreSQL configuration with connection pooling, retry logic, and resilience patterns.
"""

import os
import asyncio
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, DateTime, event

from pydantic_settings import BaseSettings, SettingsConfigDict

# Declarative base for all models
Base = declarative_base()


class DatabaseSettings(BaseSettings):
    """Industrial database configuration settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DB_",
        case_sensitive=False
    )
    
    # Connection settings
    host: str = "localhost"
    port: int = 5432
    name: str = "orchestration"
    user: str = "cybernetics"
    password: str = "industrial_secure_001"
    
    # Connection pooling
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 1800  # Recycle connections every 30 minutes
    
    # SSL/TLS
    ssl_mode: str = "prefer"
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_root_cert: Optional[str] = None
    
    # Performance
    statement_cache_size: int = 1000
    echo: bool = False
    echo_pool: bool = False
    
    # Resilience
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    
    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string"""
        ssl_params = ""
        if self.ssl_mode != "disable":
            ssl_params = f"&sslmode={self.ssl_mode}"
            if self.ssl_cert:
                ssl_params += f"&sslcert={self.ssl_cert}"
            if self.ssl_key:
                ssl_params += f"&sslkey={self.ssl_key}"
            if self.ssl_root_cert:
                ssl_params += f"&sslrootcert={self.ssl_root_cert}"
        
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
            f"?async_fallback=True{ssl_params}"
        )


class TimestampMixin:
    """Industrial timestamp mixin for all models"""
    
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="UTC timestamp of creation"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="UTC timestamp of last update"
    )
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp of soft deletion"
    )


class DatabaseManager:
    """
    Industrial-grade database manager
    
    Features:
    1. Connection pooling with monitoring
    2. Automatic retry with exponential backoff
    3. Connection health checking
    4. Transaction management with savepoints
    5. Query logging and performance tracking
    """
    
    def __init__(self, settings: DatabaseSettings):
        self.settings = settings
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
        self._connection_count = 0
        self._failed_connections = 0
        
    async def initialize(self) -> None:
        """Initialize database connection pool"""
        if self._engine is not None:
            return
        
        engine_args: Dict[str, Any] = {
            "poolclass": AsyncAdaptedQueuePool,
            "pool_size": self.settings.pool_size,
            "max_overflow": self.settings.max_overflow,
            "pool_timeout": self.settings.pool_timeout,
            "pool_recycle": self.settings.pool_recycle,
            "echo": self.settings.echo,
            "echo_pool": self.settings.echo_pool,
            "future": True,
        }
        
        # Create engine with retry logic
        for attempt in range(self.settings.max_retries):
            try:
                self._engine = create_async_engine(
                    self.settings.connection_string,
                    **engine_args
                )
                
                # Add event listeners for monitoring
                self._setup_event_listeners()
                
                # Test connection
                async with self._engine.connect() as conn:
                    await conn.execute("SELECT 1")
                
                print(f"Database connection established (attempt {attempt + 1})")
                break
                
            except Exception as e:
                self._failed_connections += 1
                if attempt == self.settings.max_retries - 1:
                    raise ConnectionError(
                        f"Failed to connect to database after {self.settings.max_retries} attempts: {e}"
                    )
                
                delay = self.settings.retry_delay * (self.settings.retry_backoff ** attempt)
                print(f"Database connection failed (attempt {attempt + 1}), retrying in {delay:.1f}s: {e}")
                await asyncio.sleep(delay)
        
        # Create session factory
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    
    def _setup_event_listeners(self) -> None:
        """Setup SQLAlchemy event listeners for monitoring"""
        
        @event.listens_for(self._engine.sync_engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            self._connection_count += 1
            # Set statement timeout to prevent runaway queries
            cursor = dbapi_connection.cursor()
            cursor.execute("SET statement_timeout = 30000")  # 30 seconds
            cursor.close()
        
        @event.listens_for(self._engine.sync_engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            # Verify connection is still alive
            cursor = dbapi_connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
        
        @event.listens_for(self._engine.sync_engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            pass  # Connection returned to pool
        
        @event.listens_for(self._engine.sync_engine, "close")
        def on_close(dbapi_connection, connection_record):
            self._connection_count -= 1
    
    @property
    def engine(self) -> AsyncEngine:
        """Get database engine"""
        if self._engine is None:
            raise RuntimeError("Database manager not initialized")
        return self._engine
    
    @property
    def session_factory(self) -> async_sessionmaker:
        """Get session factory"""
        if self._session_factory is None:
            raise RuntimeError("Database manager not initialized")
        return self._session_factory
    
    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """
        Industrial-grade session context manager
        
        Features:
        1. Automatic transaction management
        2. Savepoint support for nested transactions
        3. Automatic rollback on exception
        4. Connection health verification
        """
        session: AsyncSession = self.session_factory()
        
        try:
            # Verify connection is alive
            await session.execute("SELECT 1")
            
            yield session
            await session.commit()
            
        except Exception as e:
            await session.rollback()
            raise
            
        finally:
            await session.close()
    
    @asynccontextmanager
    async def transaction(self, session: AsyncSession, savepoint_name: Optional[str] = None):
        """
        Industrial transaction manager with savepoint support
        
        Usage:
            async with db.get_session() as session:
                async with db.transaction(session, "sp1") as sp:
                    # Nested transaction work
                    pass
        """
        if savepoint_name:
            # Nested transaction using savepoint
            savepoint = await session.begin_nested()
            try:
                yield savepoint
                await session.commit()
            except Exception:
                await savepoint.rollback()
                raise
        else:
            # Top-level transaction
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive database health check"""
        try:
            async with self.get_session() as session:
                # Check basic connectivity
                result = await session.execute("SELECT 1 as healthy, version() as version")
                row = result.fetchone()
                
                # Check connection pool status
                pool_status = await session.execute("""
                    SELECT 
                        COUNT(*) as total_connections,
                        SUM(CASE WHEN state = 'active' THEN 1 ELSE 0 END) as active_connections,
                        SUM(CASE WHEN state = 'idle' THEN 1 ELSE 0 END) as idle_connections
                    FROM pg_stat_activity 
                    WHERE usename = current_user
                """)
                pool_row = pool_status.fetchone()
                
                # Check database size
                size_status = await session.execute("""
                    SELECT pg_database_size(current_database()) as size_bytes
                """)
                size_row = size_status.fetchone()
                
                return {
                    "status": "healthy",
                    "version": row.version if row else "unknown",
                    "connections": {
                        "total": pool_row.total_connections if pool_row else 0,
                        "active": pool_row.active_connections if pool_row else 0,
                        "idle": pool_row.idle_connections if pool_row else 0,
                        "pool_managed": self._connection_count,
                    },
                    "database_size_bytes": size_row.size_bytes if size_row else 0,
                    "failed_connection_attempts": self._failed_connections,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
    
    async def close(self) -> None:
        """Close all database connections"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._connection_count = 0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get database metrics for monitoring"""
        return {
            "connection_count": self._connection_count,
            "failed_connections": self._failed_connections,
            "pool_size": self.settings.pool_size,
            "max_overflow": self.settings.max_overflow,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


async def get_database_manager() -> DatabaseManager:
    """Get or create global database manager"""
    global _db_manager
    
    if _db_manager is None:
        settings = DatabaseSettings()
        _db_manager = DatabaseManager(settings)
        await _db_manager.initialize()
    
    return _db_manager


async def shutdown_database() -> None:
    """Shutdown database connections"""
    global _db_manager
    
    if _db_manager:
        await _db_manager.close()
        _db_manager = None
EOF

# Create Redis configuration with industrial resilience
cat > orchestrator/src/industrial_orchestrator/infrastructure/config/redis.py << 'EOF'
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
        
        args = [key, serialized]
        if expire_seconds:
            args.extend(["EX", expire_seconds])
        if nx:
            args.append("NX")
        if xx:
            args.append("XX")
        
        result = await self._execute_with_retry(RedisCommand.SET, *args)
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
            result = await self.set_json(
                lock_key,
                {
                    "value": lock_value,
                    "acquired_at": datetime.now(timezone.utc).isoformat(),
                    "timeout": timeout_seconds,
                },
                expire_seconds=timeout_seconds,
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
EOF

# Create OpenCode API client with industrial resilience
cat > orchestrator/src/industrial_orchestrator/infrastructure/adapters/opencode_client.py << 'EOF'
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
EOF

#### **1.5 Docker Compose Development Environment**

```bash
# Create comprehensive docker-compose for development
cat > docker-compose.dev.yml << 'EOF'
version: '3.8'

services:
  # Core Infrastructure
  postgres:
    image: postgres:15-alpine
    container_name: industrial-postgres
    environment:
      POSTGRES_DB: orchestration
      POSTGRES_USER: cybernetics
      POSTGRES_PASSWORD: industrial_secure_001
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=C"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infrastructure/postgres/init:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    networks:
      - industrial-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cybernetics"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    restart: unless-stopped
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  redis:
    image: redis:7-alpine
    container_name: industrial-redis
    command: >
      redis-server
      --appendonly yes
      --appendfsync everysec
      --save 900 1
      --save 300 10
      --save 60 10000
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
      - ./infrastructure/redis/redis.conf:/usr/local/etc/redis/redis.conf
    ports:
      - "6379:6379"
    networks:
      - industrial-network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  # OpenCode Server
  opencode-server:
    image: opencode/cli:latest
    container_name: industrial-opencode
    command: >
      serve
      --port 4096
      --hostname 0.0.0.0
      --cors "*"
    environment:
      OPENCODE_SERVER_PASSWORD: industrial_secure
      OPENCODE_AUTO_SHARE: "true"
      OPENCODE_EXPERIMENTAL_PLAN_MODE: "true"
      OPENCODE_CONFIG_CONTENT: '{"defaultModel": "anthropic/claude-sonnet-4.5"}'
    volumes:
      - opencode_data:/root/.opencode
      - ./opencode-projects:/projects
    ports:
      - "4096:4096"
    networks:
      - industrial-network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4096/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  # Orchestrator API
  orchestrator-api:
    build:
      context: ./orchestrator
      dockerfile: Dockerfile.dev
    container_name: industrial-orchestrator
    environment:
      # Database
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: orchestration
      DB_USER: cybernetics
      DB_PASSWORD: industrial_secure_001
      # Redis
      REDIS_HOST: redis
      REDIS_PORT: 6379
      # OpenCode
      OPENCODE_BASE_URL: http://opencode-server:4096
      OPENCODE_API_KEY: industrial_secure
      # Application
      NODE_ENV: development
      PYTHONPATH: /app
      LOG_LEVEL: INFO
      DEBUG: "true"
    volumes:
      - ./orchestrator:/app
      - ./orchestrator/.venv:/app/.venv
      - orchestrator_logs:/app/logs
    ports:
      - "8000:8000"
      - "5678:5678"  # Debug port
    networks:
      - industrial-network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      opencode-server:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped
    command: >
      bash -c "
        poetry install --no-root &&
        alembic upgrade head &&
        uvicorn src.industrial_orchestrator.presentation.api.main:app
          --host 0.0.0.0
          --port 8000
          --reload
          --reload-dir /app/src
          --log-level info
      "
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  # Monitoring Stack
  prometheus:
    image: prom/prometheus:latest
    container_name: industrial-prometheus
    volumes:
      - ./infrastructure/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - industrial-network
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: industrial-grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: industrial_secure
      GF_INSTALL_PLUGINS: grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./infrastructure/monitoring/grafana/provisioning:/etc/grafana/provisioning
    ports:
      - "3000:3000"
    networks:
      - industrial-network
    depends_on:
      - prometheus
    restart: unless-stopped

  # Dashboard (Next.js) - Will be added in Phase 2.3
  # dashboard:
  #   build:
  #     context: ./dashboard
  #     dockerfile: Dockerfile.dev
  #   container_name: industrial-dashboard
  #   environment:
  #     NEXT_PUBLIC_API_URL: http://orchestrator-api:8000
  #     NEXT_PUBLIC_WS_URL: ws://orchestrator-api:8000/ws
  #   volumes:
  #     - ./dashboard:/app
  #     - /app/node_modules
  #     - /app/.next
  #   ports:
  #     - "3001:3000"
  #   networks:
  #     - industrial-network
  #   depends_on:
  #     - orchestrator-api
  #   command: npm run dev
  #   restart: unless-stopped

  # Reverse Proxy (Optional)
  nginx:
    image: nginx:alpine
    container_name: industrial-proxy
    volumes:
      - ./infrastructure/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./infrastructure/nginx/conf.d:/etc/nginx/conf.d
    ports:
      - "80:80"
      - "443:443"
    networks:
      - industrial-network
    depends_on:
      - orchestrator-api
      # - dashboard
    restart: unless-stopped

networks:
  industrial-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1

volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PWD}/.data/postgres
  redis_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PWD}/.data/redis
  opencode_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PWD}/.data/opencode
  orchestrator_logs:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PWD}/.data/logs
  prometheus_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PWD}/.data/prometheus
  grafana_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PWD}/.data/grafana
EOF

# Create development Dockerfile for orchestrator
cat > orchestrator/Dockerfile.dev << 'EOF'
# Industrial Orchestrator - Development Image
FROM python:3.11-slim as development

# Industrial labeling
LABEL maintainer="Industrial Orchestrator Team"
LABEL version="1.0.0-dev"
LABEL description="Industrial-grade OpenCode Orchestrator"

# Set industrial environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Install system dependencies for industrial development
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    gcc \
    g++ \
    postgresql-client \
    redis-tools \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry for industrial dependency management
RUN pip install "poetry==$POETRY_VERSION"

# Set work directory with industrial structure
WORKDIR /app

# Copy industrial dependency files
COPY pyproject.toml poetry.lock* ./

# Configure Poetry for industrial development
RUN poetry config virtualenvs.create true \
    && poetry config virtualenvs.in-project true \
    && poetry install --no-root --with dev

# Copy industrial source code
COPY . .

# Create industrial directory structure
RUN mkdir -p /app/logs /app/data /app/cache

# Set industrial permissions
RUN chmod +x /app/scripts/*.sh 2>/dev/null || true

# Expose industrial ports
EXPOSE 8000  # API
EXPOSE 5678  # Debug

# Set industrial entrypoint
ENTRYPOINT ["poetry", "run"]

# Default industrial command
CMD ["uvicorn", "src.industrial_orchestrator.presentation.api.main:app", \
     "--host", "0.0.0.0", "--port", "8000", "--reload"]
EOF

#### **1.6 Initial Tests & Verification**

```bash
# Create comprehensive test suite for infrastructure
cat > tests/integration/infrastructure/test_database_integration.py << 'EOF'
"""
INDUSTRIAL DATABASE INTEGRATION TESTS
Test PostgreSQL integration with real database connection.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from src.industrial_orchestrator.infrastructure.config.database import (
    DatabaseManager,
    DatabaseSettings,
    get_database_manager,
    shutdown_database,
)


class TestDatabaseManagerIntegration:
    """Integration tests for DatabaseManager"""
    
    @pytest.fixture
    async def db_manager(self):
        """Create database manager for testing"""
        # Use test settings
        settings = DatabaseSettings(
            host="localhost",
            port=5432,
            name="test_orchestration",
            user="cybernetics",
            password="industrial_secure_001",
            pool_size=5,
            max_overflow=2,
            echo=False,
        )
        
        manager = DatabaseManager(settings)
        await manager.initialize()
        
        yield manager
        
        await manager.close()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_connection_pool_initialization(self, db_manager):
        """Test connection pool initialization"""
        assert db_manager.engine is not None
        assert db_manager.session_factory is not None
        
        # Verify connection works
        async with db_manager.get_session() as session:
            result = await session.execute("SELECT 1 as test_value")
            row = result.fetchone()
            assert row.test_value == 1
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_session_context_manager(self, db_manager):
        """Test session context manager functionality"""
        async with db_manager.get_session() as session:
            # Should be able to execute queries
            result = await session.execute("SELECT version()")
            version = result.scalar()
            assert "PostgreSQL" in version
            
            # Session should commit automatically on success
            await session.execute("CREATE TEMPORARY TABLE test (id SERIAL PRIMARY KEY)")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_transaction_management(self, db_manager):
        """Test transaction management with savepoints"""
        async with db_manager.get_session() as session:
            # Create test table
            await session.execute("""
                CREATE TEMPORARY TABLE transaction_test (
                    id SERIAL PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # Start transaction
            async with db_manager.transaction(session):
                await session.execute(
                    "INSERT INTO transaction_test (value) VALUES (:value)",
                    {"value": "test1"}
                )
            
            # Verify commit
            result = await session.execute("SELECT COUNT(*) FROM transaction_test")
            count = result.scalar()
            assert count == 1
            
            # Test nested transaction with savepoint
            async with db_manager.transaction(session, "sp1"):
                await session.execute(
                    "INSERT INTO transaction_test (value) VALUES (:value)",
                    {"value": "test2"}
                )
                
                # Rollback savepoint
                raise Exception("Test rollback")
            
            # Verify savepoint rollback
            result = await session.execute("SELECT COUNT(*) FROM transaction_test")
            count = result.scalar()
            assert count == 1  # Only first insert persisted
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_check(self, db_manager):
        """Test database health check"""
        health = await db_manager.health_check()
        
        assert "status" in health
        assert "version" in health
        assert "connections" in health
        assert "database_size_bytes" in health
        
        if health["status"] == "healthy":
            assert "PostgreSQL" in health["version"]
            assert health["connections"]["pool_managed"] >= 0
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_connection_retry_logic(self):
        """Test connection retry logic with invalid host"""
        settings = DatabaseSettings(
            host="invalid_host",
            port=5432,
            name="nonexistent",
            user="invalid",
            password="wrong",
            max_retries=2,
            retry_delay=0.1,
        )
        
        manager = DatabaseManager(settings)
        
        # Should fail after retries
        with pytest.raises(ConnectionError):
            await manager.initialize()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, db_manager):
        """Test concurrent session usage"""
        async def use_session(session_id: int):
            async with db_manager.get_session() as session:
                await session.execute("SELECT pg_sleep(0.1)")
                return session_id
        
        # Create multiple concurrent sessions
        tasks = [use_session(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert set(results) == set(range(10))
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_metrics_collection(self, db_manager):
        """Test metrics collection"""
        metrics = db_manager.get_metrics()
        
        assert "connection_count" in metrics
        assert "failed_connections" in metrics
        assert "pool_size" in metrics
        assert "timestamp" in metrics


class TestGlobalDatabaseFunctions:
    """Test global database functions"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_database_manager(self):
        """Test global database manager singleton"""
        manager1 = await get_database_manager()
        manager2 = await get_database_manager()
        
        assert manager1 is manager2  # Should be same instance
        
        await shutdown_database()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_shutdown_database(self):
        """Test database shutdown"""
        manager = await get_database_manager()
        
        # Verify manager exists
        assert manager is not None
        
        # Shutdown
        await shutdown_database()
        
        # Verify manager is cleared
        with pytest.raises(RuntimeError):
            await get_database_manager()
EOF

# Create test for Redis integration
cat > tests/integration/infrastructure/test_redis_integration.py << 'EOF'
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
EOF

### **Progress Report: DAY 1-2 COMPLETED**

✅ **Project Structure Established**  
✅ **Domain Layer Implemented**  
✅ **Value Objects with Industrial Precision**  
✅ **TDD Setup with Factory Pattern**  
✅ **Infrastructure Layer Foundations**  
✅ **Docker Development Environment**  
✅ **Comprehensive Test Suite Started**

**Key Industrial Design Decisions Applied:**

1. **Hexagonal Architecture**: Clear separation of concerns with ports & adapters
2. **Immutable Core Entities**: Session entities with validated state transitions  
3. **Industrial Resilience Patterns**: Circuit breakers, retry logic, connection pooling
4. **Anti-Generic Naming**: Rejected generic patterns, enforced industrial terminology
5. **Comprehensive Error Hierarchy**: Domain-specific exceptions with recovery paths

**Next Steps (Day 3-4):**  
- Complete PostgreSQL repository implementations  
- Implement Redis-based distributed locking  
- Create OpenCode API adapter with resilience  
- Set up Alembic database migrations  
- Implement session persistence layer

---

## **VALIDATION CHECKPOINT**

**Before proceeding to Day 3-4, please verify:**

1. **Architecture Validation**
   - [ ] Hexagonal architecture approach approved?
   - [ ] Domain entity design aligns with industrial requirements?
   - [ ] Value object precision meets standards?

2. **Technical Implementation**
   - [ ] Database/Redis configuration patterns acceptable?
   - [ ] Error handling strategy sufficient?
   - [ ] Test coverage approach meets TDD standards?

3. **Development Environment**
   - [ ] Docker setup meets development needs?
   - [ ] Environment configuration approach approved?
   - [ ] Monitoring infrastructure setup sufficient?

**Please provide explicit confirmation or adjustments needed before proceeding with session persistence and repository implementations.**

