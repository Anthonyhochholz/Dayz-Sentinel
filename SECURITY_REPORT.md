# Security Report — DayZ Sentinel

**Date:** 2026-06-20  
**Auditor:** Copilot Security Audit  
**Framework:** OWASP Top 10 (2021)  
**Scope:** All Python source, configuration, Docker infrastructure, and schema files

---

## Executive Summary

| Severity | Count | Open | Resolved |
|----------|-------|------|----------|
| 🔴 Critical | 3 | 2 | 1 |
| 🟠 High | 3 | 1 | 2 |
| 🟡 Medium | 4 | 4 | 0 |
| 🔵 Low | 4 | 4 | 0 |
| **Total** | **14** | **11** | **3** |

**Production Readiness:** ❌ **NOT READY** — Two open Critical vulnerabilities block production deployment.

---

## 🔴 Critical

---

### SEC-001 · Unauthenticated Write Endpoint (OWASP A01 — Broken Access Control)

| Field | Detail |
|-------|--------|
| **Status** | 🔴 OPEN |
| **OWASP** | A01 — Broken Access Control |
| **File** | `sentinel_spr019/api/routes/economy_events.py:77` |
| **Original Audit** | AUDIT-001 (filed SPR-019, still open SPR-021) |

**Finding:**

```python
@router.post("/events/{event_name}/toggle-active", response_model=dict)
async def toggle_event_active(event_name: str):
    # No Depends() guard, no token validation, no IP restriction
```

`POST /api/v1/economy/events/{event_name}/toggle-active` is the only write endpoint in the application and it has **zero access control**. Any HTTP client that can reach port 8000 can toggle any DayZ server event active/inactive — including disabling zombie spawns, contaminated zones, vehicle spawns, and loot events.

**Attack scenario:** An attacker (or a misconfigured internal service) sends `POST /api/v1/economy/events/ZmbF_Base/toggle-active` repeatedly, cycling the game's zombie faction between enabled and disabled states, causing server gameplay to become erratic or unplayable without any trace of who performed the action.

**Risk escalation:** Docker exposes port 8000 on the host by default (`ports: - "${API_PORT:-8000}:8000"`). If the host is internet-accessible (common in home lab / VPS deployments), this endpoint is publicly reachable.

**Recommended fix:**

1. Create `sentinel_spr019/api/auth.py`:
```python
import os
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    expected = os.environ.get("SENTINEL_API_KEY")
    if not expected or api_key != expected:
        raise HTTPException(status_code=403, detail="Forbidden")
```
2. Add `Depends(get_api_key)` to `toggle_event_active` function signature
3. Add `SENTINEL_API_KEY=<random-secret>` to `.env.example` with instructions
4. Resolve SEC-002 (env loading) simultaneously or this fix is a no-op

---

### SEC-002 · Environment Variables Never Loaded — Future Secrets Will Be Silently Ignored (OWASP A05)

| Field | Detail |
|-------|--------|
| **Status** | 🔴 OPEN |
| **OWASP** | A05 — Security Misconfiguration |
| **Files** | `requirements.txt`, `sentinel_spr019/api/main.py`, `docker-compose.yml` |

**Finding:**

- `python-dotenv` is NOT in `requirements.txt`
- `load_dotenv()` is NEVER called in `main.py` or anywhere in the application
- `docker-compose.yml` does NOT have `env_file: .env`

**Why this is critical:**

The SEC-001 fix (API key authentication) requires reading `SENTINEL_API_KEY` from the environment. If SEC-002 is not fixed first, `os.environ.get("SENTINEL_API_KEY")` will always return `None` — and the auth check will reject ALL requests (denial of service) or, if the implementation defaults to `None == None`, accept ALL requests (authentication bypass).

This is not theoretical — it is the exact failure mode that will occur if SEC-001 is implemented without SEC-002.

**Additional impact:**

- `API_PORT` is documented as configurable via `.env` but is only honored by Docker's port mapping at the host level, not by the Python application
- Any future `LOG_LEVEL`, `CORS_ORIGINS`, or `DATABASE_URL` configuration will silently have no effect

