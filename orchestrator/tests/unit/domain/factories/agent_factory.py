"""
INDUSTRIAL AGENT TEST FACTORY
Generates realistic agent test data with performance and load variations.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from uuid import uuid4

import factory
from factory import LazyFunction, LazyAttribute, SubFactory
from faker import Faker

fake = Faker()

from src.industrial_orchestrator.domain.entities.agent import (
    AgentEntity,
    AgentType,
    AgentCapability,
    AgentPerformanceTier,
    AgentLoadLevel,
    AgentPerformanceMetrics,
    AgentLoadMetrics,
)


class AgentPerformanceMetricsFactory(factory.Factory):
    """Factory for AgentPerformanceMetrics"""

    class Meta:
        model = AgentPerformanceMetrics

    total_tasks = factory.Faker('random_int', min=10, max=500)
    successful_tasks = LazyAttribute(lambda o: int(o.total_tasks * 0.85))
    failed_tasks = LazyAttribute(lambda o: int(o.total_tasks * 0.05))
    partially_successful_tasks = LazyAttribute(
        lambda o: o.total_tasks - o.successful_tasks - o.failed_tasks
    )

    average_quality_score = factory.Faker('pyfloat', min_value=0.7, max_value=0.95)
    code_coverage_impact = factory.Faker('pyfloat', min_value=0.5, max_value=0.9)
    security_improvement_score = factory.Faker('pyfloat', min_value=0.6, max_value=0.9)
    performance_improvement_score = factory.Faker('pyfloat', min_value=0.5, max_value=0.85)

    average_execution_time_seconds = factory.Faker('random_int', min=30, max=600)
    tokens_per_task = factory.Faker('random_int', min=500, max=5000)
    cost_per_task_usd = factory.Faker('pyfloat', min_value=0.01, max_value=0.5)

    capability_success_rates = factory.Dict({})
    technology_success_rates = factory.Dict({})

    success_rate_trend_30d = factory.Faker('pyfloat', min_value=-0.1, max_value=0.1)
    quality_trend_30d = factory.Faker('pyfloat', min_value=-0.05, max_value=0.1)
    efficiency_trend_30d = factory.Faker('pyfloat', min_value=-0.05, max_value=0.15)


class AgentLoadMetricsFactory(factory.Factory):
    """Factory for AgentLoadMetrics"""

    class Meta:
        model = AgentLoadMetrics

    current_concurrent_tasks = factory.Faker('random_int', min=0, max=3)
    max_concurrent_capacity = 5
    queue_length = factory.Faker('random_int', min=0, max=5)

    cpu_utilization = factory.Faker('pyfloat', min_value=0.1, max_value=0.7)
    memory_utilization = factory.Faker('pyfloat', min_value=0.2, max_value=0.6)
    network_utilization = factory.Faker('pyfloat', min_value=0.05, max_value=0.3)

    load_trend_1h = factory.Faker('pyfloat', min_value=-0.2, max_value=0.2)
    peak_load_today = LazyAttribute(lambda o: max(o.current_concurrent_tasks, 3))


class AgentEntityFactory(factory.Factory):
    """Industrial-grade factory for AgentEntity"""

    class Meta:
        model = AgentEntity

    # Identity
    id = LazyFunction(uuid4)
    name = factory.LazyFunction(
        lambda: f"Nexus-{fake.word().capitalize()}-{fake.pyint(min_value=100, max_value=999)}"
    )
    agent_type = AgentType.IMPLEMENTER
    description = factory.Faker('sentence', nb_words=10)

    # Capabilities (must match agent_type)
    primary_capabilities = LazyAttribute(
        lambda o: [
            AgentCapability.CODE_GENERATION,
            AgentCapability.TEST_GENERATION,
        ]
        if o.agent_type == AgentType.IMPLEMENTER
        else [AgentCapability.SYSTEM_DESIGN, AgentCapability.ARCHITECTURE_PLANNING]
    )
    secondary_capabilities = factory.List([])

    # Configuration
    model_identifier = "anthropic/claude-sonnet-4.5"
    temperature = 0.3
    max_tokens = 8000
    system_prompt_template = factory.LazyFunction(
        lambda: """You are an Industrial-grade coding agent specialized in generating 
        high-quality, production-ready code. You follow strict coding standards, 
        implement comprehensive error handling, and ensure all code is fully tested 
        before delivery. Your output must be industrial-grade and production-ready."""
    )

    # Performance and load
    performance = SubFactory(AgentPerformanceMetricsFactory)
    load = SubFactory(AgentLoadMetricsFactory)

    # Specialization
    preferred_technologies = factory.List(['python', 'typescript', 'rust'])
    avoided_technologies = factory.List([])
    complexity_preference = 'medium'

    # Operational state
    is_active = True
    last_active_at = LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(hours=1))
    maintenance_mode = False

    # Routing preferences
    preferred_session_types = factory.List([])
    max_task_duration_hours = 4.0
    min_quality_threshold = 0.7

    # Metadata
    version = "1.0.0"
    created_at = LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(days=30))
    updated_at = LazyFunction(lambda: datetime.now(timezone.utc))
    metadata = factory.Dict({})

    class Params:
        """Factory variants"""

        # Elite performer
        elite = factory.Trait(
            performance=SubFactory(
                AgentPerformanceMetricsFactory,
                total_tasks=500,
                successful_tasks=490,
                failed_tasks=5,
                partially_successful_tasks=5,
                average_quality_score=0.95,
            ),
            load=SubFactory(
                AgentLoadMetricsFactory,
                current_concurrent_tasks=2,
            ),
        )

        # Degraded agent
        degraded = factory.Trait(
            performance=SubFactory(
                AgentPerformanceMetricsFactory,
                total_tasks=100,
                successful_tasks=30,
                failed_tasks=50,
                partially_successful_tasks=20,
                average_quality_score=0.4,
            ),
        )

        # Overloaded agent
        overloaded = factory.Trait(
            load=SubFactory(
                AgentLoadMetricsFactory,
                current_concurrent_tasks=6,
                max_concurrent_capacity=5,
            ),
        )

        # Architect type
        architect = factory.Trait(
            agent_type=AgentType.ARCHITECT,
            primary_capabilities=[
                AgentCapability.SYSTEM_DESIGN,
                AgentCapability.ARCHITECTURE_PLANNING,
            ],
        )

        # Reviewer type
        reviewer = factory.Trait(
            agent_type=AgentType.REVIEWER,
            primary_capabilities=[
                AgentCapability.CODE_REVIEW,
                AgentCapability.SECURITY_AUDIT,
            ],
        )

        # Debugger type
        debugger = factory.Trait(
            agent_type=AgentType.DEBUGGER,
            primary_capabilities=[
                AgentCapability.DEBUGGING,
                AgentCapability.ROOT_CAUSE_ANALYSIS,
            ],
        )


def create_agent_pool(
    count: int = 5,
    type_distribution: Optional[Dict[AgentType, float]] = None,
) -> List[AgentEntity]:
    """Create pool of agents with type distribution"""
    if type_distribution is None:
        type_distribution = {
            AgentType.IMPLEMENTER: 0.4,
            AgentType.ARCHITECT: 0.2,
            AgentType.REVIEWER: 0.2,
            AgentType.DEBUGGER: 0.2,
        }

    agents = []
    for _ in range(count):
        rand = fake.pyfloat(min_value=0, max_value=1)
        cumulative = 0
        selected_type = AgentType.IMPLEMENTER

        for agent_type, probability in type_distribution.items():
            cumulative += probability
            if rand <= cumulative:
                selected_type = agent_type
                break

        if selected_type == AgentType.ARCHITECT:
            agents.append(AgentEntityFactory(architect=True))
        elif selected_type == AgentType.REVIEWER:
            agents.append(AgentEntityFactory(reviewer=True))
        elif selected_type == AgentType.DEBUGGER:
            agents.append(AgentEntityFactory(debugger=True))
        else:
            agents.append(AgentEntityFactory(agent_type=selected_type))

    return agents
