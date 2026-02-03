"""
INDUSTRIAL CONTEXT ENTITY
Domain entity for execution context management with scope-based access control.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from enum import Enum
import copy


class ContextScope(str, Enum):
    """
    Scope levels for context visibility and lifecycle.
    
    Industrial Design:
    - SESSION: Tied to single session, cleaned on session end
    - AGENT: Tied to agent instance, persists across sessions
    - GLOBAL: Shared across all sessions and agents
    - TEMPORARY: Short-lived, auto-cleanup after TTL
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


@dataclass
class ContextChange:
    """Record of a single context change."""
    key: str
    old_value: Any
    new_value: Any
    changed_at: datetime = field(default_factory=datetime.utcnow)
    changed_by: Optional[str] = None


@dataclass
class ContextDiff:
    """
    Difference between two contexts.
    
    Industrial Features:
    - Tracks additions, modifications, deletions
    - Records conflict points
    - Provides merge suggestions
    """
    added: Dict[str, Any] = field(default_factory=dict)
    modified: Dict[str, tuple] = field(default_factory=dict)  # key -> (old, new)
    deleted: Dict[str, Any] = field(default_factory=dict)
    conflicts: List[str] = field(default_factory=list)
    
    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.modified or self.deleted)
    
    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)
    
    def __len__(self) -> int:
        return len(self.added) + len(self.modified) + len(self.deleted)


