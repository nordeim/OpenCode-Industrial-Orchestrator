# Session Entity Test Fixes - Implementation Plan

## Issue Categories

### Category 1: SessionStatus `cls` NameError (HIGH PRIORITY)
**Affects:** ~15 tests (all state transition tests)
**Root Cause:** Line 131 of `session_status.py` uses `cls` in a dict comprehension inside an instance method, but `cls` is only available in `@classmethod` methods.

```python
# Current (broken)
**{state: set() for state in cls.get_terminal_states()},  # NameError

# Fix
**{state: set() for state in SessionStatus.get_terminal_states()},
```

**File:** `src/industrial_orchestrator/domain/value_objects/session_status.py`

---

### Category 2: Test Assertion Mismatches (MEDIUM PRIORITY)
**Affects:** 2 tests
**Root Cause:** Tests expect `ValueError` with "generic" regex, but Pydantic V2 raises `ValidationError`

**File:** `tests/unit/domain/test_session_entity.py`
**Fix:** Update test to catch both or match actual error message

---

### Category 3: Factory/Test Issues (MEDIUM PRIORITY)
**Remaining tests:** ~5 tests
- `test_default_agent_config_when_empty`
- `test_checkpoint_rotation`
- `test_create_session_with_dependencies`
- `test_concurrent_state_transitions`
- `test_metrics_integration`

**Approach:** Fix individually after Category 1 is resolved

---

## Execution Order

1. [ ] Fix `cls` → `SessionStatus` in session_status.py (line 131)
2. [ ] Run tests to verify transition tests now pass
3. [ ] Fix test assertions in test_invalid_titles_rejected
4. [ ] Address remaining factory/test-specific issues
5. [ ] Final verification run

---

## Files to Modify

| File | Change |
|------|--------|
| `session_status.py` | Replace `cls` with `SessionStatus` |
| `test_session_entity.py` | Update exception matching |
