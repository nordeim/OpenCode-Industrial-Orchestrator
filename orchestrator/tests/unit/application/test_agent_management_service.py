"""
TEST AGENT MANAGEMENT SERVICE
Comprehensive unit tests for AgentManagementService business logic.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from dataclasses import dataclass

from src.industrial_orchestrator.application.services.agent_management_service import (
    AgentManagementService,
    TaskExecutionResult,
    AgentPerformanceMetrics,
    RebalanceResult,
    RouteTaskResult,
)
from src.industrial_orchestrator.domain.entities.registry import (
    RegisteredAgent,
    AgentCapability,
    AgentPerformanceTier,
    AgentLoadLevel,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_agent_repo():
    """Create mock agent repository."""
    repo = AsyncMock()
    repo.register = AsyncMock()
    repo.deregister = AsyncMock(return_value=True)
    repo.get_by_id = AsyncMock(return_value=None)
    repo.find_by_capabilities = AsyncMock(return_value=[])
    repo.find_available = AsyncMock(return_value=[])
    repo.update_heartbeat = AsyncMock(return_value=True)
    repo.update_performance_metrics = AsyncMock(return_value=True)
    repo.cleanup_stale_agents = AsyncMock(return_value=0)
    repo.get_agent_stats = AsyncMock(return_value={"total": 0})
    return repo


@pytest.fixture
def mock_lock_manager():
    """Create mock distributed lock."""
    lock = MagicMock()
    lock.acquire = MagicMock(return_value=True)
    lock.release = MagicMock(return_value=True)
    return lock


@pytest.fixture
def agent_service(mock_agent_repo, mock_lock_manager):
    """Create AgentManagementService with mock dependencies."""
    return AgentManagementService(
        agent_repository=mock_agent_repo,
        lock_manager=mock_lock_manager,
    )


@pytest.fixture
def sample_registered_agent():
    """Create sample registered agent."""
    return RegisteredAgent(
        id=uuid4(),
        name="AGENT-TEST-001",
        agent_type="IMPLEMENTATION",
        capabilities=[AgentCapability.CODE_GENERATION, AgentCapability.TESTING],
        max_concurrent_capacity=5,
        current_load=0,
        performance_tier=AgentPerformanceTier.STANDARD,
        load_level=AgentLoadLevel.LOW,
        preferred_technologies=["python", "typescript"],
        registered_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def task_execution_result_success():
    """Create successful task execution result."""
    return TaskExecutionResult(
        success=True,
        partial_success=False,
        quality_score=0.95,
        execution_time_seconds=120.0,
        tokens_used=2500,
        cost_usd=0.05,
    )


@pytest.fixture
def task_execution_result_failure():
    """Create failed task execution result."""
    return TaskExecutionResult(
        success=False,
        partial_success=False,
        quality_score=0.0,
        execution_time_seconds=30.0,
        tokens_used=500,
        error_message="Task failed due to timeout",
    )


# ============================================================================
# Test Agent Registration
# ============================================================================

class TestAgentRegistration:
    """Test agent registration use cases."""

    @pytest.mark.asyncio
    async def test_register_agent_success(self, agent_service, mock_agent_repo):
        """Test successful agent registration."""
        agent_data = {
            "name": "AGENT-NEW-001",
            "agent_type": "IMPLEMENTATION",
            "capabilities": [AgentCapability.CODE_GENERATION],
            "max_concurrent_capacity": 5,
        }
        
        mock_agent_repo.register.return_value = MagicMock(
            id=uuid4(),
            name=agent_data["name"],
        )
        
        result = await agent_service.register_agent(**agent_data)
        
        assert result is not None
        mock_agent_repo.register.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_agent_with_technologies(self, agent_service, mock_agent_repo):
        """Test agent registration with preferred technologies."""
        mock_agent_repo.register.return_value = MagicMock(id=uuid4())
        
        result = await agent_service.register_agent(
            name="AGENT-TECH-001",
            agent_type="SPECIALIST",
            capabilities=[AgentCapability.CODE_GENERATION],
            preferred_technologies=["rust", "go", "python"],
        )
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_deregister_agent_success(self, agent_service, mock_agent_repo, sample_registered_agent):
        """Test successful agent deregistration."""
        agent_id = sample_registered_agent.id
        mock_agent_repo.get_by_id.return_value = sample_registered_agent
        mock_agent_repo.deregister.return_value = True
        
        result = await agent_service.deregister_agent(agent_id, graceful=False)
        
        assert result is True
        mock_agent_repo.deregister.assert_called_once_with(agent_id)

    @pytest.mark.asyncio
    async def test_deregister_nonexistent_agent(self, agent_service, mock_agent_repo):
        """Test deregistering agent that doesn't exist."""
        agent_id = uuid4()
        mock_agent_repo.get_by_id.return_value = None
        mock_agent_repo.deregister.return_value = False
        
        result = await agent_service.deregister_agent(agent_id)
        
        assert result is False


