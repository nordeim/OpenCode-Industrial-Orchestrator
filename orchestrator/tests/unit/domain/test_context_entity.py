"""
INDUSTRIAL-GRADE CONTEXT ENTITY TESTS
Comprehensive TDD-style tests for context merge, diff, and conflict handling.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from src.industrial_orchestrator.domain.entities.context import (
    ContextEntity,
    ContextScope,
    MergeStrategy,
    ContextDiff,
    ContextChange,
)

from tests.unit.domain.factories.context_factory import (
    ContextEntityFactory,
    create_conflicting_contexts,
)


class TestContextEntityCreation:
    """Test context entity creation"""

    def test_create_minimal_context(self):
        """Test creating context with minimal fields"""
        ctx = ContextEntityFactory()

        assert ctx.id is not None
        assert ctx.session_id is not None
        assert ctx.scope == ContextScope.SESSION
        assert ctx.version == 1
        assert ctx.data is not None

    def test_create_global_context(self):
        """Test creating global scope context"""
        ctx = ContextEntityFactory(global_scope=True)

        assert ctx.scope == ContextScope.GLOBAL
        assert ctx.session_id is None
        assert ctx.agent_id is None

    def test_create_agent_context(self):
        """Test creating agent scope context"""
        ctx = ContextEntityFactory(agent_scope=True)

        assert ctx.scope == ContextScope.AGENT
        assert ctx.agent_id is not None


class TestContextGetSet:
    """Test context get/set operations"""

    def test_get_simple_key(self):
        """Test getting simple key"""
        ctx = ContextEntityFactory()
        ctx.data = {"key": "value"}

        assert ctx.get("key") == "value"

    def test_get_nested_key(self):
        """Test getting nested key with dot notation"""
        ctx = ContextEntityFactory(nested=True)

        assert ctx.get("level1.level2.level3.deep_value") == "found"

    def test_get_missing_key_returns_default(self):
        """Test missing key returns default"""
        ctx = ContextEntityFactory()

        assert ctx.get("nonexistent") is None
        assert ctx.get("nonexistent", "default") == "default"

    def test_set_simple_key(self):
        """Test setting simple key"""
        ctx = ContextEntityFactory()
        initial_version = ctx.version

        ctx.set("new_key", "new_value", changed_by="test")

        assert ctx.get("new_key") == "new_value"
        assert ctx.version == initial_version + 1

    def test_set_nested_key(self):
        """Test setting nested key creates hierarchy"""
        ctx = ContextEntity(tenant_id=uuid4(), session_id=uuid4(), data={})

        ctx.set("parent.child.grandchild", "deep")

        assert ctx.get("parent.child.grandchild") == "deep"
        assert isinstance(ctx.data["parent"]["child"], dict)

    def test_set_records_change(self):
        """Test that set records change in history"""
        ctx = ContextEntityFactory()

        ctx.set("tracked", "value", changed_by="tester")

        changes = ctx.get_recent_changes(1)
        assert len(changes) == 1
        assert changes[0].key == "tracked"
        assert changes[0].new_value == "value"
        assert changes[0].changed_by == "tester"


class TestContextDelete:
    """Test context delete operations"""

    def test_delete_existing_key(self):
        """Test deleting existing key"""
        ctx = ContextEntityFactory()
        ctx.data = {"to_delete": "value"}

        result = ctx.delete("to_delete")

        assert result is True
        assert ctx.has("to_delete") is False

    def test_delete_missing_key_returns_false(self):
        """Test deleting missing key returns False"""
        ctx = ContextEntityFactory()

        result = ctx.delete("nonexistent")

        assert result is False

    def test_delete_nested_key(self):
        """Test deleting nested key"""
        ctx = ContextEntityFactory(nested=True)

        result = ctx.delete("level1.level2.level3.deep_value")

        assert result is True
        assert ctx.get("level1.level2.level3.deep_value") is None


class TestContextKeys:
    """Test key enumeration"""

    def test_keys_returns_top_level(self):
        """Test keys returns top-level keys"""
        ctx = ContextEntityFactory()
        ctx.data = {"a": 1, "b": 2, "c": {"nested": 3}}

        keys = ctx.keys()

        assert set(keys) == {"a", "b", "c"}

    def test_all_keys_includes_nested(self):
        """Test all_keys includes nested keys"""
        ctx = ContextEntityFactory(nested=True)

        all_keys = ctx.all_keys()

        assert "level1" in all_keys
        assert "level1.level2" in all_keys
        assert "level1.level2.level3.deep_value" in all_keys

    def test_has_returns_true_for_existing(self):
        """Test has returns True for existing key"""
        ctx = ContextEntityFactory()
        ctx.set("exists", "yes")

        assert ctx.has("exists") is True

    def test_has_returns_false_for_missing(self):
        """Test has returns False for missing key"""
        ctx = ContextEntityFactory()

        assert ctx.has("missing") is False


class TestContextDiff:
    """Test context diff operations"""

    def test_diff_no_changes(self):
        """Test diff with identical contexts"""
        ctx1 = ContextEntityFactory()
        ctx2 = ctx1.clone()

        diff = ctx1.diff(ctx2)

        assert diff.has_changes is False
        assert len(diff) == 0

    def test_diff_additions(self):
        """Test diff detects additions"""
        tenant_id = uuid4()
        ctx1 = ContextEntity(tenant_id=tenant_id, session_id=uuid4(), data={"existing": 1})
        ctx2 = ContextEntity(tenant_id=tenant_id, session_id=uuid4(), data={"existing": 1, "added": 2})

        diff = ctx1.diff(ctx2)

        assert "added" in diff.added
        assert diff.added["added"] == 2

    def test_diff_deletions(self):
        """Test diff detects deletions"""
        tenant_id = uuid4()
        ctx1 = ContextEntity(tenant_id=tenant_id, session_id=uuid4(), data={"existing": 1, "removed": 2})
        ctx2 = ContextEntity(tenant_id=tenant_id, session_id=uuid4(), data={"existing": 1})

        diff = ctx1.diff(ctx2)

        assert "removed" in diff.deleted
        assert diff.deleted["removed"] == 2

    def test_diff_modifications(self):
        """Test diff detects modifications"""
        tenant_id = uuid4()
        ctx1 = ContextEntity(tenant_id=tenant_id, session_id=uuid4(), data={"key": "old"})
        ctx2 = ContextEntity(tenant_id=tenant_id, session_id=uuid4(), data={"key": "new"})

        diff = ctx1.diff(ctx2)

        assert "key" in diff.modified
        assert diff.modified["key"] == ("old", "new")


class TestContextMerge:
    """Test context merge operations"""

    def test_merge_last_write_wins(self):
        """Test merge with LAST_WRITE_WINS strategy"""
        ctx1, ctx2 = create_conflicting_contexts()

        merged = ctx1.merge(ctx2, MergeStrategy.LAST_WRITE_WINS)

        # ctx2 (other) values should win
        assert merged.get("shared") == "value_from_ctx2"
        assert merged.get("only_in_ctx1") == "unique1"
        assert merged.get("only_in_ctx2") == "unique2"

    def test_merge_prefer_source(self):
        """Test merge with PREFER_SOURCE strategy"""
        ctx1, ctx2 = create_conflicting_contexts()

        merged = ctx1.merge(ctx2, MergeStrategy.PREFER_SOURCE)

        assert merged.get("shared") == "value_from_ctx2"

    def test_merge_prefer_target(self):
        """Test merge with PREFER_TARGET strategy"""
        ctx1, ctx2 = create_conflicting_contexts()

        merged = ctx1.merge(ctx2, MergeStrategy.PREFER_TARGET)

        assert merged.get("shared") == "value_from_ctx1"

    def test_merge_deep_merge(self):
        """Test merge with DEEP_MERGE strategy"""
        ctx1, ctx2 = create_conflicting_contexts()

        merged = ctx1.merge(ctx2, MergeStrategy.DEEP_MERGE)

        # Nested obj should have keys from both
        assert merged.get("nested.extra") == "new"

    def test_merge_manual_records_conflicts(self):
        """Test merge with MANUAL strategy records conflicts"""
        ctx1, ctx2 = create_conflicting_contexts()

        merged = ctx1.merge(ctx2, MergeStrategy.MANUAL)

        assert "conflicts" in merged.metadata
        assert len(merged.metadata["conflicts"]) > 0

    def test_merge_creates_new_id(self):
        """Test merge creates new context ID"""
        ctx1, ctx2 = create_conflicting_contexts()

        merged = ctx1.merge(ctx2)

        assert merged.id != ctx1.id
        assert merged.id != ctx2.id

    def test_merge_records_source_ids(self):
        """Test merge records source IDs in metadata"""
        ctx1, ctx2 = create_conflicting_contexts()

        merged = ctx1.merge(ctx2)

        assert "merged_from" in merged.metadata
        assert str(ctx1.id) in merged.metadata["merged_from"]
        assert str(ctx2.id) in merged.metadata["merged_from"]


class TestContextClone:
    """Test context clone operations"""

    def test_clone_creates_deep_copy(self):
        """Test clone creates independent copy"""
        ctx = ContextEntityFactory(nested=True)

        cloned = ctx.clone()

        # Modify original
        ctx.set("level1.new", "added")

        # Clone should not be affected
        assert cloned.get("level1.new") is None

    def test_clone_with_new_scope(self):
        """Test clone can change scope"""
        ctx = ContextEntityFactory()

        cloned = ctx.clone(new_scope=ContextScope.GLOBAL)

        assert cloned.scope == ContextScope.GLOBAL
        assert ctx.scope == ContextScope.SESSION

    def test_clone_records_source(self):
        """Test clone records source in metadata"""
        ctx = ContextEntityFactory()

        cloned = ctx.clone()

        assert "cloned_from" in cloned.metadata
        assert cloned.metadata["cloned_from"] == str(ctx.id)


class TestContextSerialization:
    """Test context serialization"""

    def test_to_dict(self):
        """Test serialization to dict"""
        ctx = ContextEntityFactory()

        d = ctx.to_dict()

        assert "id" in d
        assert "scope" in d
        assert "data" in d
        assert d["scope"] == "session"

    def test_from_dict(self):
        """Test deserialization from dict"""
        original = ContextEntityFactory()
        d = original.to_dict()

        restored = ContextEntity.from_dict(d)

        assert restored.id == original.id
        assert restored.scope == original.scope
        assert restored.data == original.data

    def test_roundtrip(self):
        """Test serialization roundtrip"""
        original = ContextEntityFactory(nested=True)

        restored = ContextEntity.from_dict(original.to_dict())

        assert restored.get("level1.level2.level3.deep_value") == "found"


class TestContextChangeHistory:
    """Test change history tracking"""

    def test_changes_recorded(self):
        """Test changes are recorded in history"""
        ctx = ContextEntityFactory()

        ctx.set("key1", "value1", changed_by="user1")
        ctx.set("key2", "value2", changed_by="user2")

        changes = ctx.get_recent_changes(10)

        assert len(changes) == 2
        assert changes[0].key == "key1"
        assert changes[1].key == "key2"

    def test_history_limited(self):
        """Test history is limited to max size"""
        ctx = ContextEntity(tenant_id=uuid4(), session_id=uuid4(), data={})
        ctx._max_history = 5

        for i in range(10):
            ctx.set(f"key{i}", f"value{i}")

        changes = ctx.get_recent_changes(100)

        assert len(changes) == 5
        # Should have most recent changes
        assert changes[-1].key == "key9"


class TestContextScopeHandling:
    """Test scope-related behavior"""

    def test_merge_scope_promotion(self):
        """Test merged context gets most permissive scope"""
        tenant_id = uuid4()
        session_ctx = ContextEntityFactory(tenant_id=tenant_id)
        global_ctx = ContextEntityFactory(tenant_id=tenant_id, global_scope=True)
    
        merged = session_ctx.merge(global_ctx)
        # GLOBAL is more permissive than SESSION
        assert merged.scope == ContextScope.GLOBAL


class TestContextFactory:
    """Test factory integration"""

    def test_factory_creates_valid_context(self):
        """Test factory produces valid entities"""
        ctx = ContextEntityFactory()

        assert isinstance(ctx, ContextEntity)
        assert ctx.id is not None
        assert ctx.scope in ContextScope

    def test_factory_variants(self):
        """Test factory variants"""
        session = ContextEntityFactory()
        assert session.scope == ContextScope.SESSION

        global_ctx = ContextEntityFactory(global_scope=True)
        assert global_ctx.scope == ContextScope.GLOBAL

        agent_ctx = ContextEntityFactory(agent_scope=True)
        assert agent_ctx.scope == ContextScope.AGENT
        assert agent_ctx.agent_id is not None

    def test_create_conflicting_contexts(self):
        """Test conflicting context generator"""
        ctx1, ctx2 = create_conflicting_contexts()

        assert ctx1.session_id == ctx2.session_id
        assert ctx1.get("shared") != ctx2.get("shared")
