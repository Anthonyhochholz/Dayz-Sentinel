# Code Quality Audit — DayZ Sentinel

**Date:** 2026-06-17  
**Scope:** Code quality, maintainability, correctness  
**Auditor:** Copilot Coding Agent

---

## Summary

| ID | Category | Severity | Status |
|----|----------|----------|--------|
| CQ-001 | Code Duplication | 🟡 Medium | Open |
| CQ-002 | Dead Code | 🟡 Medium | Open |
| CQ-003 | Missing Dependency | 🟡 Medium | Open |
| CQ-004 | Pagination Bug (Search) | 🟡 Medium | Open |
| CQ-005 | Unpinned Dependencies | 🟡 Medium | Open |
| CQ-006 | Documentation Mismatch | 🔵 Low | Open |
| CQ-007 | Response Model Typing | 🔵 Low | Open |

---

## CQ-001 · Duplicated `dict_factory` Function

**Severity:** 🟡 Medium  
**Files:**
- `economy_items_repository.py:128-131`
- `economy_events_repository.py:177-180`

```python
# Identical in both files:
def dict_factory(cursor, row):
    """Convert database rows to dictionaries"""
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}
```

**Fix:** Move to `database.py`, import in both repositories:
```python
# database.py
def dict_factory(cursor, row):
    return {col[0]: val for col, val in zip(cursor.description, row)}

# repositories:
from sentinel_spr019.api.database import get_connection, dict_factory
```

---

## CQ-002 · Dead Code

**Severity:** 🟡 Medium

### economy_repository.py (entire file)
**File:** `economy_repository.py:1-11`

```python
class EconomyRepository:
    def get_items(self, limit=100):
        ...
```
This class is never imported or used anywhere. It is a superseded prototype.

**Fix:** Delete the file.

### Unused Model Imports in Repositories
**Files:** `economy_items_repository.py:2`, `economy_events_repository.py:2`

```python
# economy_items_repository.py:2
from sentinel_spr019.api.models.economy_item import EconomyItem, EconomyItemResponse
# Both are imported but never referenced in this file

# economy_events_repository.py:2
from sentinel_spr019.api.models.economy_event import EconomyEvent, EconomyEventResponse
# Both are imported but never referenced in this file
```

**Fix:** Remove unused imports, or use the models as return types (see ARCH-006).

---

## CQ-003 · Missing Package in `requirements.txt`

**Severity:** 🟡 Medium  
**Files:** `requirements.txt:1-2`, `scripts/test_api.py:8`

```
# requirements.txt (complete):
fastapi
uvicorn[standard]
```

```python
# test_api.py:8
import requests   # package not listed
```

`docker build` does not install `requests`, causing `ModuleNotFoundError` when running tests inside the container.

**Fix:**
```
fastapi
uvicorn[standard]
requests
```

---

## CQ-004 · `offset` Parameter Ignored in Search Endpoints

**Severity:** 🟡 Medium  
**Files:** `routes/economy_items.py:25-33`, `repositories/economy_items_repository.py:79-110`

**Route accepts `offset`:**
```python
# economy_items.py:11-13
async def get_items(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),     # ← accepted
    search: Optional[str] = Query(None)
):
    if search:
        items = EconomyItemsRepository.search(search, limit)
        return {
            "offset": offset,   # ← included in response
            ...
        }
```

**Repository ignores `offset`:**
```python
# economy_items_repository.py:79
def search(query: str, limit: int = 50) -> List[dict]:
    # no offset parameter, no OFFSET in SQL
```

Same pattern in `economy_events_repository.py:85`.

**Fix:** Add `offset: int = 0` to `search()` signatures and `OFFSET ?` to SQL queries.

---

## CQ-005 · Unpinned Dependencies

**Severity:** 🟡 Medium  
**File:** `requirements.txt:1-2`

```
fastapi
uvicorn[standard]
```

No version pinning means `docker build` installs the latest available versions. A breaking release of FastAPI or Pydantic v2 (which FastAPI may pick up) can silently break the build.

**Fix:**
```
fastapi==0.115.0
uvicorn[standard]==0.30.6
requests==2.32.3
```
Pin to currently known-good versions; update deliberately.

---

## CQ-006 · README Documents Incorrect Endpoints

**Severity:** 🔵 Low  
**File:** `README.md:75-77, 88`

| README Claims | Actual Implementation |
|---|---|
| `GET /health` | `GET /api/v1/health` |
| Response: `{"status": "operational"}` | Response: `{"status": "ok"}` |
| `?type=weapon` filter | Parameter does not exist |

**Fix:** Update README to reflect actual route paths and response shapes.

---

## CQ-007 · Route Response Types Declared as `dict`

**Severity:** 🔵 Low  
**Files:** `routes/economy_items.py:9,46,69`, `routes/economy_events.py:9,50,73,95`

```python
@router.get("/items", response_model=dict)   # ← loses OpenAPI schema
@router.get("/items/{item_name}", response_model=dict)
```

Declaring `response_model=dict` disables automatic OpenAPI response schema generation. The `/docs` UI shows no response body schema for any endpoint.

**Fix:** Define proper response wrapper models:
```python
class PaginatedItemsResponse(BaseModel):
    data: List[EconomyItemResponse]
    total: int
    limit: int
    offset: int

@router.get("/items", response_model=PaginatedItemsResponse)
```

---

## Code Quality Strengths

| Aspect | Assessment |
|--------|-----------|
| Docstrings on all public methods | ✅ Good |
| Repository pattern applied consistently | ✅ Good |
| Input validation via FastAPI `Query()` with bounds | ✅ Good |
| Separate model files per domain object | ✅ Good |
| Static methods in repositories (no unnecessary state) | ✅ Appropriate |

---

*Audit completed: 2026-06-17*
