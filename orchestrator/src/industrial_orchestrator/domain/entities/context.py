"""
INDUSTRIAL CONTEXT ENTITY
Domain entity for execution context management with scope-based access control.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from enum import Enum
import copy
from pydantic import Field, ConfigDict

from .base import DomainEntity


class ContextScope(str, Enum):
    """
    Scope levels for context visibility and lifecycle.
    """
    SESSION = "session"
    AGENT = "agent"
    GLOBAL = "global"
    TEMPORARY = "temporary"


class MergeStrategy(str, Enum):
    """Strategy for merging contexts with conflicts."""
    LAST_WRITE_WINS = "last_write_wins"
    DEEP_MERGE = "deep_merge"
    MANUAL = "manual"
    PREFER_SOURCE = "prefer_source"
    PREFER_TARGET = "prefer_target"


class ContextChange(DomainEntity):
    """Record of a single context change."""
    key: str
    old_value: Any
    new_value: Any
    changed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    changed_by: Optional[str] = None


class ContextDiff(DomainEntity):
    """
    Difference between two contexts.
    """
    added: Dict[str, Any] = Field(default_factory=dict)
    modified: Dict[str, tuple] = Field(default_factory=dict)  # key -> (old, new)
    deleted: Dict[str, Any] = Field(default_factory=dict)
    conflicts: List[str] = Field(default_factory=list)
    
    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.modified or self.deleted)
    
    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)
    
    def __len__(self) -> int:
        return len(self.added) + len(self.modified) + len(self.deleted)


class ContextEntity(DomainEntity):
    """
    Industrial-grade execution context for orchestration.
    """
    
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID = Field(...)  # Required for isolation
    session_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    scope: ContextScope = ContextScope.SESSION
    data: Dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Audit trail (private field in pydantic)
    _change_history: List[ContextChange] = []
    _max_history: int = 100
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from context supporting dot notation."""
        keys = key.split('.')
        value = self.data
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def set(
        self,
        key: str,
        value: Any,
        changed_by: Optional[str] = None
    ) -> None:
        """Set value in context with versioning and history."""
        keys = key.split('.')
        old_value = self.get(key)
        
        # Navigate to parent
        current = self.data
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        # Set the value
        current[keys[-1]] = value
        
        # Record change
        self._record_change(key, old_value, value, changed_by)
        
        # Update version and timestamp
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
    
    def delete(
        self,
        key: str,
        changed_by: Optional[str] = None
    ) -> bool:
        """Delete value from context."""
        keys = key.split('.')
        old_value = self.get(key)
        
        if old_value is None:
            return False
        
        # Navigate to parent
        current = self.data
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                return False
            current = current[k]
        
        # Delete the key
        if keys[-1] in current:
            del current[keys[-1]]
            self._record_change(key, old_value, None, changed_by)
            self.version += 1
            self.updated_at = datetime.now(timezone.utc)
            return True
        
        return False
    
    def diff(self, other: "ContextEntity") -> ContextDiff:
        """Calculate difference between this context and another."""
        diff = ContextDiff()
        
        self_keys = set(self.all_keys())
        other_keys = set(other.all_keys())
        
        for key in other_keys - self_keys:
            diff.added[key] = other.get(key)
        
        for key in self_keys - other_keys:
            diff.deleted[key] = self.get(key)
        
        for key in self_keys & other_keys:
            self_val = self.get(key)
            other_val = other.get(key)
            if self_val != other_val:
                diff.modified[key] = (self_val, other_val)
        
        return diff

    def all_keys(self, prefix: str = "") -> List[str]:
        """Get all keys including nested."""
        result = []
        
        def _flatten(d: Dict, parent: str = ""):
            for k, v in d.items():
                full_key = f"{parent}.{k}" if parent else k
                result.append(full_key)
                if isinstance(v, dict):
                    _flatten(v, full_key)
        
        _flatten(self.data, prefix)
        return result

    def merge(
        self,
        other: "ContextEntity",
        strategy: MergeStrategy = MergeStrategy.LAST_WRITE_WINS
    ) -> "ContextEntity":
        """Merge another context into this one."""
        if self.tenant_id != other.tenant_id:
            raise ValueError("Cannot merge contexts from different tenants")

        merged_data = copy.deepcopy(self.data)
        conflicts = []
        
        if strategy == MergeStrategy.LAST_WRITE_WINS:
            merged_data = self._deep_merge_dicts(merged_data, other.data, prefer_other=True)
        elif strategy == MergeStrategy.DEEP_MERGE:
            merged_data = self._deep_merge_dicts(merged_data, other.data, prefer_other=False)
        elif strategy == MergeStrategy.PREFER_SOURCE:
            merged_data = self._deep_merge_dicts(merged_data, other.data, prefer_other=True)
        elif strategy == MergeStrategy.PREFER_TARGET:
            merged_data = self._deep_merge_dicts(other.data.copy(), merged_data, prefer_other=True)
        elif strategy == MergeStrategy.MANUAL:
            diff = self.diff(other)
            conflicts = list(diff.modified.keys())
            merged_data = self._deep_merge_dicts(merged_data, other.data, prefer_other=True)
        
        return ContextEntity(
            tenant_id=self.tenant_id,
            session_id=self.session_id or other.session_id,
            agent_id=self.agent_id or other.agent_id,
            scope=self._determine_merged_scope(other),
            data=merged_data,
            metadata={
                "merged_from": [str(self.id), str(other.id)],
                "merge_strategy": strategy.value,
                "conflicts": conflicts,
            }
        )

    def has(self, key: str) -> bool:
        """Check if key exists in context."""
        return self.get(key) is not None

    def keys(self) -> List[str]:
        """Get top-level keys."""
        return list(self.data.keys())

    def clone(self, new_scope: Optional[ContextScope] = None) -> "ContextEntity":
        """Create a deep copy of this context."""
        return ContextEntity(
            tenant_id=self.tenant_id,
            session_id=self.session_id,
            agent_id=self.agent_id,
            scope=new_scope or self.scope,
            data=copy.deepcopy(self.data),
            metadata={
                **copy.deepcopy(self.metadata),
                "cloned_from": str(self.id)
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextEntity":
        """Create from dictionary."""
        return cls.model_validate(data)

    def get_recent_changes(self, count: int = 10) -> List[ContextChange]:
        """Get recent change history."""
        return self._change_history[-count:]

    def _record_change(self, key: str, old_value: Any, new_value: Any, changed_by: Optional[str]) -> None:
        change = ContextChange(
            key=key,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by
        )
        self._change_history.append(change)
        if len(self._change_history) > self._max_history:
            self._change_history = self._change_history[-self._max_history:]

    def _deep_merge_dicts(self, base: Dict, overlay: Dict, prefer_other: bool = True) -> Dict:
        result = copy.deepcopy(base)
        for key, value in overlay.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._deep_merge_dicts(result[key], value, prefer_other)
                elif prefer_other:
                    result[key] = copy.deepcopy(value)
            else:
                result[key] = copy.deepcopy(value)
        return result

    def _determine_merged_scope(self, other: "ContextEntity") -> ContextScope:
        scope_order = [ContextScope.TEMPORARY, ContextScope.SESSION, ContextScope.AGENT, ContextScope.GLOBAL]
        return scope_order[max(scope_order.index(self.scope), scope_order.index(other.scope))]