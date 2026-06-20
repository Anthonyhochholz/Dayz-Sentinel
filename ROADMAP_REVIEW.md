# Roadmap Review — DayZ Sentinel

**Date:** 2026-06-20  
**Auditor:** Copilot Architecture Audit  
**Source:** `docs/ROADMAP.md` (last updated 2026-06-17, SPR-021)  
**Method:** Cross-referenced roadmap against actual code, `docs/PROJECT_MEMORY.md`, sprint files, and git history

---

## Roadmap vs. Implementation

---

## 🔴 P1 — Critical / Security

| ID | Task | Status | Assessment |
|----|------|--------|-----------|
| P1-001 | Add API-Key authentication for all write endpoints | ❌ NOT STARTED | `toggle_event_active` has zero auth. `auth.py` does not exist. `SENTINEL_API_KEY` not in `.env.example`. This is the sole remaining Critical security issue blocking production. |
| P1-002 | Replace `detail=str(e)` with generic 500 messages | ✅ COMPLETE | Routes return `"Internal server error"` in all except blocks — EXCEPT the 404 path in `economy_events.py:94` which still uses `str(e)`. Marked complete but has a residual defect. |
| P1-003 | Wrap all `sqlite3.connect()` calls in context managers | ⚠️ PARTIALLY COMPLETE | Repositories use `try/finally conn.close()` which prevents leaks, but is NOT a true context manager. `database.py` still returns a raw connection. A `@contextmanager` wrapper does not exist. The spirit of the fix is met; the letter is not. |
| P1-004 | Replace f-String SQL interpolation in `economy_events_repository.py` | ✅ COMPLETE | Repository uses hard-coded SQL variants selected by boolean flag. No user input is interpolated. No f-string SQL injection risk. |
| P1-005 | Read `API_PORT` from `.env` in `docker-compose.yml` and `Dockerfile` | ⚠️ PARTIALLY COMPLETE | `docker-compose.yml` correctly uses `${API_PORT:-8000}` (Docker env variable substitution). However, `Dockerfile` hardcodes port 8000 in CMD, and `python-dotenv` is not installed so the Python app itself never reads `.env`. The Docker host-level port mapping works; Python-level env loading does not. |

---

## 🟠 P2 — High / Code Quality

| ID | Task | Status | Assessment |
|----|------|--------|-----------|
| P2-001 | Centralize `dict_factory` in `database.py` | ✅ COMPLETE | `dict_factory` is defined in `database.py:10–13` and imported by both repositories. No duplicates. |
| P2-002 | Delete `economy_repository.py` (dead code) | ✅ COMPLETE | File does not exist. Confirmed by directory listing. AUDIT-007 resolved. |
| P2-003 | Add `requests` to `requirements.txt` | ✅ COMPLETE | `requests` is present in `requirements.txt:3`. AUDIT-008 resolved. |
| P2-004 | Fix broken import in `scripts/test_import_run.py` and implement `types_importer.py` | ✅ COMPLETE | `types_importer.py` is fully implemented with upsert strategy, transactions, flags, and relations. `test_import_run.py` import path is correct. AUDIT-009 resolved. |
| P2-005 | Add `offset` parameter to `search()` methods in both repositories | ✅ COMPLETE | Both `EconomyItemsRepository.search()` and `EconomyEventsRepository.search()` accept `offset: int = 0` and include `OFFSET ?` in the SQL query. AUDIT-010 resolved. |
| P2-006 | Rename package from `sentinel_spr019` to `sentinel` | ❌ NOT STARTED | Package is still `sentinel_spr019`. AUDIT-011 remains open. All 15+ import statements still reference the sprint-numbered package. |
| P2-007 | Add `pytest` test suite with in-memory SQLite fixtures | ✅ COMPLETE | `tests/test_types_importer.py` — 21 tests, all passing. In-memory fixtures implemented correctly. |
| P2-008 | Pin dependency versions in `requirements.txt` | ❌ NOT STARTED | `requirements.txt` still lists 3 packages with no version pins. No lockfile exists. |

---

## 🟡 P3 — Medium / Features

| ID | Task | Status | Assessment |
|----|------|--------|-----------|
| P3-001 | Add CORS middleware with configurable allowed origins | ❌ NOT STARTED | No `CORSMiddleware` in `main.py`. Required before any web UI feature. |
| P3-002 | Fix README endpoint documentation | ✅ COMPLETE | `README.md` correctly documents `/api/v1/health`, correct response `{"status": "ok"}`, no phantom `?type=` parameter. AUDIT-013 resolved. |
| P3-003 | Implement player log import pipeline | ❌ NOT STARTED | Schema exists (20+ player/session tables). No importer file. No API endpoints. |
| P3-004 | Implement server session log import | ❌ NOT STARTED | Schema exists (`server_sessions`, `script_sessions`). No importer. No API. |
| P3-005 | Implement damage event import and analytics endpoint | ❌ NOT STARTED | Schema exists (`player_damage_events`). No importer. No API. |
| P3-006 | Add schema migration tooling | ❌ NOT STARTED | Two SQL files, no runner, no migration tracking. Manual steps required for all deployments. |
| P3-007 | Add Swagger/OpenAPI response schemas (replace `response_model=dict`) | ❌ NOT STARTED | All 9 route handlers still declare `response_model=dict`. Pydantic models exist but are unused (dead code). |
| P3-008 | Rate limiting via `slowapi` | ❌ NOT STARTED | No rate limiting middleware exists. |
| P3-009 | Repository methods return typed Pydantic models instead of plain `dict` | ❌ NOT STARTED | All repository methods return `List[dict]` or `Optional[dict]`. |

