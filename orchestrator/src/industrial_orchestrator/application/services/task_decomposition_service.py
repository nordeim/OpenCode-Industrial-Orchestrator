"""
INDUSTRIAL TASK DECOMPOSITION SERVICE
Advanced algorithms for breaking down complex tasks into manageable subtasks.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple, Set
from uuid import UUID, uuid4
from datetime import datetime, timezone

import networkx as nx
from pydantic import BaseModel, Field, ConfigDict

from ...domain.entities.task import (
    TaskEntity, TaskDecompositionTemplate, TaskComplexityLevel,
    TaskPriority, TaskDependencyType, TaskEstimate, AgentCapability
)
from ...domain.entities.agent import AgentType
from ...domain.exceptions.task_exceptions import (
    TaskDecompositionError,
    TaskComplexityOverflowError,
    TaskDependencyCycleError,
)


class DecompositionRule(BaseModel):
    """Rule for task decomposition"""
    
    pattern: str  # Regex pattern to match task title/description
    strategy: str  # Decomposition strategy
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=1, ge=1, le=10)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ComplexityAnalyzer(BaseModel):
    """Analyze task complexity using multiple heuristics"""
    
    @staticmethod
    def analyze_requirements_text(text: str) -> Dict[str, Any]:
        """Analyze requirements text for complexity indicators"""
        if not text:
            return {"word_count": 0, "estimated_hours": 1.0}
        
        word_count = len(text.split())
        sentence_count = len(re.split(r'[.!?]+', text))
        
        # Complexity heuristics
        complexity_indicators = {
            "must": 1,
            "should": 2,
            "could": 3,
            "would": 4,
            "implement": 2,
            "create": 2,
            "build": 3,
            "develop": 3,
            "design": 4,
            "architect": 5,
            "integrate": 4,
            "deploy": 3,
            "test": 2,
            "document": 1,
        }
        
        # Count technical terms
        technical_terms = re.findall(
            r'\b(API|database|authentication|encryption|scalability|performance|'
            r'security|deployment|integration|microservice|container|kubernetes|'
            r'docker|aws|azure|gcp|cloud|serverless)\b',
            text,
            re.IGNORECASE
        )
        
        # Estimate hours based on heuristics
        base_hours = word_count / 100  # 100 words ≈ 1 hour
        
        # Adjust for complexity indicators
        complexity_score = 1.0
        for indicator, weight in complexity_indicators.items():
            if indicator in text.lower():
                complexity_score += weight * 0.1
        
        # Adjust for technical terms
        complexity_score += len(technical_terms) * 0.2
        
        estimated_hours = base_hours * complexity_score
        
        return {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "technical_terms": len(technical_terms),
            "complexity_score": complexity_score,
            "estimated_hours": max(1.0, min(estimated_hours, 24.0)),
        }
    
    @staticmethod
    def estimate_from_task_description(task: TaskEntity) -> TaskEstimate:
        """Estimate task complexity from description"""
        if not task.description:
            return TaskEstimate(
                likely_hours=2.0,
                estimate_confidence=0.3,
                required_capabilities=[AgentCapability.CODE_GENERATION],
                estimation_source="default"
            )
        
        analysis = ComplexityAnalyzer.analyze_requirements_text(task.description)
        
        # Map to complexity levels
        hours = analysis["estimated_hours"]
        if hours < 0.25:
            likely_hours = 0.25
            optimistic = 0.1
            pessimistic = 0.5
        elif hours < 1.0:
            likely_hours = hours
            optimistic = hours * 0.5
            pessimistic = hours * 2.0
        elif hours < 4.0:
            likely_hours = hours
            optimistic = hours * 0.7
            pessimistic = hours * 1.5
        elif hours < 8.0:
            likely_hours = hours
            optimistic = hours * 0.8
            pessimistic = hours * 1.3
        else:
            likely_hours = 8.0
            optimistic = 6.0
            pessimistic = 12.0
        
        # Infer capabilities from description
        capabilities = ComplexityAnalyzer.infer_capabilities(task.description)
        
        # Calculate confidence based on analysis quality
        confidence = min(0.8, 0.3 + (analysis["word_count"] / 500))
        
        return TaskEstimate(
            optimistic_hours=optimistic,
            likely_hours=likely_hours,
            pessimistic_hours=pessimistic,
            estimated_tokens=analysis["word_count"] * 2,  # Rough estimate
            required_capabilities=capabilities,
            estimate_confidence=confidence,
            estimation_source="ai_analysis"
        )
    
    @staticmethod
    def infer_capabilities(text: str) -> List[AgentCapability]:
        """Infer required capabilities from text"""
        if not text:
            return [AgentCapability.CODE_GENERATION]
        
        text_lower = text.lower()
        capabilities = set()
        
        # Map keywords to capabilities
        keyword_map = {
            # Planning & Architecture
            "design": AgentCapability.SYSTEM_DESIGN,
            "architecture": AgentCapability.ARCHITECTURE_PLANNING,
            "plan": AgentCapability.ARCHITECTURE_PLANNING,
            "requirement": AgentCapability.REQUIREMENTS_ANALYSIS,
            "analyze": AgentCapability.REQUIREMENTS_ANALYSIS,
            "break down": AgentCapability.TASK_DECOMPOSITION,
            "decompose": AgentCapability.TASK_DECOMPOSITION,
            
            # Implementation
            "implement": AgentCapability.CODE_GENERATION,
            "create": AgentCapability.CODE_GENERATION,
            "build": AgentCapability.CODE_GENERATION,
            "develop": AgentCapability.CODE_GENERATION,
            "write": AgentCapability.CODE_GENERATION,
            "code": AgentCapability.CODE_GENERATION,
            "test": AgentCapability.TEST_GENERATION,
            "document": AgentCapability.DOCUMENTATION,
            "refactor": AgentCapability.REFACTORING,
            
            # Quality Assurance
            "review": AgentCapability.CODE_REVIEW,
            "audit": AgentCapability.SECURITY_AUDIT,
            "security": AgentCapability.SECURITY_AUDIT,
            "performance": AgentCapability.PERFORMANCE_ANALYSIS,
            "compliance": AgentCapability.COMPLIANCE_CHECK,
            
            # Problem Solving
            "debug": AgentCapability.DEBUGGING,
            "fix": AgentCapability.DEBUGGING,
            "troubleshoot": AgentCapability.TROUBLESHOOTING,
            "diagnose": AgentCapability.ROOT_CAUSE_ANALYSIS,
            "optimize": AgentCapability.OPTIMIZATION,
            "improve": AgentCapability.OPTIMIZATION,
            
            # Integration & Operations
            "deploy": AgentCapability.DEPLOYMENT,
            "configure": AgentCapability.CONFIGURATION,
            "monitor": AgentCapability.MONITORING,
            "scale": AgentCapability.SCALING,
            "integrate": AgentCapability.DEPLOYMENT,
        }
        
        for keyword, capability in keyword_map.items():
            if keyword in text_lower:
                capabilities.add(capability)
        
        # If no capabilities detected, default to code generation
        if not capabilities:
            capabilities.add(AgentCapability.CODE_GENERATION)
        
        return list(capabilities)


class TaskDecompositionService:
    """
    Industrial Task Decomposition Service
    
    Advanced algorithms for:
    1. Intelligent task breakdown
    2. Dependency graph generation
    3. Complexity analysis
    4. Parallel execution optimization
    """
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        
        # Predefined decomposition templates
        self._templates = self._load_default_templates()
        
        # Decomposition rules
        self._rules = self._load_default_rules()
        
        # Complexity analyzer
        self._analyzer = ComplexityAnalyzer()
    
    def _load_default_templates(self) -> Dict[str, TaskDecompositionTemplate]:
        """Load default decomposition templates"""
        return {
            "web_service_implementation": TaskDecompositionTemplate(
                name="Web Service Implementation",
                description="Template for implementing web services with full stack",
                complexity_threshold=TaskComplexityLevel.COMPLEX,
                decomposition_strategy="temporal",
                max_depth=4,
                target_leaf_complexity=TaskComplexityLevel.MODERATE,
                applicable_task_types=["web_service", "api", "backend"],
                subtask_templates=[
                    {
                        "phase": "requirements",
                        "title_template": "{parent_title} - Requirements Analysis",
                        "description": "Analyze and document requirements",
                        "capabilities": [AgentCapability.REQUIREMENTS_ANALYSIS],
                        "estimated_hours": 2.0,
                    },
                    {
                        "phase": "design",
                        "title_template": "{parent_title} - System Design",
                        "description": "Design system architecture and API",
                        "capabilities": [AgentCapability.SYSTEM_DESIGN],
                        "estimated_hours": 4.0,
                    },
                    {
                        "phase": "implementation",
                        "title_template": "{parent_title} - Implementation",
                        "description": "Implement core functionality",
                        "capabilities": [AgentCapability.CODE_GENERATION],
                        "estimated_hours": 8.0,
                    },
                    {
                        "phase": "testing",
                        "title_template": "{parent_title} - Testing",
                        "description": "Write and execute tests",
                        "capabilities": [AgentCapability.TEST_GENERATION],
                        "estimated_hours": 4.0,
                    },
                    {
                        "phase": "deployment",
                        "title_template": "{parent_title} - Deployment",
                        "description": "Deploy and configure service",
                        "capabilities": [AgentCapability.DEPLOYMENT],
                        "estimated_hours": 2.0,
                    },
                ],
            ),
            "refactoring_task": TaskDecompositionTemplate(
                name="Code Refactoring",
                description="Template for code refactoring tasks",
                complexity_threshold=TaskComplexityLevel.MODERATE,
                decomposition_strategy="functional",
                max_depth=3,
                target_leaf_complexity=TaskComplexityLevel.SIMPLE,
                applicable_task_types=["refactoring", "optimization"],
                subtask_templates=[
                    {
                        "component": "analysis",
                        "title_template": "{parent_title} - Code Analysis",
                        "description": "Analyze current code structure",
                        "capabilities": [AgentCapability.CODE_REVIEW],
                        "estimated_hours": 1.0,
                    },
                    {
                        "component": "planning",
                        "title_template": "{parent_title} - Refactoring Plan",
                        "description": "Plan refactoring approach",
                        "capabilities": [AgentCapability.SYSTEM_DESIGN],
                        "estimated_hours": 2.0,
                    },
                    {
                        "component": "execution",
                        "title_template": "{parent_title} - Refactoring Execution",
                        "description": "Execute refactoring changes",
                        "capabilities": [AgentCapability.REFACTORING],
                        "estimated_hours": 4.0,
                    },
                    {
                        "component": "verification",
                        "title_template": "{parent_title} - Verification",
                        "description": "Verify refactoring didn't break functionality",
                        "capabilities": [AgentCapability.TEST_GENERATION],
                        "estimated_hours": 2.0,
                    },
                ],
            ),
        }
    
    def _load_default_rules(self) -> List[DecompositionRule]:
        """Load default decomposition rules"""
        return [
            DecompositionRule(
                pattern=r".*(microservice|distributed).*",
                strategy="microservice_pattern",
                parameters={
                    "decomposition_strategy": "functional",
                    "service_count": 3,
                    "shared_components": ["auth", "database", "api_gateway"],
                },
                priority=5,
            ),
            DecompositionRule(
                pattern=r".*(CRUD|database|model).*",
                strategy="crud_pattern",
                parameters={
                    "decomposition_strategy": "capability",
                    "entities": ["create", "read", "update", "delete"],
                    "include_tests": True,
                },
                priority=4,
            ),
            DecompositionRule(
                pattern=r".*(UI|frontend|interface).*",
                strategy="ui_components",
                parameters={
                    "decomposition_strategy": "functional",
                    "components": ["layout", "navigation", "forms", "tables", "charts"],
                },
                priority=4,
            ),
            DecompositionRule(
                pattern=r".*(auth|authentication|security).*",
                strategy="security_pattern",
                parameters={
                    "decomposition_strategy": "temporal",
                    "phases": ["design", "implementation", "testing", "audit"],
                    "security_level": "high",
                },
                priority=6,  # High priority for security
            ),
        ]
    
    def analyze_and_decompose(
        self,
        task: TaskEntity,
        auto_estimate: bool = True,
        apply_templates: bool = True,
        apply_rules: bool = True,
        max_depth: int = 3
    ) -> TaskEntity:
        """
        Comprehensive task analysis and decomposition
        
        Args:
            task: Task to decompose
            auto_estimate: Automatically estimate complexity
            apply_templates: Apply matching templates
            apply_rules: Apply decomposition rules
            max_depth: Maximum decomposition depth
        
        Returns:
            Decomposed task with subtasks
        """
        self._logger.info(f"Analyzing task: {task.title} (ID: {task.id})")
        
        # Step 1: Auto-estimate if needed
        if auto_estimate and (not task.estimate or task.estimate.estimate_confidence < 0.5):
            new_estimate = self._analyzer.estimate_from_task_description(task)
            task.estimate = new_estimate
            self._logger.debug(f"Auto-estimated task: {task.estimate.expected_hours:.1f} hours")
        
        # Step 2: Apply matching templates
        if apply_templates:
            applied_templates = self._apply_matching_templates(task)
            if applied_templates:
                self._logger.info(f"Applied {len(applied_templates)} templates to task")
        
        # Step 3: Apply decomposition rules
        if apply_rules:
            applied_rules = self._apply_decomposition_rules(task)
            if applied_rules:
                self._logger.info(f"Applied {len(applied_rules)} rules to task")
        
        # Step 4: Recursively decompose child tasks
        if max_depth > 0:
            for child in task.child_tasks.copy():  # Copy to avoid modification issues
                if child.estimate.complexity_level.value >= TaskComplexityLevel.MODERATE.value:
                    self.analyze_and_decompose(
                        child,
                        auto_estimate=auto_estimate,
                        apply_templates=apply_templates,
                        apply_rules=apply_rules,
                        max_depth=max_depth - 1
                    )
        
        # Step 5: Validate decomposition
        self._validate_decomposition(task)
        
        self._logger.info(
            f"Decomposition complete: {task.count_subtasks()} total subtasks, "
            f"max depth: {self._calculate_max_depth(task)}"
        )
        
        return task
    
    def _apply_matching_templates(self, task: TaskEntity) -> List[str]:
        """Apply matching decomposition templates to task"""
        applied = []
        
        for template_name, template in self._templates.items():
            try:
                subtasks = template.apply_to_task(task)
                if subtasks:
                    applied.append(template_name)
                    self._logger.debug(f"Applied template '{template_name}' to task {task.id}")
            except Exception as e:
                self._logger.warning(f"Failed to apply template '{template_name}': {e}")
        
        return applied
    
    def _apply_decomposition_rules(self, task: TaskEntity) -> List[str]:
        """Apply decomposition rules to task"""
        applied = []
        
        # Combine title and description for pattern matching
        text_to_match = f"{task.title} {task.description or ''}"
        
        for rule in sorted(self._rules, key=lambda r: r.priority, reverse=True):
            if re.search(rule.pattern, text_to_match, re.IGNORECASE):
                try:
                    self._apply_rule(rule, task)
                    applied.append(rule.pattern)
                    self._logger.debug(f"Applied rule '{rule.pattern}' to task {task.id}")
                except Exception as e:
                    self._logger.warning(f"Failed to apply rule '{rule.pattern}': {e}")
        
        return applied
    
    def _apply_rule(self, rule: DecompositionRule, task: TaskEntity) -> None:
        """Apply a specific decomposition rule to task"""
        strategy = rule.strategy
        params = rule.parameters
        
        if strategy == "microservice_pattern":
            self._decompose_microservice(task, params)
        elif strategy == "crud_pattern":
            self._decompose_crud(task, params)
        elif strategy == "ui_components":
            self._decompose_ui_components(task, params)
        elif strategy == "security_pattern":
            self._decompose_security(task, params)
        else:
            # Default decomposition
            task.decompose(
                decomposition_strategy=params.get("decomposition_strategy", "functional"),
                max_depth=params.get("max_depth", 3),
                target_complexity=TaskComplexityLevel.MODERATE
            )
    
    def _decompose_microservice(self, task: TaskEntity, params: Dict[str, Any]) -> None:
        """Decompose microservice task into services and shared components"""
        service_count = params.get("service_count", 3)
        shared_components = params.get("shared_components", [])
        
        # Create service tasks
        for i in range(service_count):
            service_task = TaskEntity(
                session_id=task.session_id,
                parent_task_id=task.id,
                title=f"{task.title} - Service {i+1}",
                description=f"Microservice {i+1} implementation",
                task_type="microservice",
                priority=task.priority,
                estimate=TaskEstimate(
                    likely_hours=task.estimate.likely_hours / (service_count + len(shared_components)),
                    required_capabilities=[AgentCapability.CODE_GENERATION, AgentCapability.DEPLOYMENT],
                    estimation_source="microservice_decomposition"
                )
            )
            task.add_child_task(service_task)
        
        # Create shared component tasks
        for component in shared_components:
            component_task = TaskEntity(
                session_id=task.session_id,
                parent_task_id=task.id,
                title=f"{task.title} - {component.title()} Component",
                description=f"Shared {component} component for microservices",
                task_type="shared_component",
                priority=task.priority,
                estimate=TaskEstimate(
                    likely_hours=task.estimate.likely_hours * 0.5 / len(shared_components),
                    required_capabilities=[AgentCapability.CODE_GENERATION, AgentCapability.SYSTEM_DESIGN],
                    estimation_source="microservice_decomposition"
                )
            )
            
            # Add dependencies: services depend on shared components
            for i, service_task in enumerate(task.child_tasks[:service_count]):
                service_task.add_dependency(
                    component_task.id,
                    dependency_type=TaskDependencyType.START_TO_START,
                    description=f"Requires {component} component"
                )
            
            task.add_child_task(component_task)
    
    def _decompose_crud(self, task: TaskEntity, params: Dict[str, Any]) -> None:
        """Decompose CRUD task into entity operations"""
        entities = params.get("entities", ["create", "read", "update", "delete"])
        include_tests = params.get("include_tests", True)
        
        # Create entity operation tasks
        for entity_op in entities:
            op_task = TaskEntity(
                session_id=task.session_id,
                parent_task_id=task.id,
                title=f"{task.title} - {entity_op.title()}",
                description=f"{entity_op.title()} operation implementation",
                task_type="crud_operation",
                priority=task.priority,
                estimate=TaskEstimate(
                    likely_hours=task.estimate.likely_hours / len(entities),
                    required_capabilities=[AgentCapability.CODE_GENERATION],
                    estimation_source="crud_decomposition"
                )
            )
            task.add_child_task(op_task)
        
        # Add test task if requested
        if include_tests:
            test_task = TaskEntity(
                session_id=task.session_id,
                parent_task_id=task.id,
                title=f"{task.title} - Tests",
                description="CRUD operation tests",
                task_type="testing",
                priority=task.priority,
                estimate=TaskEstimate(
                    likely_hours=task.estimate.likely_hours * 0.3,
                    required_capabilities=[AgentCapability.TEST_GENERATION],
                    estimation_source="crud_decomposition"
                )
            )
            
            # Tests depend on all operations
            for op_task in task.child_tasks:
                if op_task.task_type == "crud_operation":
                    test_task.add_dependency(
                        op_task.id,
                        dependency_type=TaskDependencyType.FINISH_TO_START,
                        description=f"Test depends on {op_task.title}"
                    )
            
            task.add_child_task(test_task)
    
    def _decompose_ui_components(self, task: TaskEntity, params: Dict[str, Any]) -> None:
        """Decompose UI task into components"""
        components = params.get("components", ["layout", "navigation", "forms", "tables", "charts"])
        
        for component in components:
            component_task = TaskEntity(
                session_id=task.session_id,
                parent_task_id=task.id,
                title=f"{task.title} - {component.title()} Component",
                description=f"UI {component} component implementation",
                task_type="ui_component",
                priority=task.priority,
                estimate=TaskEstimate(
                    likely_hours=task.estimate.likely_hours / len(components),
                    required_capabilities=[AgentCapability.CODE_GENERATION],
                    estimation_source="ui_decomposition"
                )
            )
            
            # Add dependencies: some components depend on others
            if component in ["forms", "tables", "charts"]:
                # These depend on layout
                for layout_task in task.child_tasks:
                    if "layout" in layout_task.title.lower():
                        component_task.add_dependency(
                            layout_task.id,
                            dependency_type=TaskDependencyType.START_TO_START,
                            description="Requires layout component"
                        )
            
            task.add_child_task(component_task)
    
    def _decompose_security(self, task: TaskEntity, params: Dict[str, Any]) -> None:
        """Decompose security task with rigorous phases"""
        phases = params.get("phases", ["design", "implementation", "testing", "audit"])
        security_level = params.get("security_level", "high")
        
        # Adjust estimates based on security level
        level_multipliers = {
            "low": 0.5,
            "medium": 1.0,
            "high": 1.5,
            "critical": 2.0,
        }
        multiplier = level_multipliers.get(security_level, 1.0)
        
        previous_task = None
        for i, phase in enumerate(phases):
            phase_task = TaskEntity(
                session_id=task.session_id,
                parent_task_id=task.id,
                title=f"{task.title} - {phase.title()}",
                description=f"Security {phase} phase",
                task_type=f"security_{phase}",
                priority=TaskPriority.HIGH if security_level in ["high", "critical"] else task.priority,
                estimate=TaskEstimate(
                    likely_hours=task.estimate.likely_hours * multiplier / len(phases),
                    required_capabilities=self._get_security_capabilities(phase),
                    estimation_source="security_decomposition"
                )
            )
            
            # Add sequential dependencies
            if previous_task:
                phase_task.add_dependency(
                    previous_task.id,
                    dependency_type=TaskDependencyType.FINISH_TO_START,
                    description=f"Depends on {previous_task.title}"
                )
            
            task.add_child_task(phase_task)
            previous_task = phase_task
    
    def _get_security_capabilities(self, phase: str) -> List[AgentCapability]:
        """Get capabilities required for security phase"""
        phase_capabilities = {
            "design": [AgentCapability.SYSTEM_DESIGN, AgentCapability.SECURITY_AUDIT],
            "implementation": [AgentCapability.CODE_GENERATION, AgentCapability.SECURITY_AUDIT],
            "testing": [AgentCapability.TEST_GENERATION, AgentCapability.SECURITY_AUDIT],
            "audit": [AgentCapability.SECURITY_AUDIT, AgentCapability.CODE_REVIEW],
        }
        return phase_capabilities.get(phase, [AgentCapability.CODE_GENERATION])

    def _validate_decomposition(self, task: TaskEntity) -> None:
        """Validate decomposition for cycles and depth limits"""
        if task.validate_dependencies() is False:
             raise TaskDependencyCycleError("Decomposition created task dependency cycle")
        
        if self._calculate_max_depth(task) > 10: # Arbitrary depth limit safety
             raise TaskComplexityOverflowError("Decomposition depth exceeded safety limit")

    def _calculate_max_depth(self, task: TaskEntity) -> int:
        """Calculate maximum depth of task hierarchy"""
        if not task.child_tasks:
            return 1
        return 1 + max(self._calculate_max_depth(child) for child in task.child_tasks)
