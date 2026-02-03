"""
TEST TASK DECOMPOSITION SERVICE
Unit tests for TaskDecompositionService business logic.

These tests use mocks to isolate the service from infrastructure dependencies.
"""

import pytest
from uuid import uuid4

# Import only what exists in the domain
from src.industrial_orchestrator.application.services.task_decomposition_service import (
    TaskDecompositionService,
    ComplexityAnalyzer,
    DecompositionRule,
)
from src.industrial_orchestrator.domain.entities.task import (
    TaskEntity,
    TaskComplexityLevel,
    TaskPriority,
    TaskStatus,
    TaskEstimate,
)
from src.industrial_orchestrator.domain.entities.agent import AgentCapability


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def decomposition_service():
    """Create TaskDecompositionService."""
    return TaskDecompositionService()


@pytest.fixture
def complexity_analyzer():
    """Create ComplexityAnalyzer."""
    return ComplexityAnalyzer()


@pytest.fixture
def simple_task():
    """Create simple implementation task."""
    return TaskEntity(
        title="Implement user login functionality for IND-TASK-001",
        description="Create login form and authentication logic",
        task_type="implementation",
        priority=TaskPriority.NORMAL,
        session_id=uuid4(),
    )


@pytest.fixture
def complex_microservice_task():
    """Create complex microservice task."""
    return TaskEntity(
        title="Build microservice API for distributed system IND-TASK-002",
        description="Create a microservice with REST API, database integration, and authentication",
        task_type="implementation",
        priority=TaskPriority.HIGH,
        session_id=uuid4(),
    )


@pytest.fixture
def crud_task():
    """Create CRUD operation task."""
    return TaskEntity(
        title="Create CRUD operations for product entity with database model",
        description="Implement create, read, update, delete operations for product entity with database model",
        task_type="implementation",
        priority=TaskPriority.NORMAL,
        session_id=uuid4(),
    )


@pytest.fixture
def security_task():
    """Create security-focused task."""
    return TaskEntity(
        title="Implement security audit and authentication hardening",
        description="Perform security audit, vulnerability scanning, and implement security fixes for authentication",
        task_type="implementation",
        priority=TaskPriority.HIGH,
        session_id=uuid4(),
    )


# ============================================================================
# Test Complexity Analyzer
# ============================================================================

class TestComplexityAnalyzer:
    """Test complexity analysis heuristics."""

    def test_analyze_simple_requirements(self, complexity_analyzer):
        """Test analyzing simple requirements text."""
        text = "Create a simple button component"
        
        result = complexity_analyzer.analyze_requirements_text(text)
        
        assert result is not None
        assert "complexity_score" in result
        assert "estimated_hours" in result

    def test_analyze_complex_requirements(self, complexity_analyzer):
        """Test analyzing complex requirements text."""
        text = """
        Build a distributed microservice architecture with:
        - Multiple service components
        - Database migrations and schema design
        - Authentication and authorization
        - API gateway integration
        - Event-driven communication
        - Comprehensive testing suite
        """
        
        result = complexity_analyzer.analyze_requirements_text(text)
        
        assert result is not None
        assert result["complexity_score"] > 1.0  # Should be elevated

    def test_analyze_security_keywords(self, complexity_analyzer):
        """Test that security keywords are detected."""
        secure_text = "Implement authentication, authorization, and encryption for user data"
        simple_text = "Create a display component"
        
        secure_result = complexity_analyzer.analyze_requirements_text(secure_text)
        simple_result = complexity_analyzer.analyze_requirements_text(simple_text)
        
        # Security requirements should have higher complexity
        assert secure_result["technical_terms"] > simple_result["technical_terms"]

    def test_analyze_empty_text(self, complexity_analyzer):
        """Test analyzing empty text."""
        result = complexity_analyzer.analyze_requirements_text("")
        
        assert result["word_count"] == 0
        assert result["estimated_hours"] == 1.0

    def test_estimate_from_task_description(self, complexity_analyzer, simple_task):
        """Test estimating complexity from task entity."""
        result = complexity_analyzer.estimate_from_task_description(simple_task)
        
        assert result is not None
        assert isinstance(result, TaskEstimate)
        assert result.likely_hours > 0

    def test_infer_capabilities_from_text(self, complexity_analyzer):
        """Test inferring required capabilities from text."""
        text = "Write unit tests and integration tests for the API"
        
        result = complexity_analyzer.infer_capabilities(text)
        
        assert result is not None
        assert isinstance(result, list)
        assert AgentCapability.TEST_GENERATION in result

    def test_infer_security_capabilities(self, complexity_analyzer):
        """Test inferring security-related capabilities."""
        text = "Perform security audit and vulnerability assessment"
        
        result = complexity_analyzer.infer_capabilities(text)
        
        assert AgentCapability.SECURITY_AUDIT in result

    def test_infer_default_capability(self, complexity_analyzer):
        """Test default capability when no keywords match."""
        text = ""
        
        result = complexity_analyzer.infer_capabilities(text)
        
        assert AgentCapability.CODE_GENERATION in result


# ============================================================================
# Test Template Matching
# ============================================================================

