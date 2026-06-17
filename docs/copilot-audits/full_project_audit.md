# Full Project Audit — DayZ Sentinel

**Date:** 2026-06-17  
**Scope:** Complete codebase analysis  
**Auditor:** Copilot Coding Agent

---

## Executive Summary

DayZ Sentinel is a functional FastAPI REST API for DayZ server administration. The core economy features (items + events) are implemented and working. The project is containerized and deployable. However, 13 issues were identified spanning security, reliability, maintainability, and configuration correctness.

| Severity | Count |
|----------|-------|
| 🔴 Critical | 2 |
| 🟠 High | 3 |
| 🟡 Medium | 6 |
| 🔵 Low | 2 |
| **Total** | **13** |

---

## AUDIT-001 · No Authentication on Write Endpoint

| Field | Detail |
|-------|--------|
| **File** | `sentinel_spr019/api/routes/economy_events.py` |
| **Lines** | 73–75 |
| **Risk** | 🔴 Critical — Broken Access Control (OWASP A01) |

**Finding:**
```python
@router.post("/events/{event_name}/toggle-active", response_model=dict)
async def toggle_event_active(event_name: str):
```
No `Depends()` guard, no token validation. Any client on port 8000 can mutate server event state.

**Fix:** Add `FastAPI` API-Key dependency. See `security_audit.md` for full implementation.

---

## AUDIT-002 · Internal Error Details Leaked in HTTP 500 Responses

| Field | Detail |
|-------|--------|
| **Files** | `routes/economy_items.py:43,66,80` · `routes/economy_events.py:47,70,92,111` |
| **Risk** | 🔴 Critical — Information Disclosure (OWASP A05) |

**Finding:**
```python
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```
Exposes DB path, table names, SQLite error codes.

**Fix:** Log `e` server-side, return generic `"Internal server error"`.

---

## AUDIT-003 · Database Connection Leaks

| Field | Detail |
|-------|--------|
| **Files** | `economy_items_repository.py:22-45` · `economy_events_repository.py:22-50` · `economy_repository.py:4-11` |
| **Risk** | 🟠 High — Resource Leak |

**Finding:** `conn.close()` is called manually after queries, not in a `finally` block. Exceptions between open and close leave connections dangling.

**Fix:** Use `contextmanager` wrapper in `database.py`.

---

## AUDIT-004 · f-String SQL Interpolation

| Field | Detail |
|-------|--------|
| **File** | `economy_events_repository.py` |
| **Lines** | 30, 36–44, 107–113, 130 |
| **Risk** | 🟠 High — SQL Injection (OWASP A03) |

**Finding:**
```python
where_clause = "WHERE active = 1" if active_only else ""
cursor.execute(f"SELECT COUNT(*) as count FROM economy_events {where_clause}")
```
Pattern is exploitable if `active_only` handling is ever loosened.

**Fix:** Build clauses programmatically with lists and join; never interpolate user-derived strings.

---

## AUDIT-005 · `.env` File Never Read

| Field | Detail |
|-------|--------|
| **Files** | `.env.example:1-2` · `docker-compose.yml:6-7` · `Dockerfile:6` |
| **Risk** | 🟠 High — Configuration Failure |

**Finding:** `API_PORT=8000` in `.env.example` is never referenced. Port is hardcoded everywhere.

**Fix:** Use `env_file: .env` in `docker-compose.yml` and `${API_PORT:-8000}` in port bindings.

---

## AUDIT-006 · Duplicated `dict_factory` Function

| Field | Detail |
|-------|--------|
| **Files** | `economy_items_repository.py:128-131` · `economy_events_repository.py:177-180` |
| **Risk** | 🟡 Medium — Maintainability |

**Fix:** Define once in `database.py`, import in both repositories.

---

## AUDIT-007 · Dead Code

| Field | Detail |
|-------|--------|
| **Files** | `economy_repository.py:1-11` (entire file) · `economy_items_repository.py:2` · `economy_events_repository.py:2` |
| **Risk** | 🟡 Medium — Maintainability |

**Fix:** Delete `economy_repository.py`; remove unused model imports from repositories.

---

## AUDIT-008 · `requests` Missing from `requirements.txt`

| Field | Detail |
|-------|--------|
| **Files** | `requirements.txt:1-2` · `scripts/test_api.py:8` |
| **Risk** | 🟡 Medium — Build Failure |

**Fix:** Add `requests` to `requirements.txt`.

---

## AUDIT-009 · Broken Import in `test_import_run.py`

| Field | Detail |
|-------|--------|
| **File** | `scripts/test_import_run.py:4` |
| **Risk** | 🟡 Medium — Runtime Error |

**Finding:**
```python
from importer.economy.types_importer import import_types
# types_importer.py does not exist
```

**Fix:** Implement `types_importer.py` or remove the broken reference.

---

## AUDIT-010 · `offset` Ignored in Search Endpoints

| Field | Detail |
|-------|--------|
| **Files** | `routes/economy_items.py:25-33` · `repositories/economy_items_repository.py:79` |
| **Risk** | 🟡 Medium — Incorrect Behavior |

**Finding:** `offset` query param is accepted by route but not passed to `search()`.

**Fix:** Add `offset` parameter to `search()` and include `OFFSET ?` in the SQL.

---

## AUDIT-011 · Package Name Contains Sprint Number

| Field | Detail |
|-------|--------|
| **Files** | `Dockerfile:6` · `docker-compose.yml:8` · all `__init__.py` files |
| **Risk** | 🟡 Medium — Maintainability |

**Fix:** Rename `sentinel_spr019` → `sentinel`; update all references.

---

## AUDIT-012 · No CORS Middleware

| Field | Detail |
|-------|--------|
| **File** | `api/main.py:1-12` |
| **Risk** | 🔵 Low — Configuration |

**Fix:** Add `CORSMiddleware` with explicit `allow_origins`.

---

## AUDIT-013 · README Contains Incorrect Endpoint Documentation

| Field | Detail |
|-------|--------|
| **File** | `README.md:75-77, 88` |
| **Risk** | 🔵 Low — Documentation |

**Finding:** `GET /health` documented (actual: `/api/v1/health`); `?type=weapon` documented (does not exist).

**Fix:** Update README to match actual implementation.

---

*Audit completed: 2026-06-17*
