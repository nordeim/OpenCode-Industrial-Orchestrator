"""
INDUSTRIAL SESSION STATUS STATE MACHINE
Precise state transitions with validation for resilient orchestration.
"""

from enum import Enum
from typing import Set, Dict


class SessionStatus(str, Enum):
    """
    Industrial-grade session status enumeration
    
    Design Principles:
    1. Terminal states are clearly defined
    2. Transitions are validated via can_transition_to
    3. Each state has clear business meaning
    """
    
    # Initial state
    PENDING = "pending"            # Created, awaiting execution
    
    # Active states
    QUEUED = "queued"              # In execution queue
    RUNNING = "running"            # Actively executing
    PAUSED = "paused"              # Manually paused
    
    # Terminal success states
    COMPLETED = "completed"        # Successfully finished
    PARTIALLY_COMPLETED = "partially_completed"  # Some sub-tasks succeeded
    
    # Terminal failure states
    FAILED = "failed"              # Execution failed
    TIMEOUT = "timeout"            # Exceeded max duration
    STOPPED = "stopped"            # Manually stopped
    CANCELLED = "cancelled"        # Cancelled before execution
    
    # System states
    ORPHANED = "orphaned"          # Lost parent/child relationship
    DEGRADED = "degraded"          # Running with reduced capacity
    
    @classmethod
    def get_terminal_states(cls) -> Set["SessionStatus"]:
        """States from which no further transitions are allowed"""
        return {
            cls.COMPLETED,
            cls.PARTIALLY_COMPLETED,
            cls.FAILED,
            cls.TIMEOUT,
            cls.STOPPED,
            cls.CANCELLED,
            cls.ORPHANED,
        }
    
    @classmethod
    def get_active_states(cls) -> Set["SessionStatus"]:
        """States where session is actively being processed"""
        return {
            cls.QUEUED,
            cls.RUNNING,
            cls.PAUSED,
            cls.DEGRADED,
        }
    
    @classmethod
    def get_error_states(cls) -> Set["SessionStatus"]:
        """States indicating some form of failure"""
        return {
            cls.FAILED,
            cls.TIMEOUT,
            cls.STOPPED,
            cls.CANCELLED,
            cls.ORPHANED,
            cls.DEGRADED,
        }
    
    def can_transition_to(self, target_status: "SessionStatus") -> bool:
        """
        Industrial-grade state transition validation
        
        Returns True if transition from current to target is valid
        """
        transition_map: Dict[SessionStatus, Set[SessionStatus]] = {
            # From PENDING
            SessionStatus.PENDING: {
                SessionStatus.QUEUED,     # Scheduled for execution
                SessionStatus.CANCELLED,  # Cancelled before queueing
                SessionStatus.FAILED,     # Immediate failure (e.g., validation)
            },
            
            # From QUEUED
            SessionStatus.QUEUED: {
                SessionStatus.RUNNING,    # Execution started
                SessionStatus.CANCELLED,  # Cancelled while queued
                SessionStatus.FAILED,     # Pre-execution failure
            },
            
            # From RUNNING
            SessionStatus.RUNNING: {
                SessionStatus.COMPLETED,          # Successful completion
                SessionStatus.PARTIALLY_COMPLETED, # Partial success
                SessionStatus.FAILED,             # Execution failure
                SessionStatus.TIMEOUT,            # Exceeded time limit
                SessionStatus.PAUSED,             # Manually paused
                SessionStatus.STOPPED,            # Manually stopped
                SessionStatus.DEGRADED,           # Running with issues
            },
            
            # From PAUSED
            SessionStatus.PAUSED: {
                SessionStatus.RUNNING,    # Resumed execution
                SessionStatus.STOPPED,    # Stopped while paused
                SessionStatus.CANCELLED,  # Cancelled while paused
            },
            
            # From DEGRADED
            SessionStatus.DEGRADED: {
                SessionStatus.RUNNING,    # Recovered to normal
                SessionStatus.FAILED,     # Degraded further to failure
                SessionStatus.COMPLETED,  # Managed to complete despite issues
                SessionStatus.STOPPED,    # Manually stopped
            },
            
            # From PARTIALLY_COMPLETED (can sometimes be recovered)
            SessionStatus.PARTIALLY_COMPLETED: {
                SessionStatus.RUNNING,    # Retry failed sub-tasks
                SessionStatus.COMPLETED,  # All sub-tasks eventually succeeded
            },
            
            # Terminal states - no transitions allowed
            **{state: set() for state in cls.get_terminal_states()},
        }
        
        return target_status in transition_map.get(self, set())
    
    def is_terminal(self) -> bool:
        """Check if status is terminal (no further transitions)"""
        return self in self.get_terminal_states()
    
    def is_active(self) -> bool:
        """Check if status indicates active processing"""
        return self in self.get_active_states()
    
    def is_error(self) -> bool:
        """Check if status indicates an error condition"""
        return self in self.get_error_states()
    
    def get_emoji(self) -> str:
        """Industrial visualization via emoji (for dashboard)"""
        emoji_map = {
            SessionStatus.PENDING: "⏳",
            SessionStatus.QUEUED: "📋",
            SessionStatus.RUNNING: "⚙️",
            SessionStatus.PAUSED: "⏸️",
            SessionStatus.COMPLETED: "✅",
            SessionStatus.PARTIALLY_COMPLETED: "⚠️",
            SessionStatus.FAILED: "❌",
            SessionStatus.TIMEOUT: "⏰",
            SessionStatus.STOPPED: "🛑",
            SessionStatus.CANCELLED: "🚫",
            SessionStatus.ORPHANED: "🧩",
            SessionStatus.DEGRADED: "🔻",
        }
        return emoji_map.get(self, "❓")
    
    def get_color_code(self) -> str:
        """Color coding for industrial dashboard"""
        color_map = {
            SessionStatus.PENDING: "#6B7280",      # Gray
            SessionStatus.QUEUED: "#3B82F6",       # Blue
            SessionStatus.RUNNING: "#10B981",      # Green
            SessionStatus.PAUSED: "#F59E0B",       # Yellow
            SessionStatus.COMPLETED: "#059669",    # Dark green
            SessionStatus.PARTIALLY_COMPLETED: "#D97706", # Amber
            SessionStatus.FAILED: "#DC2626",       # Red
            SessionStatus.TIMEOUT: "#7C3AED",      # Purple
            SessionStatus.STOPPED: "#4B5563",      # Dark gray
            SessionStatus.CANCELLED: "#374151",    # Darker gray
            SessionStatus.ORPHANED: "#9333EA",     # Violet
            SessionStatus.DEGRADED: "#F97316",     # Orange
        }
        return color_map.get(self, "#000000")