**Recommended fix:**

1. Add `python-dotenv>=1.0.0` to `requirements.txt`
2. Add at the top of `main.py`:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```
3. Add `env_file: .env` to the `sentinel` service in `docker-compose.yml`

---

### SEC-003 · `sentinel.db` Binary Database Committed to Git (OWASP A02 — Cryptographic Failures / Data Exposure)

| Field | Detail |
|-------|--------|
| **Status** | 🔴 OPEN (new finding, not in previous audits) |
| **OWASP** | A02 — Cryptographic Failures / Information Disclosure |
| **File** | `sentinel_spr019/database/sqlite/sentinel.db` |

**Finding:**

The live SQLite database file is committed to the git repository. It contains:
- 1,917 DayZ item configurations
- 58 server event configurations including active/inactive states

**Risks:**

1. **Data exposure:** If this repository is ever made public (GitHub fork, accidental public toggle), the exact DayZ server configuration is visible to any player who finds the repository — revealing spawn locations, item rarities, active event zones.
2. **Git history bloat:** Binary files cannot be diff'd. Every re-import of DayZ data generates a new binary blob in git history. Over time this makes the repository uncloneable in reasonable time.
3. **Non-reproducible builds:** The Docker image copies the pre-populated database into the container. A developer who `docker build` from a fresh clone gets a container with the data from the last git commit, not from the actual DayZ server. Migrations or re-imports that change the DB format will conflict with the committed file.
4. **False freshness:** A developer pulling the repo may see "1,917 items" in the DB without realizing the data is from the last git commit date, not from the live DayZ server.

**Recommended fix:**

1. Add `sentinel_spr019/database/sqlite/*.db` to `.gitignore`
2. Remove `sentinel.db` from git tracking: `git rm --cached sentinel_spr019/database/sqlite/sentinel.db`
3. Create `sentinel_spr019/database/sqlite/.gitkeep` to preserve the directory in git
4. Create `scripts/db_init.py` that initializes the DB from schema files + importers on first run
5. Add a `HEALTHCHECK` in `Dockerfile` that verifies the DB file exists before marking container healthy

---

## 🟠 High

---

### SEC-004 · Exception Message Leaked in 404 HTTP Response (OWASP A05 — Information Disclosure)

| Field | Detail |
|-------|--------|
| **Status** | 🟠 OPEN |
| **OWASP** | A05 — Security Misconfiguration / Information Disclosure |
| **File** | `sentinel_spr019/api/routes/economy_events.py:93–95` |

**Finding:**

```python
except Exception as e:
    if "not found" in str(e):
        raise HTTPException(status_code=404, detail=str(e))  # ← leaks str(e)
    LOGGER.exception(...)
    raise HTTPException(status_code=500, detail="Internal server error")
```

The 500 path (AUDIT-002) was correctly fixed to return a generic message. However, the 404 path still passes `str(e)` directly to the HTTP response. The current message is `"Event {name} not found"` (controlled by our code), but this pattern is fragile and the use of `str(e)` as an HTTP response body violates the generic-error-response policy established for the rest of the application.

**Recommended fix:** Replace `detail=str(e)` with `detail=f"Event '{event_name}' not found"`. Define a typed `EventNotFoundError` exception and catch it explicitly.

---

### SEC-005 · f-String SQL Concatenation in Repository (OWASP A03 — SQL Injection Pattern) — ✅ RESOLVED

| Field | Detail |
|-------|--------|
| **Status** | ✅ RESOLVED (AUDIT-004, SPR-021) |
| **File** | `sentinel_spr019/api/repositories/economy_events_repository.py` |

**Resolution:** The f-string SQL pattern was replaced with conditional parameterized query construction. The `active_only` boolean flag selects between two hard-coded SQL strings; no user input is interpolated into SQL. Bandit-level concern addressed.

---

### SEC-006 · Synchronous SQLite in Async Handlers — Denial of Service Risk

| Field | Detail |
|-------|--------|
| **Status** | 🟠 OPEN |
| **OWASP** | A05 — Security Misconfiguration (availability impact) |
| **Files** | All route handlers (`economy_items.py`, `economy_events.py`) |

**Finding:**

All route handlers are declared `async def` but perform synchronous SQLite I/O directly on the event loop thread. A single slow query (e.g., full-table scan of 1,917 items with no index) blocks ALL concurrent requests for the duration.

**Attack scenario (low-sophistication DoS):** An attacker sends `GET /api/v1/economy/items?search=a` (matches ~1,500 items with `LIKE '%a%'`) repeatedly. Each request performs a full table scan on the event loop thread. Under 5–10 concurrent requests, the server becomes unresponsive to all clients including legitimate admin actions on the toggle endpoint.

**Recommended fix:** Convert all route handlers from `async def` to plain `def`. FastAPI automatically runs `def` handlers in a thread pool, making SQLite I/O non-blocking from the event loop's perspective. This is the lowest-risk, lowest-effort fix.

---

## 🟡 Medium

---

### SEC-007 · No Rate Limiting on Any Endpoint

| Field | Detail |
|-------|--------|
| **Status** | 🟡 OPEN |
| **OWASP** | A05 — Security Misconfiguration |

All endpoints accept unlimited requests per second per client. Combined with SEC-006 (synchronous event loop blocking), a trivial attack can overwhelm the server. The `toggle-active` endpoint is particularly exposed — once authenticated (after SEC-001 is fixed), brute-forcing an API key is feasible without rate limiting.

**Recommended fix:** Add `slowapi` or implement custom rate limiting middleware. Start with: 60 req/min for read endpoints, 10 req/min for write endpoints per IP.

---

### SEC-008 · No HTTPS / TLS Configuration

| Field | Detail |
|-------|--------|
| **Status** | 🟡 OPEN |
| **OWASP** | A02 — Cryptographic Failures |

The application listens on plain HTTP (port 8000). The API key (once implemented per SEC-001 fix) is transmitted as a plain-text HTTP header. On any network with interception capability (home LAN, cloud VPS), the API key can be captured in a single observed request.

**Recommended fix:** For LAN deployments, document use of a reverse proxy (nginx with self-signed cert or Let's Encrypt). For public deployments, add TLS termination to the Docker Compose setup. Add a note in `.env.example` about running behind a proxy.

---

### SEC-009 · No Security Headers in HTTP Responses

| Field | Detail |
|-------|--------|
| **Status** | 🟡 OPEN |
| **OWASP** | A05 — Security Misconfiguration |

The API returns no security-relevant HTTP headers:
- No `X-Content-Type-Options: nosniff`
- No `X-Frame-Options: DENY`
- No `Content-Security-Policy`
- No `Strict-Transport-Security`

While most of these are browser-security headers (relevant when a web UI calls the API), they are best practice for any HTTP API.

**Recommended fix:** Add a middleware function to `main.py` that appends security headers to all responses. This is a 5-line addition.

---

### SEC-010 · No Audit Log for Write Operations

| Field | Detail |
|-------|--------|
| **Status** | 🟡 OPEN |
| **OWASP** | A09 — Security Logging and Monitoring Failures |

When `toggle_event_active` is called, there is no structured audit log recording who made the change, from what IP, and what the previous state was. The `LOGGER.exception(...)` only fires on errors, not on successful mutations.

**Recommended fix:** Add `LOGGER.info("toggle_active: event=%s old_active=%s new_active=%s", name, old_status, new_status)` in `toggle_active()`. Once authentication is added (SEC-001), include the authenticated identity in the log.

---

## 🔵 Low

---

### SEC-011 · API Key Transmitted as HTTP Header (Plain Text)

| Field | Detail |
|-------|--------|
| **Status** | 🔵 OPEN (Pre-condition: SEC-001 not yet implemented) |

Once API key auth is added, the key will travel as `X-API-Key: <secret>` in plain HTTP headers. Without TLS (SEC-008), this is observable on the network. Low-risk in a trusted LAN context, but documents as a known residual risk.

---

### SEC-012 · SQLite Database File Has No Access Controls

| Field | Detail |
|-------|--------|
| **Status** | 🔵 OPEN |

`sentinel.db` is a regular file with default filesystem permissions inside the Docker container (running as root). Any process inside the container can read, write, or delete the database file.

**Recommended fix:** Run the uvicorn process as a non-root user in Docker. Set file permissions to `640` with the app user as owner.

---

### SEC-013 · `SENTINEL_API_KEY` Not in `.env.example`

| Field | Detail |
|-------|--------|
| **Status** | 🔵 OPEN (Pre-condition: SEC-001 not yet implemented) |

`.env.example` only contains `TZ` and `API_PORT`. When SEC-001 is implemented, `SENTINEL_API_KEY` must be added to `.env.example` with a clear instruction that it must be set before starting the container. Without this, users who copy `.env.example` to `.env` will have a blank API key — either causing auth failures or (if the implementation has a permissive `None` check) an authentication bypass.

---

### SEC-014 · `docker-compose.yml` Uses No Health Check

| Field | Detail |
|-------|--------|
| **Status** | 🔵 OPEN |

The Docker Compose service definition has no `healthcheck` directive. Container orchestrators cannot determine if the application is ready to receive traffic. A container that starts but fails to connect to the DB will appear healthy.

**Recommended fix:** Add:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

---

## SQL Injection Risk Assessment

The following SQL operations were reviewed for injection risk:

| File | SQL Pattern | Parameterized? | Risk |
|------|------------|----------------|------|
| `economy_items_repository.py:29` | `SELECT COUNT(*)` | N/A — no user input | None |
| `economy_items_repository.py:31–38` | `SELECT ... LIMIT ? OFFSET ?` | ✅ Yes | None |
| `economy_items_repository.py:62–68` | `SELECT ... WHERE name = ?` | ✅ Yes | None |
| `economy_items_repository.py:94–101` | `SELECT ... WHERE name LIKE ?` | ✅ Yes | None |
| `economy_events_repository.py:36–48` | Conditional query selection | ✅ Boolean flag only | None |
| `economy_events_repository.py:72–76` | `SELECT ... WHERE event_name = ?` | ✅ Yes | None |
| `economy_events_repository.py:99–113` | Conditional + `LIKE ?` | ✅ Yes | None |
| `economy_events_repository.py:153–158` | `SELECT/UPDATE WHERE event_name = ?` | ✅ Yes | None |
| `types_importer.py:317–342` | Dynamic table/column names | ✅ Validated allowlist | None — protected by `_validate_identifier()` |

**Conclusion:** No SQL injection vulnerabilities exist in production code. The `_validate_identifier()` function in `types_importer.py` correctly prevents dynamic SQL injection from XML input.

---

## Dependency Vulnerability Assessment

| Package | Version in use | Known CVEs |
|---------|---------------|------------|
| `fastapi` | unpinned (latest) | No known critical CVEs at time of audit |
| `uvicorn[standard]` | unpinned (latest) | No known critical CVEs at time of audit |
| `requests` | unpinned (latest) | No known critical CVEs at time of audit |
| `sqlite3` | Python stdlib | N/A |
| `xml.etree.ElementTree` | Python stdlib | ⚠ Known XML bomb / billion-laughs attack risk when parsing untrusted XML |

**XML parsing risk (SEC-015):** `types_importer.py` and `events_importer.py` use `xml.etree.ElementTree` to parse DayZ XML files. Python's `ET` is vulnerable to billion-laughs (XML bomb) attacks when parsing untrusted XML from the network. However, in the current architecture, XML files are loaded from the local filesystem by a trusted operator — not from network input. Risk is LOW as long as the importer is never exposed as an HTTP endpoint that accepts XML input.

---

*Last updated: 2026-06-20 · Full repository security audit*