@dataclass
class ContextEntity:
    """
    Industrial-grade execution context for orchestration.
    
    Stores key-value data with:
    1. Scope-based visibility
    2. Version tracking for optimistic locking
    3. Audit trail of changes
    4. Conflict detection and resolution
    
    Industrial Design:
    - Context is immutable-ish: updates create new versions
    - Merge operations support multiple strategies
    - Full audit trail for debugging
    """
    
    id: UUID = field(default_factory=uuid4)
    session_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    scope: ContextScope = ContextScope.SESSION
    data: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Audit trail (limited to recent changes in memory)
    _change_history: List[ContextChange] = field(default_factory=list, repr=False)
    _max_history: int = field(default=100, repr=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from context.
        
        Supports nested access via dot notation: 'parent.child.value'
        
        Args:
            key: Key to retrieve (supports dot notation)
            default: Default if not found
            
        Returns:
            Value or default
        """
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
        """
        Set value in context.
        
        Supports nested access via dot notation.
        Records change in history and increments version.
        
        Args:
            key: Key to set (supports dot notation)
            value: Value to set
            changed_by: Identifier of who made the change
        """
        keys = key.split('.')
        old_value = self.get(key)
        
        # Navigate to parent, creating intermediate dicts if needed
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
        self.updated_at = datetime.utcnow()
    
    def delete(
        self,
        key: str,
        changed_by: Optional[str] = None
    ) -> bool:
        """
        Delete value from context.
        
        Args:
            key: Key to delete (supports dot notation)
            changed_by: Identifier of who made the change
            
        Returns:
            True if deleted, False if not found
        """
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
            self.updated_at = datetime.utcnow()
            return True
        
        return False
    
    def has(self, key: str) -> bool:
        """Check if key exists in context."""
        return self.get(key) is not None
    
    def keys(self) -> List[str]:
        """Get all top-level keys."""
        return list(self.data.keys())
    
    def all_keys(self, prefix: str = "") -> List[str]:
        """Get all keys including nested (flattened with dot notation)."""
        result = []
        
        def _flatten(d: Dict, parent: str = ""):
            for k, v in d.items():
                full_key = f"{parent}.{k}" if parent else k
                result.append(full_key)
                if isinstance(v, dict):
                    _flatten(v, full_key)
        
        _flatten(self.data, prefix)
        return result
    
    def diff(self, other: "ContextEntity") -> ContextDiff:
        """
        Calculate difference between this context and another.
        
        Args:
            other: Context to compare against
            
        Returns:
            ContextDiff with added, modified, deleted keys
        """
        diff = ContextDiff()
        
        self_keys = set(self.all_keys())
        other_keys = set(other.all_keys())
        
        # Find additions (in other but not self)
        for key in other_keys - self_keys:
            diff.added[key] = other.get(key)
        
        # Find deletions (in self but not other)
        for key in self_keys - other_keys:
            diff.deleted[key] = self.get(key)
        
        # Find modifications (in both but different)
        for key in self_keys & other_keys:
            self_val = self.get(key)
            other_val = other.get(key)
            if self_val != other_val:
                diff.modified[key] = (self_val, other_val)
        
        return diff
    
    def merge(
        self,
        other: "ContextEntity",
        strategy: MergeStrategy = MergeStrategy.LAST_WRITE_WINS
    ) -> "ContextEntity":
        """
        Merge another context into this one.
        
        Args:
            other: Context to merge from
            strategy: Merge strategy for conflicts
            
        Returns:
            New merged ContextEntity
        """
        # Create a deep copy for the result
        merged_data = copy.deepcopy(self.data)
        conflicts = []
        
        if strategy == MergeStrategy.LAST_WRITE_WINS:
            # Other's values override
            merged_data = self._deep_merge_dicts(merged_data, other.data, prefer_other=True)
        
        elif strategy == MergeStrategy.DEEP_MERGE:
            # Recursive merge, keeping both where possible
            merged_data = self._deep_merge_dicts(merged_data, other.data, prefer_other=False)
        
        elif strategy == MergeStrategy.PREFER_SOURCE:
            # Other (source) values win
            merged_data = self._deep_merge_dicts(merged_data, other.data, prefer_other=True)
        
        elif strategy == MergeStrategy.PREFER_TARGET:
            # Self (target) values win
            merged_data = self._deep_merge_dicts(other.data.copy(), merged_data, prefer_other=True)
        
        elif strategy == MergeStrategy.MANUAL:
            # Mark conflicts for manual resolution
            diff = self.diff(other)
            conflicts = list(diff.modified.keys())
            merged_data = self._deep_merge_dicts(merged_data, other.data, prefer_other=True)
        
        # Create new merged context
        merged = ContextEntity(
            id=uuid4(),  # New ID for merged context
            session_id=self.session_id or other.session_id,
            agent_id=self.agent_id or other.agent_id,
            scope=self._determine_merged_scope(other),
            data=merged_data,
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={
                "merged_from": [str(self.id), str(other.id)],
                "merge_strategy": strategy.value,
                "conflicts": conflicts,
            }
        )
        
        return merged
    
    def clone(self, new_scope: Optional[ContextScope] = None) -> "ContextEntity":
        """
        Create a deep copy of this context.
        
        Args:
            new_scope: Optional new scope for the clone
            
        Returns:
            New ContextEntity with copied data
        """
        return ContextEntity(
            id=uuid4(),
            session_id=self.session_id,
            agent_id=self.agent_id,
            scope=new_scope or self.scope,
            data=copy.deepcopy(self.data),
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=self.created_by,
            metadata={"cloned_from": str(self.id)}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize context to dictionary."""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id) if self.session_id else None,
            "agent_id": str(self.agent_id) if self.agent_id else None,
            "scope": self.scope.value,
            "data": self.data,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ContextEntity":
        """Deserialize context from dictionary."""
        return cls(
            id=UUID(d["id"]) if d.get("id") else uuid4(),
            session_id=UUID(d["session_id"]) if d.get("session_id") else None,
            agent_id=UUID(d["agent_id"]) if d.get("agent_id") else None,
            scope=ContextScope(d.get("scope", "session")),
            data=d.get("data", {}),
            version=d.get("version", 1),
            created_at=datetime.fromisoformat(d["created_at"]) if d.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(d["updated_at"]) if d.get("updated_at") else datetime.utcnow(),
            created_by=d.get("created_by"),
            metadata=d.get("metadata", {}),
        )
    
    def get_recent_changes(self, limit: int = 10) -> List[ContextChange]:
        """Get recent changes from history."""
        return self._change_history[-limit:]
    
    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================
    
    def _record_change(
        self,
        key: str,
        old_value: Any,
        new_value: Any,
        changed_by: Optional[str]
    ) -> None:
        """Record a change in the history."""
        change = ContextChange(
            key=key,
            old_value=old_value,
            new_value=new_value,
            changed_at=datetime.utcnow(),
            changed_by=changed_by
        )
        self._change_history.append(change)
        
        # Trim history if needed
        if len(self._change_history) > self._max_history:
            self._change_history = self._change_history[-self._max_history:]
    
    def _deep_merge_dicts(
        self,
        base: Dict,
        overlay: Dict,
        prefer_other: bool = True
    ) -> Dict:
        """Deep merge two dictionaries."""
        result = copy.deepcopy(base)
        
        for key, value in overlay.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._deep_merge_dicts(result[key], value, prefer_other)
                elif prefer_other:
                    result[key] = copy.deepcopy(value)
                # If not prefer_other, keep result[key]
            else:
                result[key] = copy.deepcopy(value)
        
        return result
    
    def _determine_merged_scope(self, other: "ContextEntity") -> ContextScope:
        """Determine scope for merged context (most permissive wins)."""
        scope_order = [ContextScope.TEMPORARY, ContextScope.SESSION, ContextScope.AGENT, ContextScope.GLOBAL]
        self_idx = scope_order.index(self.scope)
        other_idx = scope_order.index(other.scope)
        return scope_order[max(self_idx, other_idx)]
