from pydantic import BaseModel
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from ..value_objects.session_status import SessionStatus

class DomainEvent(BaseModel):
    timestamp: datetime

class SessionCreated(DomainEvent):
    session_id: UUID
    title: str
    session_type: Any # SessionType
    created_by: Optional[str]

class SessionStatusChanged(DomainEvent):
    session_id: UUID
    old_status: Any # SessionStatus
    new_status: Any # SessionStatus

class SessionCompleted(DomainEvent):
    session_id: UUID
    result: Dict[str, Any]
    success_rate: float
    execution_duration_seconds: Optional[float]

class SessionFailed(DomainEvent):
    session_id: UUID
    error_type: str
    error_message: str
    error_context: Dict[str, Any]
    retryable: bool
