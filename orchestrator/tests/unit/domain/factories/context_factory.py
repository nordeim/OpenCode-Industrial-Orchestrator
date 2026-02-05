"""
INDUSTRIAL CONTEXT TEST FACTORY
Generates realistic context test data with scopes and merge scenarios.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

import factory
from factory import LazyFunction, LazyAttribute

from src.industrial_orchestrator.domain.entities.context import (
    ContextEntity,
    ContextScope,
    MergeStrategy,
)


class ContextEntityFactory(factory.Factory):
    """Industrial-grade factory for ContextEntity"""

    class Meta:
        model = ContextEntity

    # Identity
    id = LazyFunction(uuid4)
    tenant_id = LazyFunction(uuid4)
    session_id = LazyFunction(uuid4)
    agent_id = None
    scope = ContextScope.SESSION

    # Data
    data = LazyFunction(
        lambda: {
            "project": {"name": "test-project", "version": "1.0.0"},
            "config": {"debug": True, "timeout": 30},
        }
    )

    # Version and timestamps
    version = 1
    created_at = LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = LazyFunction(lambda: datetime.now(timezone.utc))
    created_by = "factory"

    # Metadata
    metadata = factory.Dict({})

    class Params:
        """Factory variants"""

        # Global scope context
        global_scope = factory.Trait(
            scope=ContextScope.GLOBAL,
            agent_id=None,
            session_id=None,
        )

        # Agent scope context
        agent_scope = factory.Trait(
            scope=ContextScope.AGENT,
            agent_id=LazyFunction(uuid4),
        )

        # Temporary scope context
        temp_scope = factory.Trait(
            scope=ContextScope.TEMPORARY,
            data={"temp_key": "temp_value"},
        )

        # With rich nested data (use LazyFunction to prevent mutation)
        nested = factory.Trait(
            data=LazyFunction(
                lambda: {
                    "level1": {
                        "level2": {
                            "level3": {"deep_value": "found"},
                        },
                        "sibling": "value",
                    },
                    "top": "level",
                }
            ),
        )

        # With history
        with_history = factory.Trait(
            version=5,
        )


def create_conflicting_contexts() -> tuple:
    """Create two contexts with conflicting values for merge testing."""
    tenant_id = uuid4()
    session_id = uuid4()
    base_time = datetime.now(timezone.utc)

    ctx1 = ContextEntity(
        tenant_id=tenant_id,
        session_id=session_id,
        scope=ContextScope.SESSION,
        data={
            "shared": "value_from_ctx1",
            "only_in_ctx1": "unique1",
            "nested": {"key": "ctx1_nested"},
        },
        created_at=base_time,
        updated_at=base_time,
    )

    ctx2 = ContextEntity(
        tenant_id=tenant_id,
        session_id=session_id,
        scope=ContextScope.SESSION,
        data={
            "shared": "value_from_ctx2",
            "only_in_ctx2": "unique2",
            "nested": {"key": "ctx2_nested", "extra": "new"},
        },
        created_at=base_time + timedelta(seconds=10),
        updated_at=base_time + timedelta(seconds=10),
    )

    return ctx1, ctx2
