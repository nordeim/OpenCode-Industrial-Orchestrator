"""
INDUSTRIAL TASK ENTITY
Advanced task models with decomposition, dependencies, and complexity analysis.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Set, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator, ConfigDict
import networkx as nx

from .agent import AgentCapability
from ..value_objects.session_status import SessionStatus
from ..exceptions.task_exceptions import (
    TaskDependencyCycleError,
    TaskComplexityOverflowError,
    TaskDecompositionError,
)


class TaskComplexityLevel(str, Enum):
    """Task complexity classification"""
    TRIVIAL = "trivial"      # < 15 minutes, simple implementation
    SIMPLE = "simple"        # 15-60 minutes, straightforward
    MODERATE = "moderate"    # 1-4 hours, some complexity
    COMPLEX = "complex"      # 4-8 hours, significant complexity
    EXPERT = "expert"        # 8+ hours, very complex, multiple components


class TaskPriority(str, Enum):
    """Task execution priority"""
    BLOCKER = "blocker"      # Blocks all other work
    CRITICAL = "critical"    # Must be completed soon
    HIGH = "high"            # Important, but not blocking
    NORMAL = "normal"        # Standard priority
    LOW = "low"              # Can be deferred
    BACKGROUND = "background" # Non-urgent background work


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"          # Created, not started
    READY = "ready"              # Dependencies satisfied, ready to start
    ASSIGNED = "assigned"        # Assigned to agent, not started
    IN_PROGRESS = "in_progress"  # Currently being worked on
    BLOCKED = "blocked"          # Blocked by external factor
    PAUSED = "paused"            # Manually paused
    COMPLETED = "completed"      # Successfully completed
    FAILED = "failed"            # Failed execution
    CANCELLED = "cancelled"      # Cancelled before completion
    SKIPPED = "skipped"          # Skipped (dependency failed)


class TaskDependencyType(str, Enum):
    """Types of task dependencies"""
    FINISH_TO_START = "finish_to_start"  # B can't start until A finishes
    START_TO_START = "start_to_start"    # B can't start until A starts
    FINISH_TO_FINISH = "finish_to_finish" # B can't finish until A finishes
    START_TO_FINISH = "start_to_finish"   # B can't finish until A starts


class TaskDependency(BaseModel):
    """Task dependency relationship"""
    
    source_task_id: UUID
    target_task_id: UUID
    dependency_type: TaskDependencyType = Field(default=TaskDependencyType.FINISH_TO_START)
    is_required: bool = Field(default=True)
    description: Optional[str] = Field(None, max_length=200)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class TaskEstimate(BaseModel):
    """Task time and resource estimates"""
    
    # Time estimates (in hours)
    optimistic_hours: float = Field(default=0.0, ge=0.0)
    likely_hours: float = Field(default=0.0, ge=0.0)
    pessimistic_hours: float = Field(default=0.0, ge=0.0)
    
    # Resource estimates
    estimated_tokens: Optional[int] = Field(None, ge=0)
    estimated_cost_usd: Optional[float] = Field(None, ge=0.0)
    required_capabilities: List[AgentCapability] = Field(default_factory=list)
    
    # Confidence metrics
    estimate_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    last_estimated_at: Optional[datetime] = None
    estimation_source: str = Field(default="manual")  # manual, ai, historical
    
    @property
    def expected_hours(self) -> float:
        """Calculate expected hours using PERT formula"""
        if self.optimistic_hours == 0 and self.likely_hours == 0 and self.pessimistic_hours == 0:
            return 0.0
        
        return (self.optimistic_hours + 4 * self.likely_hours + self.pessimistic_hours) / 6
    
    @property
    def standard_deviation_hours(self) -> float:
        """Calculate standard deviation"""
        if self.pessimistic_hours <= self.optimistic_hours:
            return 0.0
        return (self.pessimistic_hours - self.optimistic_hours) / 6
    
    @property
    def complexity_level(self) -> TaskComplexityLevel:
        """Determine complexity level based on expected hours"""
        hours = self.expected_hours
        
        if hours < 0.25:  # < 15 minutes
            return TaskComplexityLevel.TRIVIAL
        elif hours < 1.0:  # < 1 hour
            return TaskComplexityLevel.SIMPLE
        elif hours < 4.0:  # < 4 hours
            return TaskComplexityLevel.MODERATE
        elif hours < 8.0:  # < 8 hours
            return TaskComplexityLevel.COMPLEX
        else:  # 8+ hours
            return TaskComplexityLevel.EXPERT
    
    def update_from_execution(
        self,
        actual_hours: float,
        actual_tokens: Optional[int] = None,
        actual_cost_usd: Optional[float] = None
    ) -> None:
        """Update estimates based on actual execution"""
        # Simple learning algorithm - could be more sophisticated
        self.likely_hours = (self.likely_hours + actual_hours) / 2
        
        # Adjust optimistic/pessimistic based on variance
        variance = abs(actual_hours - self.expected_hours)
        if actual_hours < self.optimistic_hours:
            self.optimistic_hours = actual_hours
        elif actual_hours > self.pessimistic_hours:
            self.pessimistic_hours = actual_hours
        
        # Update confidence (increases with more data)
        self.estimate_confidence = min(0.95, self.estimate_confidence + 0.05)
        
        # Update resource estimates
        if actual_tokens is not None:
            self.estimated_tokens = actual_tokens
        
        if actual_cost_usd is not None:
            self.estimated_cost_usd = actual_cost_usd
        
        self.last_estimated_at = datetime.now(timezone.utc)
        self.estimation_source = "historical"


class TaskEntity(BaseModel):
    """
    Industrial Task Entity
    
    Represents a unit of work within a session with:
    1. Decomposition hierarchy
    2. Dependency management
    3. Complexity analysis
    4. Progress tracking
    """
    
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID = Field(...)  # Required for isolation
    session_id: UUID
    parent_task_id: Optional[UUID] = None
    
    # Task identity
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    task_type: str = Field(default="implementation")
    
    # Execution state
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    status_updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    assigned_agent_id: Optional[UUID] = None
    assigned_at: Optional[datetime] = None
    
    # Planning
    priority: TaskPriority = Field(default=TaskPriority.NORMAL)
    estimate: TaskEstimate = Field(default_factory=TaskEstimate)
    
    # Dependencies
    dependencies: List[TaskDependency] = Field(default_factory=list)
    dependents: List[UUID] = Field(default_factory=list)  # Reverse references
    
    # Execution tracking
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Child tasks (for decomposition)
    child_tasks: List["TaskEntity"] = Field(default_factory=list)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    @field_validator('title')
    @classmethod
    def validate_task_title(cls, v: str) -> str:
        """Ensure task titles are descriptive and actionable"""
        if not v.strip():
            raise ValueError("Task title cannot be empty")
        
        # Should be actionable (start with verb)
        action_verbs = [
            'implement', 'create', 'add', 'update', 'fix', 'refactor',
            'optimize', 'test', 'review', 'deploy', 'configure', 'document'
        ]
        
        first_word = v.split()[0].lower() if v.split() else ""
        if first_word not in action_verbs:
            raise ValueError(
                f"Task title should start with an action verb. "
                f"Examples: {', '.join(action_verbs[:5])}..."
            )
        
        return v.strip()
    
    @property
    def is_leaf_task(self) -> bool:
        """Check if task is a leaf (no children)"""
        return len(self.child_tasks) == 0
    
    @property
    def is_root_task(self) -> bool:
        """Check if task is a root (no parent)"""
        return self.parent_task_id is None
    
    @property
    def elapsed_hours(self) -> Optional[float]:
        """Calculate elapsed hours if in progress"""
        if self.started_at and not self.completed_at and not self.failed_at:
            return (datetime.now(timezone.utc) - self.started_at).total_seconds() / 3600
        return None
    
    @property
    def duration_hours(self) -> Optional[float]:
        """Calculate total duration if completed"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() / 3600
        elif self.started_at and self.failed_at:
            return (self.failed_at - self.started_at).total_seconds() / 3600
        return None
    
    @property
    def can_start(self) -> bool:
        """Check if task can start (dependencies satisfied)"""
        if self.status != TaskStatus.PENDING and self.status != TaskStatus.READY:
            return False
        
        # Check required dependencies
        for dep in self.dependencies:
            if dep.is_required:
                # For now, assume dependency satisfaction check
                # In practice, would check actual dependency status
                return False
        
        return True
    
    @property
    def is_blocked(self) -> bool:
        """Check if task is blocked by dependencies"""
        return self.status == TaskStatus.BLOCKED or (self.status == TaskStatus.PENDING and not self.can_start)
    
    def add_dependency(
        self,
        task_id: UUID,
        dependency_type: TaskDependencyType = TaskDependencyType.FINISH_TO_START,
        is_required: bool = True,
        description: Optional[str] = None
    ) -> None:
        """Add dependency to another task"""
        # Check for self-dependency
        if task_id == self.id:
            raise ValueError("Task cannot depend on itself")
        
        # Check for duplicate
        existing = any(dep.target_task_id == task_id for dep in self.dependencies)
        if existing:
            raise ValueError(f"Dependency on task {task_id} already exists")
        
        dependency = TaskDependency(
            source_task_id=self.id,
            target_task_id=task_id,
            dependency_type=dependency_type,
            is_required=is_required,
            description=description
        )
        
        self.dependencies.append(dependency)
        self.updated_at = datetime.now(timezone.utc)
    
    def add_child_task(self, child_task: "TaskEntity") -> None:
        """Add child task (decomposition)"""
        # Set parent reference
        child_task.parent_task_id = self.id
        
        # Add to children
        self.child_tasks.append(child_task)
        self.updated_at = datetime.now(timezone.utc)
    
    def decompose(
        self,
        decomposition_strategy: str = "functional",
        max_depth: int = 3,
        target_complexity: TaskComplexityLevel = TaskComplexityLevel.MODERATE
    ) -> List["TaskEntity"]:
        """
        Decompose task into subtasks based on strategy
        
        Args:
            decomposition_strategy: Strategy for decomposition
                - "functional": By functional components
                - "temporal": By time/phase
                - "capability": By required capabilities
            max_depth: Maximum decomposition depth
            target_complexity: Target complexity for leaf tasks
        
        Returns:
            List of generated subtasks
        """
        if max_depth <= 0:
            return []
        
        current_complexity = self.estimate.complexity_level
        complexity_value = {
            TaskComplexityLevel.TRIVIAL: 1,
            TaskComplexityLevel.SIMPLE: 2,
            TaskComplexityLevel.MODERATE: 3,
            TaskComplexityLevel.COMPLEX: 4,
            TaskComplexityLevel.EXPERT: 5,
        }
        
        target_value = complexity_value.get(target_complexity, 3)
        current_value = complexity_value.get(current_complexity, 3)
        
        # Don't decompose if already at or below target complexity
        if current_value <= target_value:
            return []
        
        # Determine decomposition factor
        decomposition_factor = current_value - target_value + 1
        
        # Generate subtasks based on strategy
        subtasks = []
        
        if decomposition_strategy == "functional":
            # Decompose by functional components
            components = [
                f"{self.title} - Component {i+1}"
                for i in range(decomposition_factor)
            ]
            
            for i, component in enumerate(components):
                subtask = TaskEntity(
                    tenant_id=self.tenant_id,
                    session_id=self.session_id,
                    parent_task_id=self.id,
                    title=component,
                    description=f"Functional component {i+1} of {self.title}",
                    task_type=self.task_type,
                    priority=self.priority,
                    estimate=TaskEstimate(
                        likely_hours=self.estimate.likely_hours / decomposition_factor,
                        estimate_confidence=self.estimate.estimate_confidence * 0.8,
                        required_capabilities=self.estimate.required_capabilities.copy(),
                        estimation_source="decomposition"
                    )
                )
                
                # Further decompose if needed
                if max_depth > 1:
                    child_subtasks = subtask.decompose(
                        decomposition_strategy,
                        max_depth - 1,
                        target_complexity
                    )
                    for child in child_subtasks:
                        subtask.add_child_task(child)
                
                subtasks.append(subtask)
        
        elif decomposition_strategy == "temporal":
            # Decompose by phases/stages
            phases = ["Analysis", "Design", "Implementation", "Testing", "Review"]
            phases = phases[:decomposition_factor]
            
            for i, phase in enumerate(phases):
                subtask = TaskEntity(
                    tenant_id=self.tenant_id,
                    session_id=self.session_id,
                    parent_task_id=self.id,
                    title=f"{self.title} - {phase}",
                    description=f"{phase} phase of {self.title}",
                    task_type=f"{self.task_type}_{phase.lower()}",
                    priority=self.priority,
                    estimate=TaskEstimate(
                        likely_hours=self.estimate.likely_hours / len(phases),
                        estimate_confidence=self.estimate.estimate_confidence * 0.7,
                        required_capabilities=self.estimate.required_capabilities.copy(),
                        estimation_source="decomposition"
                    )
                )
                
                # Add dependencies between phases
                if i > 0:
                    subtask.add_dependency(
                        subtasks[-1].id,
                        dependency_type=TaskDependencyType.FINISH_TO_START,
                        description=f"Depends on {phases[i-1]} phase"
                    )
                
                subtasks.append(subtask)
        
        elif decomposition_strategy == "capability":
            # Decompose by required capabilities
            capabilities = self.estimate.required_capabilities
            if not capabilities:
                capabilities = [AgentCapability.CODE_GENERATION]
            
            for i, capability in enumerate(capabilities[:decomposition_factor]):
                subtask = TaskEntity(
                    session_id=self.session_id,
                    parent_task_id=self.id,
                    title=f"{self.title} - {capability.value.replace('_', ' ').title()}",
                    description=f"{capability.value.replace('_', ' ')} aspect of {self.title}",
                    task_type=f"{self.task_type}_{capability.value}",
                    priority=self.priority,
                    estimate=TaskEstimate(
                        likely_hours=self.estimate.likely_hours / len(capabilities),
                        estimate_confidence=self.estimate.estimate_confidence * 0.6,
                        required_capabilities=[capability],
                        estimation_source="decomposition"
                    )
                )
                
                subtasks.append(subtask)
        
        # Add subtasks as children
        for subtask in subtasks:
            self.add_child_task(subtask)
        
        return subtasks
    
    def get_dependency_graph(self) -> nx.DiGraph:
        """Get NetworkX graph of task dependencies"""
        graph = nx.DiGraph()
        
        # Add this task
        graph.add_node(self.id, task=self)
        
        # Add dependencies
        for dep in self.dependencies:
            graph.add_edge(dep.target_task_id, dep.source_task_id, dependency=dep)
        
        # Add child task dependencies recursively
        for child in self.child_tasks:
            child_graph = child.get_dependency_graph()
            graph = nx.compose(graph, child_graph)
            
            # Add parent-child relationship
            graph.add_edge(self.id, child.id, relationship="parent_child")
        
        return graph
    
    def validate_dependencies(self) -> bool:
        """Validate that dependency graph has no cycles"""
        try:
            graph = self.get_dependency_graph()
            cycles = list(nx.simple_cycles(graph))
            
            if cycles:
                raise TaskDependencyCycleError(
                    f"Task dependency cycle detected: {cycles}"
                )
            
            return True
            
        except nx.NetworkXNoCycle:
            return True
    
    def get_execution_order(self) -> List[UUID]:
        """Get topological order for task execution"""
        graph = self.get_dependency_graph()
        
        try:
            return list(nx.topological_sort(graph))
        except nx.NetworkXUnfeasible:
            raise TaskDependencyCycleError("Cannot determine execution order due to cycles")
    
    def calculate_critical_path(self) -> List[UUID]:
        """Calculate critical path for task execution"""
        graph = self.get_dependency_graph()
        
        # Add duration estimates to graph
        for node_id in graph.nodes():
            task = graph.nodes[node_id].get('task')
            if task and task.estimate:
                graph.nodes[node_id]['duration'] = task.estimate.expected_hours
            else:
                graph.nodes[node_id]['duration'] = 0
        
        # Calculate critical path (simplified)
        try:
            # For DAGs, longest path = critical path
            longest_paths = nx.dag_longest_path(graph, weight='duration')
            return longest_paths
        except nx.NetworkXUnfeasible:
            raise TaskDependencyCycleError("Cannot calculate critical path due to cycles")
    
    def update_status(self, new_status: TaskStatus) -> None:
        """Update task status with validation"""
        valid_transitions = {
            TaskStatus.PENDING: {TaskStatus.READY, TaskStatus.ASSIGNED, TaskStatus.CANCELLED},
            TaskStatus.READY: {TaskStatus.ASSIGNED, TaskStatus.CANCELLED},
            TaskStatus.ASSIGNED: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
            TaskStatus.IN_PROGRESS: {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.BLOCKED, TaskStatus.PAUSED},
            TaskStatus.BLOCKED: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
            TaskStatus.PAUSED: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
            TaskStatus.COMPLETED: set(),
            TaskStatus.FAILED: set(),
            TaskStatus.CANCELLED: set(),
            TaskStatus.SKIPPED: set(),
        }
        
        if new_status not in valid_transitions.get(self.status, set()):
            raise ValueError(
                f"Invalid status transition from {self.status} to {new_status}"
            )
        
        old_status = self.status
        self.status = new_status
        self.status_updated_at = datetime.now(timezone.utc)
        
        # Update timestamps based on status
        if new_status == TaskStatus.IN_PROGRESS and not self.started_at:
            self.started_at = datetime.now(timezone.utc)
        elif new_status == TaskStatus.COMPLETED and not self.completed_at:
            self.completed_at = datetime.now(timezone.utc)
        elif new_status == TaskStatus.FAILED and not self.failed_at:
            self.failed_at = datetime.now(timezone.utc)
        
        self.updated_at = datetime.now(timezone.utc)
        
        return old_status
    
    def assign_to_agent(self, agent_id: UUID) -> None:
        """Assign task to agent"""
        if self.status not in [TaskStatus.PENDING, TaskStatus.READY]:
            raise ValueError(f"Cannot assign task in status {self.status}")
        
        self.assigned_agent_id = agent_id
        self.assigned_at = datetime.now(timezone.utc)
        self.update_status(TaskStatus.ASSIGNED)
    
    def complete_with_result(
        self,
        result: Dict[str, Any],
        quality_score: Optional[float] = None,
        actual_hours: Optional[float] = None,
        actual_tokens: Optional[int] = None,
        actual_cost_usd: Optional[float] = None
    ) -> None:
        """Mark task as completed with results"""
        self.result = result
        
        # Update estimates with actuals
        if actual_hours is not None:
            self.estimate.update_from_execution(
                actual_hours=actual_hours,
                actual_tokens=actual_tokens,
                actual_cost_usd=actual_cost_usd
            )
        
        self.update_status(TaskStatus.COMPLETED)
    
    def fail_with_error(
        self,
        error: Exception,
        error_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Mark task as failed with error"""
        self.error = {
            "type": error.__class__.__name__,
            "message": str(error),
            "context": error_context or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        self.update_status(TaskStatus.FAILED)
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get task progress summary"""
        total_tasks = self.count_subtasks()
        completed_tasks = self.count_subtasks(status_filter=TaskStatus.COMPLETED)
        in_progress_tasks = self.count_subtasks(status_filter=TaskStatus.IN_PROGRESS)
        failed_tasks = self.count_subtasks(status_filter=TaskStatus.FAILED)
        
        return {
            "task_id": str(self.id),
            "title": self.title,
            "status": self.status.value,
            "progress_percentage": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "failed_tasks": failed_tasks,
            "blocked_tasks": self.count_subtasks(status_filter=TaskStatus.BLOCKED),
            "elapsed_hours": self.elapsed_hours,
            "duration_hours": self.duration_hours,
            "estimated_remaining_hours": self.estimate.expected_hours - (self.elapsed_hours or 0),
            "assigned_agent": str(self.assigned_agent_id) if self.assigned_agent_id else None,
            "complexity": self.estimate.complexity_level.value,
            "priority": self.priority.value,
        }
    
    def count_subtasks(self, status_filter: Optional[TaskStatus] = None) -> int:
        """Count subtasks (recursive) optionally filtered by status"""
        count = 0
        
        # Count children
        for child in self.child_tasks:
            if status_filter is None or child.status == status_filter:
                count += 1
            
            # Recurse
            count += child.count_subtasks(status_filter)
        
        return count
    
    def find_subtask(self, task_id: UUID) -> Optional["TaskEntity"]:
        """Find subtask by ID (recursive)"""
        if self.id == task_id:
            return self
        
        for child in self.child_tasks:
            found = child.find_subtask(task_id)
            if found:
                return found
        
        return None
    
    def flatten_hierarchy(self) -> List["TaskEntity"]:
        """Flatten task hierarchy into list"""
        tasks = [self]
        
        for child in self.child_tasks:
            tasks.extend(child.flatten_hierarchy())
        
        return tasks


class TaskDecompositionTemplate(BaseModel):
    """Template for task decomposition strategies"""
    
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    # Decomposition rules
    complexity_threshold: TaskComplexityLevel = Field(default=TaskComplexityLevel.COMPLEX)
    decomposition_strategy: str = Field(default="functional")
    max_depth: int = Field(default=3, ge=1, le=5)
    target_leaf_complexity: TaskComplexityLevel = Field(default=TaskComplexityLevel.MODERATE)
    
    # Task type applicability
    applicable_task_types: List[str] = Field(default_factory=lambda: ["implementation"])
    excluded_task_types: List[str] = Field(default_factory=list)
    
    # Generation rules
    subtask_templates: List[Dict[str, Any]] = Field(default_factory=list)
    dependency_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    version: str = Field(default="1.0.0")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def apply_to_task(self, task: TaskEntity) -> List[TaskEntity]:
        """Apply decomposition template to task"""
        # Check applicability
        if task.task_type in self.excluded_task_types:
            return []
        
        if self.applicable_task_types and task.task_type not in self.applicable_task_types:
            return []
        
        # Check complexity threshold
        task_complexity_value = {
            TaskComplexityLevel.TRIVIAL: 1,
            TaskComplexityLevel.SIMPLE: 2,
            TaskComplexityLevel.MODERATE: 3,
            TaskComplexityLevel.COMPLEX: 4,
            TaskComplexityLevel.EXPERT: 5,
        }
        
        threshold_value = task_complexity_value.get(self.complexity_threshold, 3)
        actual_value = task_complexity_value.get(task.estimate.complexity_level, 3)
        
        if actual_value < threshold_value:
            return []  # Task not complex enough for decomposition
        
        # Apply decomposition
        return task.decompose(
            decomposition_strategy=self.decomposition_strategy,
            max_depth=self.max_depth,
            target_complexity=self.target_leaf_complexity
        )
