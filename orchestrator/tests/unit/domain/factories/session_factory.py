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
import random

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
        from faker import Faker
        fake = Faker()
        if extracted is not None:
            self.warnings = extracted
        elif fake.boolean(chance_of_getting_true=30):
            num_warnings = fake.random_int(min=1, max=3)
            self.warnings = [{
                'type': fake.random_element(elements=['performance', 'resource', 'quality']),
                'message': fake.sentence(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            } for _ in range(num_warnings)]


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
    model_identifier = factory.LazyAttribute(lambda o: next(iter(o.agent_config.values()))['model'])
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
        from faker import Faker
        fake = Faker()
        if extracted is not None:
            self.checkpoints = extracted
        elif self.status.is_active():
            # Add checkpoints for active sessions
            checkpoint_count = fake.random_int(min=1, max=5)
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
        rand = random.random()  # Use standard random for status distribution
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
