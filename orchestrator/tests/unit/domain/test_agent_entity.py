"""
INDUSTRIAL-GRADE AGENT ENTITY TESTS
Comprehensive TDD-style tests for agent capabilities, performance, and load.
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from src.industrial_orchestrator.domain.entities.agent import (
    AgentEntity,
    AgentType,
    AgentCapability,
    AgentPerformanceTier,
    AgentLoadLevel,
    AgentPerformanceMetrics,
    AgentLoadMetrics,
)
from src.industrial_orchestrator.domain.exceptions.agent_exceptions import (
    AgentCapabilityMismatchError,
    AgentOverloadedError,
)

from tests.unit.domain.factories.agent_factory import (
    AgentEntityFactory,
    AgentPerformanceMetricsFactory,
    AgentLoadMetricsFactory,
    create_agent_pool,
)


class TestAgentEntityCreation:
    """Test agent entity creation and validation"""

    def test_create_minimal_agent(self):
        """Test creating agent with minimal valid configuration"""
        agent = AgentEntityFactory()

        assert agent.id is not None
        assert agent.name is not None
        assert agent.agent_type == AgentType.IMPLEMENTER
        assert len(agent.primary_capabilities) > 0
        assert agent.is_active is True
        assert agent.performance is not None
        assert agent.load is not None

    def test_create_architect_agent(self):
        """Test creating architect-type agent"""
        agent = AgentEntityFactory(architect=True)

        assert agent.agent_type == AgentType.ARCHITECT
        assert AgentCapability.SYSTEM_DESIGN in agent.primary_capabilities
        assert AgentCapability.ARCHITECTURE_PLANNING in agent.primary_capabilities

    def test_create_reviewer_agent(self):
        """Test creating reviewer-type agent"""
        agent = AgentEntityFactory(reviewer=True)

        assert agent.agent_type == AgentType.REVIEWER
        assert AgentCapability.CODE_REVIEW in agent.primary_capabilities
        assert AgentCapability.SECURITY_AUDIT in agent.primary_capabilities

    @pytest.mark.parametrize("invalid_name", [
        "",
        "   ",
        "ai assistant test",
        "simple bot",
        "helper",
    ])
    def test_invalid_agent_names_rejected(self, invalid_name):
        """Test that generic/invalid names are rejected"""
        with pytest.raises(ValueError):
            AgentEntity(
                name=invalid_name,
                agent_type=AgentType.IMPLEMENTER,
                primary_capabilities=[AgentCapability.CODE_GENERATION],
                model_config="anthropic/claude-sonnet-4.5",
                system_prompt_template="A" * 100,
            )

    def test_agent_must_have_capabilities(self):
        """Test that agents must have at least one capability"""
        with pytest.raises(ValueError, match="at least one primary capability"):
            AgentEntity(
                name="Valid-Industrial-Agent",
                agent_type=AgentType.IMPLEMENTER,
                primary_capabilities=[],
                model_config="anthropic/claude-sonnet-4.5",
                system_prompt_template="A" * 100,
            )

    def test_capability_type_alignment(self):
        """Test that capabilities must align with agent type"""
        # Architect cannot have IMPLEMENTER capabilities as primary
        with pytest.raises(ValueError, match="not allowed for agent type"):
            AgentEntity(
                name="Invalid-Architect-Agent",
                agent_type=AgentType.ARCHITECT,
                primary_capabilities=[AgentCapability.CODE_GENERATION],  # Wrong!
                model_config="anthropic/claude-sonnet-4.5",
                system_prompt_template="A" * 100,
            )


class TestAgentPerformanceMetrics:
    """Test performance metrics calculation"""

    def test_success_rate_calculation(self):
        """Test overall success rate calculation"""
        metrics = AgentPerformanceMetrics(
            total_tasks=100,
            successful_tasks=80,
            failed_tasks=10,
            partially_successful_tasks=10,
        )

        # 80 + (10 * 0.5) = 85 / 100 = 0.85
        assert metrics.overall_success_rate == 0.85

    def test_complete_success_rate(self):
        """Test complete success rate (excluding partial)"""
        metrics = AgentPerformanceMetrics(
            total_tasks=100,
            successful_tasks=80,
            failed_tasks=10,
            partially_successful_tasks=10,
        )

        assert metrics.complete_success_rate == 0.8

    def test_success_rate_with_zero_tasks(self):
        """Test success rate returns 0 for zero tasks"""
        metrics = AgentPerformanceMetrics()

        assert metrics.overall_success_rate == 0.0
        assert metrics.complete_success_rate == 0.0

    @pytest.mark.parametrize("success_rate,quality,expected_tier", [
        (0.96, 0.92, AgentPerformanceTier.ELITE),
        (0.90, 0.80, AgentPerformanceTier.ADVANCED),
        (0.75, 0.70, AgentPerformanceTier.COMPETENT),
        (0.60, 0.60, AgentPerformanceTier.TRAINEE),
        (0.40, 0.40, AgentPerformanceTier.DEGRADED),
    ])
    def test_performance_tier_calculation(self, success_rate, quality, expected_tier):
        """Test performance tier based on metrics"""
        total = 100
        successful = int(total * success_rate)

        metrics = AgentPerformanceMetrics(
            total_tasks=total,
            successful_tasks=successful,
            failed_tasks=total - successful,
            average_quality_score=quality,
        )

        assert metrics.calculate_performance_tier() == expected_tier

    def test_record_task_result_success(self):
        """Test recording successful task result"""
        metrics = AgentPerformanceMetrics()

        metrics.record_task_result(
            success=True,
            quality_score=0.9,
            execution_time_seconds=120.0,
            tokens_used=1000,
            cost_usd=0.05,
        )

        assert metrics.total_tasks == 1
        assert metrics.successful_tasks == 1
        assert metrics.failed_tasks == 0
        assert metrics.average_quality_score == 0.9
        assert metrics.average_execution_time_seconds == 120.0

    def test_record_task_result_failure(self):
        """Test recording failed task result"""
        metrics = AgentPerformanceMetrics()

        metrics.record_task_result(success=False)

        assert metrics.total_tasks == 1
        assert metrics.successful_tasks == 0
        assert metrics.failed_tasks == 1

    def test_record_task_result_partial(self):
        """Test recording partial success"""
        metrics = AgentPerformanceMetrics()

        metrics.record_task_result(success=False, partial_success=True)

        assert metrics.total_tasks == 1
        assert metrics.partially_successful_tasks == 1


class TestAgentLoadMetrics:
    """Test load metrics and capacity"""

    def test_utilization_percentage(self):
        """Test utilization calculation"""
        load = AgentLoadMetrics(
            current_concurrent_tasks=3,
            max_concurrent_capacity=5,
        )

        assert load.utilization_percentage == 0.6

    @pytest.mark.parametrize("tasks,capacity,expected_level", [
        (0, 5, AgentLoadLevel.IDLE),
        (1, 5, AgentLoadLevel.IDLE),
        (2, 5, AgentLoadLevel.OPTIMAL),
        (3, 5, AgentLoadLevel.OPTIMAL),
        (4, 5, AgentLoadLevel.HIGH),
        (5, 5, AgentLoadLevel.CRITICAL),
        (6, 5, AgentLoadLevel.OVERLOADED),
    ])
    def test_load_level_classification(self, tasks, capacity, expected_level):
        """Test load level classification"""
        load = AgentLoadMetrics(
            current_concurrent_tasks=tasks,
            max_concurrent_capacity=capacity,
        )

        assert load.load_level == expected_level

    def test_can_accept_task_normal(self):
        """Test normal task acceptance"""
        load = AgentLoadMetrics(
            current_concurrent_tasks=2,
            max_concurrent_capacity=5,
        )

        assert load.can_accept_task() is True
        assert load.can_accept_task(estimated_complexity=2.0) is True

    def test_cannot_accept_when_overloaded(self):
        """Test rejection when overloaded"""
        load = AgentLoadMetrics(
            current_concurrent_tasks=6,
            max_concurrent_capacity=5,
        )

        assert load.can_accept_task() is False

    def test_cannot_accept_complex_when_critical(self):
        """Test complex task rejected at critical load"""
        load = AgentLoadMetrics(
            current_concurrent_tasks=5,
            max_concurrent_capacity=5,
        )

        # Critical load rejects complex tasks
        assert load.can_accept_task(estimated_complexity=3.0) is False

    def test_increment_decrement_load(self):
        """Test load increment and decrement"""
        load = AgentLoadMetrics(
            current_concurrent_tasks=2,
            max_concurrent_capacity=5,
        )

        load.increment_load(1.0)
        assert load.current_concurrent_tasks == 3

        load.decrement_load(1.0)
        assert load.current_concurrent_tasks == 2


class TestAgentCapabilities:
    """Test capability handling"""

    def test_all_capabilities(self):
        """Test combined primary and secondary capabilities"""
        agent = AgentEntityFactory()
        agent.secondary_capabilities = [AgentCapability.DOCUMENTATION]

        all_caps = agent.all_capabilities

        assert AgentCapability.CODE_GENERATION in all_caps
        assert AgentCapability.DOCUMENTATION in all_caps

    def test_has_capability_primary(self):
        """Test checking primary capability"""
        agent = AgentEntityFactory()

        assert agent.has_capability(AgentCapability.CODE_GENERATION) is True

    def test_has_capability_missing(self):
        """Test checking missing capability"""
        agent = AgentEntityFactory()

        assert agent.has_capability(AgentCapability.DEPLOYMENT) is False


class TestAgentTaskHandling:
    """Test task handling and suitability scoring"""

    def test_can_handle_task_success(self):
        """Test agent can handle matching task"""
        agent = AgentEntityFactory()

        result = agent.can_handle_task(
            required_capabilities=[AgentCapability.CODE_GENERATION],
            estimated_complexity=1.0,
        )

        assert result is True

    def test_cannot_handle_missing_capability(self):
        """Test rejection for missing capability"""
        agent = AgentEntityFactory()

        result = agent.can_handle_task(
            required_capabilities=[AgentCapability.DEPLOYMENT],  # Not an IMPLEMENTER cap
        )

        assert result is False

    def test_cannot_handle_when_inactive(self):
        """Test rejection when agent inactive"""
        agent = AgentEntityFactory()
        agent.is_active = False

        result = agent.can_handle_task(
            required_capabilities=[AgentCapability.CODE_GENERATION],
        )

        assert result is False

    def test_cannot_handle_when_maintenance(self):
        """Test rejection during maintenance"""
        agent = AgentEntityFactory()
        agent.maintenance_mode = True

        result = agent.can_handle_task(
            required_capabilities=[AgentCapability.CODE_GENERATION],
        )

        assert result is False

    def test_cannot_handle_when_degraded(self):
        """Test rejection when degraded"""
        agent = AgentEntityFactory(degraded=True)

        result = agent.can_handle_task(
            required_capabilities=[AgentCapability.CODE_GENERATION],
        )

        assert result is False

    def test_suitability_score_calculation(self):
        """Test suitability score is calculated"""
        agent = AgentEntityFactory(elite=True)

        score = agent.calculate_task_suitability_score(
            required_capabilities=[AgentCapability.CODE_GENERATION],
            estimated_complexity=1.0,
            technologies=['python'],
        )

        assert 0.0 < score <= 1.1  # Can exceed 1.0 due to tier multipliers

    def test_suitability_zero_when_cannot_handle(self):
        """Test zero score when cannot handle"""
        agent = AgentEntityFactory()
        agent.is_active = False

        score = agent.calculate_task_suitability_score(
            required_capabilities=[AgentCapability.CODE_GENERATION],
        )

        assert score == 0.0


class TestAgentTaskAcceptance:
    """Test accept_task and complete_task methods"""

    def test_accept_task_success(self):
        """Test successful task acceptance"""
        agent = AgentEntityFactory()
        initial_load = agent.load.current_concurrent_tasks

        agent.accept_task(estimated_complexity=1.0)

        assert agent.load.current_concurrent_tasks == initial_load + 1.0
        assert agent.last_active_at is not None

    def test_accept_task_raises_on_overload(self):
        """Test exception when overloaded"""
        agent = AgentEntityFactory(overloaded=True)

        with pytest.raises(AgentOverloadedError):
            agent.accept_task(estimated_complexity=1.0)

    def test_accept_task_raises_on_missing_capability(self):
        """Test exception when missing capability"""
        agent = AgentEntityFactory()

        with pytest.raises(AgentCapabilityMismatchError):
            agent.accept_task(
                required_capabilities=[AgentCapability.DEPLOYMENT],
            )

    def test_complete_task_updates_metrics(self):
        """Test completing task updates all metrics"""
        agent = AgentEntityFactory()
        agent.accept_task(estimated_complexity=1.0)
        initial_tasks = agent.performance.total_tasks

        agent.complete_task(
            success=True,
            quality_score=0.9,
            execution_time_seconds=100.0,
            estimated_complexity=1.0,
        )

        assert agent.performance.total_tasks == initial_tasks + 1
        assert agent.performance.successful_tasks >= 1


class TestAgentHealthStatus:
    """Test health status reporting"""

    def test_healthy_agent(self):
        """Test healthy agent has no issues"""
        agent = AgentEntityFactory(elite=True)

        health = agent.get_health_status()

        assert health['is_healthy'] is True
        assert len(health['issues']) == 0

    def test_degraded_performance_issue(self):
        """Test degraded performance flagged"""
        agent = AgentEntityFactory(degraded=True)

        health = agent.get_health_status()

        assert health['is_healthy'] is False
        assert any(i['type'] == 'performance_degradation' for i in health['issues'])

    def test_overloaded_issue(self):
        """Test overload flagged"""
        agent = AgentEntityFactory(overloaded=True)

        health = agent.get_health_status()

        assert health['is_healthy'] is False
        assert any(i['type'] == 'overloaded' for i in health['issues'])

    def test_inactive_warning(self):
        """Test inactivity warning"""
        agent = AgentEntityFactory()
        agent.last_active_at = datetime.now(timezone.utc) - timedelta(hours=48)

        health = agent.get_health_status()

        assert any(i['type'] == 'inactive' for i in health['issues'])


class TestAgentFactory:
    """Test factory integration"""

    def test_factory_creates_valid_agents(self):
        """Test factory produces valid entities"""
        agent = AgentEntityFactory()

        assert isinstance(agent, AgentEntity)
        assert agent.id is not None
        assert agent.name is not None

    def test_factory_variants(self):
        """Test factory variants produce correct types"""
        elite = AgentEntityFactory(elite=True)
        assert elite.performance.overall_success_rate >= 0.95

        degraded = AgentEntityFactory(degraded=True)
        assert degraded.performance_tier == AgentPerformanceTier.DEGRADED

        overloaded = AgentEntityFactory(overloaded=True)
        assert overloaded.load_level == AgentLoadLevel.OVERLOADED

    def test_create_agent_pool(self):
        """Test agent pool creation"""
        agents = create_agent_pool(10)

        assert len(agents) == 10
        assert all(isinstance(a, AgentEntity) for a in agents)

        # Check type distribution includes variety
        types = {a.agent_type for a in agents}
        assert len(types) >= 2
