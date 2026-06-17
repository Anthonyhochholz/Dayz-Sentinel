# Security Audit — DayZ Sentinel

**Date:** 2026-06-17  
**Scope:** Security vulnerabilities only  
**Auditor:** Copilot Coding Agent  
**Framework:** OWASP Top 10 (2021)

---

## Summary

| ID | OWASP Category | Severity | Status |
|----|----------------|----------|--------|
| SEC-001 | A01 Broken Access Control | 🔴 Critical | Open |
| SEC-002 | A05 Security Misconfiguration | 🔴 Critical | Open |
| SEC-003 | A03 Injection | 🟠 High | Open |
| SEC-004 | A05 Security Misconfiguration | 🟠 High | Open |
| SEC-005 | A05 Security Misconfiguration | 🔵 Low | Open |

---

## SEC-001 · Unauthenticated Write Endpoint

**OWASP:** A01 — Broken Access Control  
**Severity:** 🔴 Critical

**File:** `sentinel_spr019/api/routes/economy_events.py`  
**Lines:** 73–75

```python
@router.post("/events/{event_name}/toggle-active", response_model=dict)
async def toggle_event_active(event_name: str):
    # No authentication check
```

**Impact:** Any network-reachable client can toggle server event active states, effectively disabling critical gameplay spawns (zombies, vehicles, loot).

**Recommended Fix:**

1. Add `SENTINEL_API_KEY` to `.env`
2. Create `api/auth.py`:

```python
import os
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    expected = os.getenv("SENTINEL_API_KEY")
    if not expected or api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key"
        )
    return api_key
```

3. Apply to route:

```python
from sentinel_spr019.api.auth import get_api_key

@router.post(
    "/events/{event_name}/toggle-active",
    dependencies=[Depends(get_api_key)]
)
```

---

## SEC-002 · Internal Error Details Leaked to Clients

**OWASP:** A05 — Security Misconfiguration  
**Severity:** 🔴 Critical

**Files:**
- `sentinel_spr019/api/routes/economy_items.py` lines 43, 66, 80
- `sentinel_spr019/api/routes/economy_events.py` lines 47, 70, 92, 111

```python
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

**Impact:** Error messages contain DB file paths, table names, and SQLite error codes — attackers learn the internal file system layout and schema.

**Recommended Fix:**

```python
import logging
logger = logging.getLogger(__name__)

except Exception as e:
    logger.error("Unhandled error in get_items: %s", e, exc_info=True)
    raise HTTPException(
        status_code=500,
        detail="An internal server error occurred. Please try again later."
    )
```

---

## SEC-003 · SQL Injection via f-String Interpolation

**OWASP:** A03 — Injection  
**Severity:** 🟠 High

**File:** `sentinel_spr019/api/repositories/economy_events_repository.py`  
**Lines:** 27–44, 103–114, 127–131

```python
where_clause = "WHERE active = 1" if active_only else ""
cursor.execute(f"SELECT COUNT(*) as count FROM economy_events {where_clause}")
```

**Current Risk:** Low (controlled by `bool` cast). **Future Risk:** High — pattern will be copied for user-provided filter values.

Bandit (Python security linter) flags all f-String SQL usage regardless.

**Recommended Fix:**

```python
params: list = [limit, offset]
conditions: list[str] = []
if active_only:
    conditions.append("active = ?")
    params.insert(0, 1)

where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
cursor.execute(
    f"SELECT event_name, ... FROM economy_events {where} ORDER BY event_name LIMIT ? OFFSET ?",
    params
)
```

---

## SEC-004 · Configuration Variables Not Loaded from `.env`

**OWASP:** A05 — Security Misconfiguration  
**Severity:** 🟠 High

**Files:** `.env.example:1-2`, `docker-compose.yml:6-7`, `Dockerfile:6`

The `.env` file is provided but never loaded. As a result:
- `API_PORT` has no effect → port is hardcoded to 8000
- Future secrets (e.g., `SENTINEL_API_KEY`) would silently not be read

**Recommended Fix:**

```yaml
# docker-compose.yml
services:
  sentinel:
    env_file:
      - .env
    ports:
      - "${API_PORT:-8000}:${API_PORT:-8000}"
```

```python
# api/main.py (or a config module)
from dotenv import load_dotenv
load_dotenv()
```

Add `python-dotenv` to `requirements.txt`.

---

## SEC-005 · No CORS Policy

**OWASP:** A05 — Security Misconfiguration  
**Severity:** 🔵 Low

**File:** `sentinel_spr019/api/main.py` lines 1–12

FastAPI defaults to no CORS headers, which blocks legitimate browser-based frontends and may cause unexpected permissive behavior on some proxy setups.

**Recommended Fix:**

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "Content-Type"],
)
```

---

## Remediation Priority

1. **SEC-001** — Block unauthenticated writes immediately
2. **SEC-002** — Suppress error details immediately
3. **SEC-004** — Fix env loading (enables SEC-001 fix)
4. **SEC-003** — Refactor SQL construction
5. **SEC-005** — Configure CORS for browser clients

---

*Audit completed: 2026-06-17*