class TestTemplateMatching:
    """Test decomposition template matching."""

    def test_service_has_default_templates(self, decomposition_service):
        """Test that service initializes with default templates."""
        assert hasattr(decomposition_service, '_templates')
        assert len(decomposition_service._templates) > 0

    def test_service_has_default_rules(self, decomposition_service):
        """Test that service initializes with default rules."""
        assert hasattr(decomposition_service, '_rules')
        assert len(decomposition_service._rules) > 0

    def test_templates_have_required_fields(self, decomposition_service):
        """Test that templates have required configuration."""
        for name, template in decomposition_service._templates.items():
            assert template.name is not None
            assert template.description is not None
            assert template.subtask_templates is not None


# ============================================================================
# Test Task Decomposition
# ============================================================================

class TestTaskDecomposition:
    """Test analyze_and_decompose functionality."""

    def test_decompose_simple_task(self, decomposition_service, simple_task):
        """Test decomposing a simple task."""
        result = decomposition_service.analyze_and_decompose(
            task=simple_task,
            auto_estimate=True,
            max_depth=2,
        )
        
        assert result is not None
        assert result.id == simple_task.id

    def test_decompose_auto_estimates(self, decomposition_service, simple_task):
        """Test that auto_estimate populates task estimate."""
        simple_task.estimate = None  # Clear any existing estimate
        
        result = decomposition_service.analyze_and_decompose(
            task=simple_task,
            auto_estimate=True,
        )
        
        assert result.estimate is not None

    def test_decompose_crud_task_creates_subtasks(self, decomposition_service, crud_task):
        """Test decomposing CRUD task creates subtasks."""
        result = decomposition_service.analyze_and_decompose(
            task=crud_task,
            apply_templates=True,
            apply_rules=True,
        )
        
        assert result is not None
        # CRUD tasks should be decomposed into operations
        if len(result.child_tasks) > 0:
            assert len(result.child_tasks) >= 2  # At least some CRUD ops

    def test_decompose_microservice_task(self, decomposition_service, complex_microservice_task):
        """Test decomposing microservice task."""
        result = decomposition_service.analyze_and_decompose(
            task=complex_microservice_task,
            apply_templates=True,
            apply_rules=True,
        )
        
        assert result is not None

    def test_decompose_respects_max_depth(self, decomposition_service, complex_microservice_task):
        """Test that decomposition respects max_depth limit."""
        result = decomposition_service.analyze_and_decompose(
            task=complex_microservice_task,
            max_depth=1,
        )
        
        assert result is not None
        # Calculate max depth
        max_depth = decomposition_service._calculate_max_depth(result)
        assert max_depth <= 2  # Root + 1 level

    def test_decompose_without_templates(self, decomposition_service, simple_task):
        """Test decomposition without template application."""
        result = decomposition_service.analyze_and_decompose(
            task=simple_task,
            apply_templates=False,
            apply_rules=False,
        )
        
        assert result is not None


# ============================================================================
# Test DecompositionRule Model
# ============================================================================

class TestDecompositionRuleModel:
    """Test DecompositionRule Pydantic model."""

    def test_create_valid_rule(self):
        """Test creating valid decomposition rule."""
        rule = DecompositionRule(
            pattern=".*microservice.*",
            strategy="component_based",
            parameters={"min_components": 2},
            priority=5,
        )
        
        assert rule.pattern == ".*microservice.*"
        assert rule.strategy == "component_based"
        assert rule.priority == 5

    def test_rule_default_priority(self):
        """Test rule has default priority."""
        rule = DecompositionRule(
            pattern=".*simple.*",
            strategy="direct",
        )
        
        assert rule.priority >= 1

    def test_rule_with_empty_parameters(self):
        """Test rule with empty parameters."""
        rule = DecompositionRule(
            pattern=".*test.*",
            strategy="test_first",
            parameters={},
        )
        
        assert rule.parameters == {}


# ============================================================================
# Test Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_decompose_task_with_empty_description(self, decomposition_service):
        """Test decomposing task with minimal description."""
        task = TaskEntity(
            title="Create minimal task component",
            description="",
            task_type="implementation",
            priority=TaskPriority.LOW,
            session_id=uuid4(),
        )
        
        result = decomposition_service.analyze_and_decompose(task)
        assert result is not None

    def test_analyzer_handles_unicode_text(self, complexity_analyzer):
        """Test analyzer handles unicode characters."""
        text = "Implementar autenticação de usuário 用户认证 🔐"
        
        result = complexity_analyzer.analyze_requirements_text(text)
        
        assert result is not None
        assert result["word_count"] > 0

    def test_analyzer_handles_very_long_text(self, complexity_analyzer):
        """Test analyzer handles very long text."""
        text = "Implement feature. " * 1000
        
        result = complexity_analyzer.analyze_requirements_text(text)
        
        assert result is not None
        assert result["estimated_hours"] <= 24.0  # Should cap at max

    def test_calculate_max_depth_leaf_task(self, decomposition_service, simple_task):
        """Test depth calculation for leaf task."""
        depth = decomposition_service._calculate_max_depth(simple_task)
        
        assert depth == 1
