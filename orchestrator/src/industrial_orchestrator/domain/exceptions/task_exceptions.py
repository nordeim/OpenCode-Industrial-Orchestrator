class TaskError(Exception):
    """Base class for task-related exceptions"""
    pass

class TaskDependencyCycleError(TaskError):
    """Raised when a circular dependency is detected in the task graph"""
    pass

class TaskComplexityOverflowError(TaskError):
    """Raised when a task's complexity exceeds the maximum allowed limit"""
    pass

class TaskDecompositionError(TaskError):
    """Raised when a task cannot be decomposed according to the requested strategy"""
    pass

class TaskNotFoundError(TaskError):
    """Raised when a requested task cannot be found"""
    pass
