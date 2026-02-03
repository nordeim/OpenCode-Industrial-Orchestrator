class SessionError(Exception):
    """Base session error"""
    pass

class InvalidSessionTransition(SessionError):
    def __init__(self, current_status, target_status, session_id, reason=None):
        self.current_status = current_status
        self.target_status = target_status
        self.session_id = session_id
        self.reason = reason
        super().__init__(f"Invalid transition from {current_status} to {target_status} for session {session_id}: {reason}")

class SessionNotFoundError(SessionError):
    pass

class SessionTimeoutError(SessionError):
    pass
