class AgentError(Exception):
    """Base class for agent-related exceptions"""
    pass

class AgentCapabilityMismatchError(AgentError):
    """Raised when an agent lacks the required capabilities for a task"""
    pass

class AgentPerformanceDegradedError(AgentError):
    """Raised when an agent's performance drops below acceptable thresholds"""
    pass

class AgentOverloadedError(AgentError):
    """Raised when an agent is assigned more work than its capacity allows"""
    pass

class AgentNotFoundError(AgentError):
    """Raised when a requested agent cannot be found"""
    pass