# ============================================================================
# Test Task Routing
# ============================================================================

class TestTaskRouting:
    """Test capability-based task routing."""

    @pytest.mark.asyncio
    async def test_route_task_to_capable_agent(self, agent_service, mock_agent_repo, sample_registered_agent):
        """Test routing task to agent with required capabilities."""
        required_caps = [AgentCapability.CODE_GENERATION]
        mock_agent_repo.find_by_capabilities.return_value = [sample_registered_agent]
        
        result = await agent_service.route_task(
            required_capabilities=required_caps,
        )
        
        assert result is not None
        assert isinstance(result, RouteTaskResult)
        assert result.selected_agent.id == sample_registered_agent.id

    @pytest.mark.asyncio
    async def test_route_task_no_capable_agents(self, agent_service, mock_agent_repo):
        """Test routing when no agents have required capabilities."""
        mock_agent_repo.find_by_capabilities.return_value = []
        
        result = await agent_service.route_task(
            required_capabilities=[AgentCapability.SECURITY_AUDIT],
        )
        
        assert result is None

    @pytest.mark.asyncio
    async def test_route_task_prefers_higher_tier(self, agent_service, mock_agent_repo, sample_registered_agent):
        """Test that higher performance tier agents are preferred."""
        standard_agent = sample_registered_agent
        standard_agent.performance_tier = AgentPerformanceTier.STANDARD
        
        premium_agent = RegisteredAgent(
            id=uuid4(),
            name="AGENT-PREMIUM-001",
            agent_type="IMPLEMENTATION",
            capabilities=[AgentCapability.CODE_GENERATION],
            max_concurrent_capacity=10,
            performance_tier=AgentPerformanceTier.PREMIUM,
            load_level=AgentLoadLevel.LOW,
            registered_at=datetime.now(timezone.utc),
        )
        
        mock_agent_repo.find_by_capabilities.return_value = [standard_agent, premium_agent]
        
        result = await agent_service.route_task(
            required_capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        assert result is not None
        # Premium agent should be selected due to higher tier
        assert result.selected_agent.performance_tier == AgentPerformanceTier.PREMIUM

    @pytest.mark.asyncio
    async def test_route_task_avoids_overloaded(self, agent_service, mock_agent_repo, sample_registered_agent):
        """Test that overloaded agents are avoided."""
        overloaded_agent = sample_registered_agent
        overloaded_agent.load_level = AgentLoadLevel.OVERLOADED
        
        available_agent = RegisteredAgent(
            id=uuid4(),
            name="AGENT-AVAIL-001",
            agent_type="IMPLEMENTATION",
            capabilities=[AgentCapability.CODE_GENERATION],
            max_concurrent_capacity=5,
            performance_tier=AgentPerformanceTier.STANDARD,
            load_level=AgentLoadLevel.LOW,
            registered_at=datetime.now(timezone.utc),
        )
        
        mock_agent_repo.find_by_capabilities.return_value = [overloaded_agent, available_agent]
        
        result = await agent_service.route_task(
            required_capabilities=[AgentCapability.CODE_GENERATION],
        )
        
        assert result is not None
        # Available agent should be selected, not overloaded
        assert result.selected_agent.load_level != AgentLoadLevel.OVERLOADED

    @pytest.mark.asyncio
    async def test_route_task_with_preferred_agent_type(self, agent_service, mock_agent_repo):
        """Test routing with preferred agent type."""
        impl_agent = RegisteredAgent(
            id=uuid4(),
            name="AGENT-IMPL-001",
            agent_type="IMPLEMENTATION",
            capabilities=[AgentCapability.CODE_GENERATION],
            max_concurrent_capacity=5,
            performance_tier=AgentPerformanceTier.STANDARD,
            load_level=AgentLoadLevel.LOW,
            registered_at=datetime.now(timezone.utc),
        )
        
        debug_agent = RegisteredAgent(
            id=uuid4(),
            name="AGENT-DEBUG-001",
            agent_type="DEBUGGER",
            capabilities=[AgentCapability.CODE_GENERATION],
            max_concurrent_capacity=5,
            performance_tier=AgentPerformanceTier.STANDARD,
            load_level=AgentLoadLevel.LOW,
            registered_at=datetime.now(timezone.utc),
        )
        
        mock_agent_repo.find_by_capabilities.return_value = [impl_agent, debug_agent]
        
        result = await agent_service.route_task(
            required_capabilities=[AgentCapability.CODE_GENERATION],
            preferred_agent_type="DEBUGGER",
        )
        
        assert result is not None
        # Preferred agent type should be prioritized
        assert result.selected_agent.agent_type == "DEBUGGER"


# ============================================================================
# Test Performance Tracking
# ============================================================================

class TestPerformanceTracking:
    """Test agent performance metrics updates."""

    @pytest.mark.asyncio
    async def test_update_performance_on_success(
        self, agent_service, mock_agent_repo, 
        sample_registered_agent, task_execution_result_success
    ):
        """Test performance update after successful task."""
        agent_id = sample_registered_agent.id
        mock_agent_repo.get_by_id.return_value = sample_registered_agent
        
        await agent_service.update_agent_performance(
            agent_id,
            task_execution_result_success,
        )
        
        mock_agent_repo.update_performance_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_performance_on_failure(
        self, agent_service, mock_agent_repo,
        sample_registered_agent, task_execution_result_failure
    ):
        """Test performance update after failed task."""
        agent_id = sample_registered_agent.id
        mock_agent_repo.get_by_id.return_value = sample_registered_agent
        
        await agent_service.update_agent_performance(
            agent_id,
            task_execution_result_failure,
        )
        
        mock_agent_repo.update_performance_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_agent_summary(self, agent_service, mock_agent_repo, sample_registered_agent):
        """Test getting agent performance summary."""
        agent_id = sample_registered_agent.id
        mock_agent_repo.get_by_id.return_value = sample_registered_agent
        
        result = await agent_service.get_agent_summary(agent_id)
        
        assert result is not None
        assert "agent_id" in result

    @pytest.mark.asyncio
    async def test_get_summary_nonexistent_agent(self, agent_service, mock_agent_repo):
        """Test getting summary for nonexistent agent."""
        agent_id = uuid4()
        mock_agent_repo.get_by_id.return_value = None
        
        result = await agent_service.get_agent_summary(agent_id)
        
        assert result is None


# ============================================================================
# Test Workload Rebalancing
# ============================================================================

class TestWorkloadRebalancing:
    """Test workload distribution across agents."""

    @pytest.mark.asyncio
    async def test_rebalance_workload(self, agent_service, mock_agent_repo):
        """Test workload rebalancing operation."""
        mock_agent_repo.find_available.return_value = []
        
        result = await agent_service.rebalance_workload()
        
        assert result is not None
        assert isinstance(result, RebalanceResult)

    @pytest.mark.asyncio
    async def test_rebalance_with_no_agents(self, agent_service, mock_agent_repo):
        """Test rebalancing when no agents available."""
        mock_agent_repo.find_available.return_value = []
        
        result = await agent_service.rebalance_workload()
        
        assert result.tasks_rebalanced == 0


# ============================================================================
# Test Agent Health
# ============================================================================

class TestAgentHealth:
    """Test agent health monitoring."""

    @pytest.mark.asyncio
    async def test_process_heartbeat(self, agent_service, mock_agent_repo, sample_registered_agent):
        """Test processing agent heartbeat."""
        agent_id = sample_registered_agent.id
        mock_agent_repo.get_by_id.return_value = sample_registered_agent
        
        result = await agent_service.heartbeat(agent_id)
        
        assert result is True
        mock_agent_repo.update_heartbeat.assert_called_once_with(agent_id)

    @pytest.mark.asyncio
    async def test_heartbeat_nonexistent_agent(self, agent_service, mock_agent_repo):
        """Test heartbeat for nonexistent agent."""
        agent_id = uuid4()
        mock_agent_repo.get_by_id.return_value = None
        mock_agent_repo.update_heartbeat.return_value = False
        
        result = await agent_service.heartbeat(agent_id)
        
        assert result is False


# ============================================================================
# Test Performance Metrics Dataclass
# ============================================================================

class TestAgentPerformanceMetricsDataclass:
    """Test AgentPerformanceMetrics dataclass."""

    def test_success_rate_calculation(self):
        """Test success rate property calculation."""
        metrics = AgentPerformanceMetrics(
            total_tasks=100,
            successful_tasks=85,
            failed_tasks=10,
            partial_successes=5,
        )
        
        assert metrics.success_rate == 0.85

    def test_success_rate_with_zero_tasks(self):
        """Test success rate with no tasks."""
        metrics = AgentPerformanceMetrics(
            total_tasks=0,
            successful_tasks=0,
            failed_tasks=0,
        )
        
        assert metrics.success_rate == 0.0


# ============================================================================
# Test Task Execution Result Dataclass
# ============================================================================

class TestTaskExecutionResultDataclass:
    """Test TaskExecutionResult dataclass."""

    def test_successful_result(self):
        """Test creating successful task result."""
        result = TaskExecutionResult(
            success=True,
            quality_score=0.92,
            execution_time_seconds=45.5,
            tokens_used=1500,
        )
        
        assert result.success is True
        assert result.quality_score == 0.92

    def test_failed_result_with_error(self):
        """Test creating failed task result with error message."""
        result = TaskExecutionResult(
            success=False,
            error_message="Compilation failed",
        )
        
        assert result.success is False
        assert result.error_message == "Compilation failed"

    def test_partial_success_result(self):
        """Test partial success result."""
        result = TaskExecutionResult(
            success=False,
            partial_success=True,
            quality_score=0.6,
        )
        
        assert result.success is False
        assert result.partial_success is True