---

## 💡 Future / Under Discussion

| Idea | Status |
|------|--------|
| Web UI (admin dashboard) | ❌ NOT STARTED — also blocked by missing CORS (P3-001) |
| PostgreSQL option | ❌ NOT STARTED |
| Real-time log streaming (WebSocket) | ❌ NOT STARTED |
| Discord bot integration | ❌ NOT STARTED |
| Map visualization (heat-map) | ❌ NOT STARTED |

---

## Completion Summary

| Category | Complete | Partial | Not Started | Total |
|----------|----------|---------|-------------|-------|
| P1 Critical/Security | 2 | 2 | 1 | 5 |
| P2 High/Code Quality | 5 | 0 | 3 | 8 |
| P3 Medium/Features | 1 | 0 | 8 | 9 |
| Future Ideas | 0 | 0 | 5 | 5 |
| **Total** | **8** | **2** | **17** | **27** |

**Overall completion rate: 30% complete** (8/27 items fully done; 2 partially done)

---

## Discrepancies Between Roadmap and Actual State

### 1. P1-002 Marked Complete but Has Residual Defect

The ROADMAP and `PROJECT_MEMORY.md` mark AUDIT-002 (error detail leakage) as resolved. The 500 paths are correctly fixed. However, `economy_events.py:94–95` still uses `detail=str(e)` for the 404 case. The fix is ~95% complete but not 100%.

### 2. P1-003 Marked Complete but Pattern Is Suboptimal

`PROJECT_MEMORY.md` marks AUDIT-003 (DB connection leaks) as resolved. The `try/finally conn.close()` pattern does prevent leaks, but the ROADMAP description called for `@contextmanager` wrapping. The functional requirement is met but the architectural improvement (context manager) was not made.

### 3. Sprint Documents Are Wildly Out of Sync

- `docs/sprints/sprint_020.md` shows ALL acceptance criteria as `📋 Pending` — but several P1 items are now complete.
- `docs/sprints/sprint_021.md` shows ALL criteria as `📋 Pending` — but P2-001 through P2-007 are now complete.
- `docs/sprints/backlog.md` still lists `requests` as unscheduled (it was added in SPR-021).

### 4. Roadmap Has No Entry for `events_importer.py` Defects

The roadmap does not track any work item for:
- Adding upsert strategy to `events_importer.py` (currently silently skips re-imports)
- Adding tests for `events_importer.py` (0 tests vs 21 for types_importer)

These are real production bugs that should be tracked items.

### 5. SQLite DB in Git Not on Roadmap

The committed `sentinel.db` binary file (SEC-003 in SECURITY_REPORT) is a significant production blocker that appears nowhere in the ROADMAP. This needs to be added as a P1 item.

---

## ⭐ THE SINGLE MOST IMPORTANT NEXT TASK

### P1-001 — Add API-Key Authentication to the Toggle-Active Endpoint

**Why this is THE most important next task:**

1. **It is the only remaining Critical security vulnerability** that has been known since SPR-019 (two full sprints ago) and remains completely unimplemented.

2. **It directly controls who can mutate server state.** The toggle-active endpoint is the only write endpoint in the entire application. Until it is protected, the application cannot be deployed on any network-accessible machine without risking unauthorized manipulation of DayZ server events.

3. **All other security work depends on it.** SEC-002 (env loading) must be fixed as a prerequisite. That fix is small and mechanical. Once env loading works, the API key can be read securely. Both tasks together (SEC-001 + SEC-002) represent less than 30 lines of code.

4. **Nothing else unblocks as much.** P2-006 (package rename) is a large refactor with high risk. P3-001 (CORS) is needed for the future UI. P3-006 (migrations) is an infrastructure improvement. All of these are lower urgency than the unauthenticated write endpoint.

5. **The fix is well-scoped and low-risk.** Create `auth.py` (~10 lines), add `Depends(get_api_key)` to one function, add one line to `requirements.txt`, two lines to `main.py`, one line to `docker-compose.yml`, and one entry to `.env.example`. No schema changes, no database migrations, no test rewrites.

**Acceptance criteria for P1-001 + P1-005 (combined sprint):**
- [ ] `sentinel_spr019/api/auth.py` created with `get_api_key` FastAPI dependency
- [ ] `python-dotenv` added to `requirements.txt` with pinned version
- [ ] `load_dotenv()` called at top of `main.py`
- [ ] `env_file: .env` added to `docker-compose.yml`
- [ ] `SENTINEL_API_KEY` added to `.env.example` with generation instructions
- [ ] `Depends(get_api_key)` applied to `toggle_event_active` route
- [ ] Integration test: request without key returns 403, request with correct key returns 200
- [ ] `sentinel.db` removed from git tracking (SEC-003)

---

*Last updated: 2026-06-20 · Full repository roadmap audit*
