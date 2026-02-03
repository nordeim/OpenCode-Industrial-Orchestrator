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

from .factories.session_factory import SessionEntityFactory, create_session_batch


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
        "",          # Empty string
        "   ",       # Whitespace only
    ])
    def test_invalid_titles_rejected(self, invalid_title):
        """Test that empty or whitespace-only titles are rejected"""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
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
        """Test agent config is empty dict by default"""
        session = SessionEntity(
            title="DEFAULT AGENT TEST",
            initial_prompt="test"
        )
        # Agent config defaults to empty dict - configured externally
        assert session.agent_config == {}


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
        (SessionStatus.PENDING, SessionStatus.RUNNING, True),  # Immediate execution
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
        # Clear any factory-added checkpoints
        session.checkpoints = []
        
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
