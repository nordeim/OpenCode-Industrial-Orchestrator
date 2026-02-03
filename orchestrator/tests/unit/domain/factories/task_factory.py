"""
INDUSTRIAL TASK TEST FACTORY
Generates realistic task test data with decomposition and dependencies.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

import factory
from factory import LazyFunction, LazyAttribute, SubFactory

from src.industrial_orchestrator.domain.entities.task import (
    TaskEntity,
    TaskStatus,
    TaskPriority,
    TaskComplexityLevel,
    TaskDependencyType,
    TaskEstimate,
)
from src.industrial_orchestrator.domain.entities.agent import AgentCapability


class TaskEstimateFactory(factory.Factory):
    """Factory for TaskEstimate"""

    class Meta:
        model = TaskEstimate

    optimistic_hours = factory.Faker('pyfloat', min_value=0.5, max_value=2.0)
    likely_hours = factory.Faker('pyfloat', min_value=2.0, max_value=6.0)
    pessimistic_hours = factory.Faker('pyfloat', min_value=6.0, max_value=12.0)

    estimated_tokens = factory.Faker('random_int', min=1000, max=10000)
    estimated_cost_usd = factory.Faker('pyfloat', min_value=0.05, max_value=1.0)
    required_capabilities = [AgentCapability.CODE_GENERATION]

    estimate_confidence = factory.Faker('pyfloat', min_value=0.5, max_value=0.9)
    last_estimated_at = LazyFunction(lambda: datetime.now(timezone.utc))
    estimation_source = "manual"


class TaskEntityFactory(factory.Factory):
    """Industrial-grade factory for TaskEntity"""

    class Meta:
        model = TaskEntity

    # Identity
    id = LazyFunction(uuid4)
    session_id = LazyFunction(uuid4)
    parent_task_id = None

    # Task identity - must start with action verb
    title = factory.LazyFunction(
        lambda: f"Implement {factory.Faker('word').generate().capitalize()} component"
    )
    description = factory.Faker('sentence', nb_words=15)
    task_type = "implementation"

    # Execution state
    status = TaskStatus.PENDING
    status_updated_at = LazyFunction(lambda: datetime.now(timezone.utc))
    assigned_agent_id = None
    assigned_at = None

    # Planning
    priority = TaskPriority.NORMAL
    estimate = SubFactory(TaskEstimateFactory)

    # Dependencies
    dependencies = factory.List([])
    dependents = factory.List([])

    # Timestamps
    started_at = None
    completed_at = None
    failed_at = None

    # Results
    result = None
    error = None
    artifacts = factory.List([])

    # Metadata
    tags = factory.List(['test', 'factory'])
    metadata = factory.Dict({})
    created_at = LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = LazyFunction(lambda: datetime.now(timezone.utc))

    # Children
    child_tasks = factory.List([])

    class Params:
        """Factory variants"""

        # Ready to start
        ready = factory.Trait(
            status=TaskStatus.READY,
        )

        # Assigned to agent
        assigned = factory.Trait(
            status=TaskStatus.ASSIGNED,
            assigned_agent_id=LazyFunction(uuid4),
            assigned_at=LazyFunction(lambda: datetime.now(timezone.utc)),
        )

        # In progress
        in_progress = factory.Trait(
            status=TaskStatus.IN_PROGRESS,
            assigned_agent_id=LazyFunction(uuid4),
            assigned_at=LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(hours=1)),
            started_at=LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(minutes=30)),
        )

        # Completed
        completed = factory.Trait(
            status=TaskStatus.COMPLETED,
            assigned_agent_id=LazyFunction(uuid4),
            started_at=LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(hours=2)),
            completed_at=LazyFunction(lambda: datetime.now(timezone.utc)),
            result={'files_created': ['component.py'], 'tests_passed': 5},
        )

        # Failed
        failed = factory.Trait(
            status=TaskStatus.FAILED,
            assigned_agent_id=LazyFunction(uuid4),
            started_at=LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(hours=1)),
            failed_at=LazyFunction(lambda: datetime.now(timezone.utc)),
            error={'type': 'RuntimeError', 'message': 'Execution failed'},
        )

        # Complex task (needs decomposition)
        complex_task = factory.Trait(
            estimate=SubFactory(
                TaskEstimateFactory,
                optimistic_hours=6.0,
                likely_hours=10.0,
                pessimistic_hours=16.0,
            ),
        )

        # Trivial task
        trivial = factory.Trait(
            estimate=SubFactory(
                TaskEstimateFactory,
                optimistic_hours=0.1,
                likely_hours=0.15,
                pessimistic_hours=0.2,
            ),
        )


def create_task_with_subtasks(
    depth: int = 2,
    children_per_level: int = 2,
) -> TaskEntity:
    """Create task with subtask hierarchy"""
    root = TaskEntityFactory(complex_task=True)

    if depth > 0:
        for i in range(children_per_level):
            child = create_task_with_subtasks(depth - 1, children_per_level)
            child.parent_task_id = root.id
            root.child_tasks.append(child)

    return root


def create_task_chain(length: int = 3) -> List[TaskEntity]:
    """Create chain of dependent tasks"""
    tasks = []
    session_id = uuid4()

    for i in range(length):
        task = TaskEntityFactory(
            session_id=session_id,
            title=f"Implement step {i + 1} of pipeline",
        )

        # Add dependency on previous task
        if tasks:
            task.add_dependency(
                tasks[-1].id,
                dependency_type=TaskDependencyType.FINISH_TO_START,
                description=f"Depends on step {i}",
            )

        tasks.append(task)

    return tasks
