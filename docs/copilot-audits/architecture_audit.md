# Architecture Audit — DayZ Sentinel

**Date:** 2026-06-17  
**Scope:** Architecture, design patterns, and structural concerns  
**Auditor:** Copilot Coding Agent

---

## Summary

| ID | Category | Severity | Status |
|----|----------|----------|--------|
| ARCH-001 | Package Naming | 🟡 Medium | Open |
| ARCH-002 | Connection Management | 🟠 High | Open |
| ARCH-003 | Schema / Code Mismatch | 🟡 Medium | Open |
| ARCH-004 | Missing Import Pipeline | 🟡 Medium | Open |
| ARCH-005 | No Migration Strategy | 🟡 Medium | Open |
| ARCH-006 | Pydantic Models Unused in Repositories | 🔵 Low | Open |

---

## ARCH-001 · Package Name Tightly Coupled to Sprint Number

**Severity:** 🟡 Medium  
**Files:** `Dockerfile:6`, `docker-compose.yml:8`, all `from sentinel_spr019.*` imports

The module is named `sentinel_spr019`. Every sprint that renames this breaks:
- Docker CMD
- Docker volume path
- All internal imports (10+ files)
- CasaOS deployment instructions

**Recommendation:**  
Rename package to `sentinel` once. Update `Dockerfile`, `docker-compose.yml`, and all imports in a single commit. Use a sprint number only in branch/PR names, not in package names.

---

## ARCH-002 · Database Connections Not Managed Safely

**Severity:** 🟠 High  
**Files:**
- `economy_items_repository.py` — 4 methods, all open connections manually
- `economy_events_repository.py` — 5 methods, all open connections manually
- `economy_repository.py` — 1 method

**Current Pattern:**
```python
conn = get_connection()
# ... operations ...
conn.close()  # skipped if exception occurs
```

**Recommended Pattern:**
```python
# database.py
from contextlib import contextmanager

@contextmanager
def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    try:
        yield conn
    finally:
        conn.close()

# Repository usage:
with get_connection() as conn:
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    # ... safely closed even on exception
```

---

## ARCH-003 · Schema File vs. Active Column Name Mismatch

**Severity:** 🟡 Medium  
**Files:** `database/schema/sentinel_v1_schema.sql:5`, `api/repositories/economy_items_repository.py:33`

Schema v1 (`sentinel_v1_schema.sql`) defines:
```sql
CREATE TABLE IF NOT EXISTS economy_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL UNIQUE,   -- column: item_name
    ...
```

But the repository queries:
```python
SELECT name, nominal, min_value, max_value, restock, lifetime FROM economy_items
#       ^^^^  -- queries column: name (not item_name)
```

This means the live `sentinel.db` was created with a different schema than what is in `sentinel_v1_schema.sql`. The schema file does not accurately represent the real database.

**Recommendation:**
1. Run `.schema economy_items` on the live DB to get the actual column definition
2. Update `sentinel_v1_schema.sql` to match
3. Consider adding a schema validation step to the startup routine

---

## ARCH-004 · `types_importer.py` Missing

**Severity:** 🟡 Medium  
**File:** `sentinel_spr019/scripts/test_import_run.py:4`

```python
from importer.economy.types_importer import import_types
```

`types_importer.py` does not exist. The economy items table (`economy_items`, 1,917 rows) was populated externally, with no reproducible import script in the repository. This means:
- The database cannot be rebuilt from source
- New deployments require importing the SQLite file manually

**Recommendation:** Implement `types_importer.py` analogous to `events_importer.py`, parsing `types.xml` and inserting into `economy_items`.

---

## ARCH-005 · No Schema Migration Strategy

**Severity:** 🟡 Medium  
**Files:** `database/schema/sentinel_v1_schema.sql`, `sentinel_v1_schema_rev2.sql`

Two schema files exist but there is no runner that applies them in order, checks current schema version, or handles upgrades. On a fresh deployment both files must be applied manually in the correct sequence.

**Recommendation:**
Option A (minimal): Add a `db_init.py` script that applies both files idempotently on startup.  
Option B (proper): Integrate Alembic for versioned migrations.

---

## ARCH-006 · Pydantic Models Imported but Not Used

**Severity:** 🔵 Low  
**Files:** `economy_items_repository.py:2`, `economy_events_repository.py:2`

```python
from sentinel_spr019.api.models.economy_item import EconomyItem, EconomyItemResponse
# ↑ Neither is used — repositories return plain dict
```

The repository layer bypasses the type system entirely. This means return types are unvalidated and IDE auto-complete doesn't work for repository consumers.

**Recommendation:** Repositories should return typed Pydantic models:
```python
def get_by_name(name: str) -> Optional[EconomyItemResponse]:
    ...
    row = cursor.fetchone()
    return EconomyItemResponse(**row) if row else None
```

---

## Architecture Strengths

| Aspect | Assessment |
|--------|-----------|
| Layer separation (Routes → Repositories → DB) | ✅ Good |
| Pydantic schema definitions | ✅ Good foundation |
| Docker containerization | ✅ Production-ready setup |
| SQLite volume mount for persistence | ✅ Correct approach |
| FastAPI with OpenAPI docs auto-generation | ✅ Developer-friendly |

---

*Audit completed: 2026-06-17*
