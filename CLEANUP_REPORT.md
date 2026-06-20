# Cleanup Report — DayZ Sentinel

**Date:** 2026-06-20  
**Auditor:** Copilot Architecture & Security Audit  
**Scope:** Complete codebase — all source files, configuration, documentation, and infrastructure

---

## Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | 3 |
| 🟠 High | 8 |
| 🟡 Medium | 11 |
| 🔵 Low | 8 |
| **Total** | **30** |

---

## 🔴 Critical

---

### CL-001 · SQLite Database File Committed to Git

| Field | Detail |
|-------|--------|
| **Severity** | Critical |
| **File** | `sentinel_spr019/database/sqlite/sentinel.db` |
| **Problem** | The live SQLite database (135 KB binary) is tracked by git and committed to the repository. It is NOT listed in `.gitignore`. |
| **Why it is a problem** | Binary database files should never be version-controlled. (1) Git cannot diff binary files, causing every re-import to bloat history. (2) The file contains real DayZ server configuration data (1,917 items, 58 events) — if the repo becomes public, this data is exposed. (3) Fresh Docker builds copy the pre-populated DB into the container image, making the image non-reproducible and DB migration impossible. (4) Any developer who `git pulls` silently overwrites their local DB with the repo's snapshot. |
| **Recommended fix** | Add `sentinel_spr019/database/sqlite/*.db` to `.gitignore`. Delete `sentinel.db` from git history (`git rm --cached sentinel_spr019/database/sqlite/sentinel.db`). Create a startup script that runs the schema SQL files and importers on first boot if the DB does not exist. Add `sentinel_spr019/database/sqlite/sentinel.db.example` (empty placeholder) if needed. |

---

### CL-002 · Unauthenticated Write Endpoint

| Field | Detail |
|-------|--------|
| **Severity** | Critical |
| **File** | `sentinel_spr019/api/routes/economy_events.py:77–98` |
| **Problem** | `POST /api/v1/economy/events/{event_name}/toggle-active` has no authentication, no API key check, no dependency guard. |
| **Why it is a problem** | Any client that can reach port 8000 (LAN, Docker host, or internet if port-forwarded) can toggle any DayZ server event active/inactive — disabling zombie spawns, vehicle spawns, contaminated zones, or loot events. This is a direct Broken Access Control vulnerability (OWASP A01). This endpoint has been open since SPR-019 and is the only remaining Critical security issue blocking production. |
| **Recommended fix** | Create `sentinel_spr019/api/auth.py` with a FastAPI `APIKeyHeader` dependency. Add `SENTINEL_API_KEY` to `.env.example`. Apply `Depends(get_api_key)` to the `toggle_event_active` function signature. Add `python-dotenv` to `requirements.txt` and call `load_dotenv()` in `main.py`. |

---

### CL-003 · Environment Variables Never Loaded

| Field | Detail |
|-------|--------|
| **Severity** | Critical |
| **Files** | `requirements.txt`, `sentinel_spr019/api/main.py`, `docker-compose.yml` |
| **Problem** | `python-dotenv` is not in `requirements.txt`. `load_dotenv()` is never called. `docker-compose.yml` has no `env_file: .env` directive. |
| **Why it is a problem** | The documented `.env`-based configuration workflow silently does nothing. Most critically, the forthcoming `SENTINEL_API_KEY` (required by CL-002 fix) will be silently ignored at runtime — the application will start with no API key, meaning authentication is effectively a no-op. This makes an entire class of configuration fixes non-functional by default. |
| **Recommended fix** | Add `python-dotenv` (pinned) to `requirements.txt`. Add `from dotenv import load_dotenv; load_dotenv()` at the top of `main.py`. Add `env_file: .env` to the `sentinel` service in `docker-compose.yml`. |

---

## 🟠 High

---

### CL-004 · Exception Message Leaked in 404 Response

| Field | Detail |
|-------|--------|
| **Severity** | High |
| **File** | `sentinel_spr019/api/routes/economy_events.py:93–95` |
| **Problem** | The `toggle_event_active` handler catches exceptions and calls `raise HTTPException(status_code=404, detail=str(e))` when the exception message contains "not found". |
| **Why it is a problem** | This passes the raw internal exception string directly to the HTTP client. While the current exception message is `"Event {name} not found"` (controlled), the pattern relies on fragile string matching (`"not found" in str(e)`) and leaks stack information if that exception changes. This violates the principle of generic error responses (OWASP A05). The 500 path was already fixed to generic messages, but the 404 path was overlooked. |
| **Recommended fix** | In `EconomyEventsRepository.toggle_active()`, raise a custom application exception (e.g., `EventNotFoundError`) instead of a bare `Exception`. In the route handler, catch `EventNotFoundError` explicitly and return a hardcoded `"Event not found"` message, never `str(e)`. |

---

### CL-005 · Async Route Handlers Block the Event Loop

| Field | Detail |
|-------|--------|
| **Severity** | High |
| **Files** | `sentinel_spr019/api/routes/economy_items.py`, `sentinel_spr019/api/routes/economy_events.py` (all route handlers) |
| **Problem** | All route handlers are declared `async def` but call synchronous SQLite operations (`sqlite3.connect()`, `cursor.execute()`, `cursor.fetchall()`) directly. |
| **Why it is a problem** | SQLite I/O is synchronous and blocking. Calling it from an `async def` function does not make it non-blocking — it runs on the event loop thread and blocks all other requests for the duration of the query. Under any concurrent load (multiple simultaneous API calls), all requests queue behind each active DB query. The application cannot handle concurrent traffic despite being built on an async framework. |
| **Recommended fix** | Wrap all repository calls in `await asyncio.get_event_loop().run_in_executor(None, ...)`. Alternatively, switch to an async SQLite library (`aiosqlite`) or convert all route handlers from `async def` to plain `def` (FastAPI runs `def` routes in a thread pool automatically). The `def` approach is the lowest-effort correct fix. |

---

### CL-006 · Unpinned Dependencies

| Field | Detail |
|-------|--------|
| **Severity** | High |
| **File** | `requirements.txt` |
| **Problem** | `requirements.txt` lists only `fastapi`, `uvicorn[standard]`, and `requests` with no version constraints. |
| **Why it is a problem** | Any `pip install` at any point in time installs whatever the latest version is. A breaking upstream release (e.g., FastAPI, Pydantic v3, or Starlette) can silently break the application without any change to the codebase. Docker image rebuilds become non-reproducible. This is particularly dangerous for production deployments where the exact environment must be reproducible. |
| **Recommended fix** | Pin all dependencies with exact or minimum-compatible versions: `fastapi==0.115.x`, `uvicorn[standard]==0.30.x`, `requests==2.32.x`, `python-dotenv==1.0.x`. Consider generating a `requirements-lock.txt` via `pip freeze` for fully reproducible builds. |

---

### CL-007 · `events_importer.py` Uses `print()` Instead of Logging

| Field | Detail |
|-------|--------|
| **Severity** | High |
| **File** | `sentinel_spr019/importer/economy/events_importer.py:58` |
| **Problem** | The function ends with `print(f"import_events: inserted={inserted}, skipped={skipped}")` instead of using the `logging` module. |
| **Why it is a problem** | In a containerized production environment, `print()` output is not configurable, not filterable, and does not include log levels, timestamps, or context. Unlike `types_importer.py` which uses `LOGGER = logging.getLogger(__name__)`, `events_importer.py` bypasses the logging system entirely. This inconsistency means event import activity is invisible in production log aggregation. |
| **Recommended fix** | Remove the `print()` call. Add `LOGGER = logging.getLogger(__name__)` at module level. Replace `print(...)` with `LOGGER.info("import_events: inserted=%d, skipped=%d", inserted, skipped)`. |

---

### CL-008 · `events_importer.py` Has No Upsert Strategy — Silent Data Loss on Re-import

| Field | Detail |
|-------|--------|
| **Severity** | High |
| **File** | `sentinel_spr019/importer/economy/events_importer.py:33–55` |
| **Problem** | The events importer uses `INSERT INTO economy_events` and catches `sqlite3.IntegrityError` silently to skip duplicates. There is no UPDATE path — re-importing an updated `events.xml` will silently skip all existing events with no data changes. |
| **Why it is a problem** | `types_importer.py` correctly uses an upsert strategy (SELECT → INSERT or UPDATE). The events importer does not. If a server admin updates `events.xml` (changes `nominal`, `active`, `lifetime`, etc.) and re-runs the importer, all existing rows are silently skipped and the database retains stale values. This creates a false sense of data freshness and requires manual DB intervention to update events. |
| **Recommended fix** | Implement `INSERT OR REPLACE INTO` or use an explicit SELECT-then-UPDATE pattern identical to `types_importer._upsert_item()`. Wrap the import loop in a transaction with rollback on error (as `types_importer` does). |

---

### CL-009 · No Tests for `events_importer.py`

| Field | Detail |
|-------|--------|
| **Severity** | High |
| **File** | `sentinel_spr019/importer/economy/events_importer.py` |
| **Problem** | `types_importer.py` has 21 comprehensive pytest unit tests. `events_importer.py` has zero tests. |
| **Why it is a problem** | The events importer is production code that writes to the database. The CL-008 upsert bug above went undetected precisely because there are no tests. Any refactoring of the events importer is done without a safety net. The asymmetry in test coverage creates a false confidence — the test suite passes (21/21) but only half the import pipeline is covered. |
| **Recommended fix** | Create `tests/test_events_importer.py` with at minimum: basic insert, skip-on-duplicate, re-import with changed fields (to verify update behavior once CL-008 is fixed), missing fields, and transaction rollback. |

---

### CL-010 · `CASAOS_INSTALL.md` Is Partially in German and Contains Broken Volume Reference

| Field | Detail |
|-------|--------|
| **Severity** | High |
| **File** | `CASAOS_INSTALL.md` |
| **Problem** | The file contains German-language instructions ("ZIP entpacken", "Ordner nach /DATA/AppData/dayz-sentinel kopieren") in an otherwise English-language project. It also references a `mirror -> DayZ Mirror` volume that does not exist in `docker-compose.yml`. |
| **Why it is a problem** | The installation guide is the first document a new user reads when deploying on CasaOS. Inconsistent language is unprofessional and confusing. The phantom `mirror` volume reference will cause confusion since no such volume is defined anywhere in the project infrastructure. If a user follows these instructions literally, their deployment will be misconfigured. |
| **Recommended fix** | Rewrite `CASAOS_INSTALL.md` in English. Remove the `mirror -> DayZ Mirror` volume reference (or add the volume to `docker-compose.yml` if it is intentional). Verify all installation steps against the actual `docker-compose.yml`. |

---

### CL-011 · Search Pagination Returns Incorrect `total` Count

| Field | Detail |
|-------|--------|
| **Severity** | High |
| **Files** | `sentinel_spr019/api/routes/economy_items.py:28–35`, `sentinel_spr019/api/routes/economy_events.py:29–38` |
| **Problem** | When `search` parameter is provided, both routes return `"total": len(items)` (count of items in the current page) instead of the total number of matching records in the database. |
| **Why it is a problem** | Clients implementing pagination rely on `total` to calculate the number of pages. With `total: len(items)`, a client that requests `limit=10&offset=0&search=rifle` and gets back 10 items is told `total=10` and believes it has all matching items — even if there are 150 matches. The second and subsequent pages are unreachable. This is a functional pagination bug that silently truncates search results for any consumer of the API. |
| **Recommended fix** | Add a `search_count()` method to both repositories that executes `SELECT COUNT(*) FROM ... WHERE name LIKE ?`. Call it in the search branch and return its result as `total`. This mirrors the behavior of the non-search path. |

---

## 🟡 Medium

---

### CL-012 · Package Name Coupled to Sprint Number

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **Files** | All `import` statements, `Dockerfile:6`, `docker-compose.yml:8`, `pytest.ini` |
| **Problem** | The root Python package is named `sentinel_spr019`, where `spr019` is the sprint number in which it was created. |
| **Why it is a problem** | Package names are part of the public API and appear in every `import` statement. When the project is renamed (as planned in ROADMAP P2-006), every import across all files breaks simultaneously. The sprint number is meaningless to external consumers or new contributors. It also implies the codebase is "frozen at sprint 19" rather than being a living project. |
| **Recommended fix** | Rename package to `sentinel` or `dayz_sentinel`. Update all 15+ import statements, `Dockerfile` CMD, `docker-compose.yml` volume path, `pytest.ini`, and `README.md`. This is a breaking change and should be done in a dedicated migration sprint. |

---

### CL-013 · All Pydantic Models Are Dead Code — Never Used in Production

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **Files** | `sentinel_spr019/api/models/economy_item.py`, `sentinel_spr019/api/models/economy_event.py` |
| **Problem** | Six Pydantic model classes (`EconomyItemBase`, `EconomyItem`, `EconomyItemResponse`, `EconomyEventBase`, `EconomyEvent`, `EconomyEventResponse`) are defined but imported by nothing in production code. Routes return raw `dict`, repositories return raw `dict`. |
| **Why it is a problem** | Dead model code misleads developers about the intended architecture — models appear to be "the way" to add new fields, but changes to them have zero effect at runtime. The `Config: from_attributes = True` and `Optional[int] = None` fields suggest an ORM usage that was never implemented. This is 70+ lines of misleading, unmaintained code. |
| **Recommended fix** | Either (a) DELETE the model files and the entire `models/` directory until models are actually needed; or (b) immediately wire them into routes by replacing `response_model=dict` with typed response models — which also fixes CL-015. Option (b) is preferred as it provides real value. |

---

### CL-014 · `EconomyItemResponse` and `EconomyEventResponse` Duplicate Base Classes

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **Files** | `sentinel_spr019/api/models/economy_item.py:23–33`, `sentinel_spr019/api/models/economy_event.py:29–45` |
| **Problem** | `EconomyItemResponse` re-declares all six fields from `EconomyItemBase` instead of inheriting from it. Same for `EconomyEventResponse` re-declaring all twelve fields from `EconomyEventBase`. |
| **Why it is a problem** | Adding a new field requires updating both the Base class and the Response class separately, with no guarantee they stay in sync. This is textbook code duplication (DRY violation). Given that the models are already dead (CL-013), this also means the duplication will never be caught by tests. |
| **Recommended fix** | `EconomyItemResponse` should inherit `EconomyItemBase` (same for events). If they truly need different field sets, document why. This is a one-line fix per class once they're actually used. |

---

### CL-015 · All Routes Declare `response_model=dict`

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **Files** | All route handlers in `economy_items.py` and `economy_events.py` |
| **Problem** | Every route handler declares `response_model=dict`, which is a valid but useless type hint. |
| **Why it is a problem** | FastAPI generates OpenAPI schemas from `response_model`. When `dict` is used, the `/docs` endpoint shows no response structure — no field names, no types, no examples. Clients and integrators have no machine-readable contract. Response validation is also disabled, so a response that accidentally includes a new field or drops a required field passes unnoticed. |
| **Recommended fix** | Define proper Pydantic response schemas (resolving CL-013) and apply them as `response_model=EconomyItemListResponse`, etc. This is the single change with the highest documentation payoff. |

---

### CL-016 · No CORS Middleware

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **File** | `sentinel_spr019/api/main.py` |
| **Problem** | No `CORSMiddleware` is configured in the FastAPI application. |
| **Why it is a problem** | Any web browser-based frontend (the planned Web UI dashboard) will be blocked by the browser's same-origin policy when calling this API. CORS must be configured before any web UI can be built against this API. Without it, the "Web UI" roadmap item is blocked at the infrastructure level before a single line of frontend code is written. |
| **Recommended fix** | Add `app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "*").split(","), allow_methods=["*"], allow_headers=["*"])` to `main.py`. Add `CORS_ORIGINS` to `.env.example`. Restrict origins in production. |

---

### CL-017 · No Schema Migration Tooling — Two SQL Files Applied Manually

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **Files** | `sentinel_spr019/database/schema/sentinel_v1_schema.sql`, `sentinel_spr019/database/schema/sentinel_v1_schema_rev2.sql` |
| **Problem** | The schema is split across two `.sql` files with no runner, no migration tracking, and no documented order. |
| **Why it is a problem** | A fresh deployment requires a developer to (1) know both files exist, (2) know to apply `_v1_schema.sql` before `_rev2.sql`, and (3) manually run them with `sqlite3`. There is no automatic check that the deployed DB matches the expected schema version. If a third schema file is added, this problem compounds. |
| **Recommended fix** | Create `scripts/db_init.py` that applies both schema files in order. Call it from the Docker `CMD` if the DB file does not exist. Long-term, integrate Alembic for versioned migrations. |

---

### CL-018 · Missing `__init__.py` in Importer Packages

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **Files** | `sentinel_spr019/importer/` (directory), `sentinel_spr019/importer/economy/` (directory) |
| **Problem** | Neither `sentinel_spr019/importer/` nor `sentinel_spr019/importer/economy/` contains an `__init__.py` file. All other package directories (`api/`, `api/models/`, `api/repositories/`, `api/routes/`) have `__init__.py`. |
| **Why it is a problem** | While Python 3 supports namespace packages without `__init__.py`, the rest of the codebase consistently uses explicit `__init__.py` markers. The inconsistency creates confusion about whether the omission is intentional. More critically, certain Python tooling (some test runners, coverage tools, static analyzers) behaves differently for namespace packages vs. regular packages. Imports from these modules via `sentinel_spr019.importer.economy.*` rely on namespace package behavior rather than the project's explicit convention. |
| **Recommended fix** | Add empty `__init__.py` to `sentinel_spr019/importer/` and `sentinel_spr019/importer/economy/`. |

---

### CL-019 · No API Integration Tests (FastAPI TestClient)

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **File** | `tests/` directory |
| **Problem** | `tests/` contains only `test_types_importer.py`. There are no tests for any API route handler. The integration tests in `scripts/test_api.py` require a running server and are not part of the pytest suite. |
| **Why it is a problem** | Route handler bugs (CL-004 exception message leak, CL-011 search pagination total, incorrect HTTP status codes) are undetectable by the current test suite. A developer can break an API contract with no failing test. FastAPI provides `TestClient` specifically for in-process route testing without needing a running server, making this straightforward to add. |
| **Recommended fix** | Create `tests/test_api_items.py` and `tests/test_api_events.py` using FastAPI `TestClient` with an in-memory SQLite fixture injected via app override of `get_connection`. Cover: all endpoints, 404 behavior, search, pagination, toggle-active. |

---

### CL-020 · `economy_events_repository.py` — String Exception Detection Is Fragile

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **File** | `sentinel_spr019/api/routes/economy_events.py:93–95` |
| **Problem** | `if "not found" in str(e):` detects event-not-found conditions by parsing the exception message string. |
| **Why it is a problem** | This is brittle: if the error message in `toggle_active()` changes (e.g., localization, refactor, or a different code path raises an exception with "not found" in a different context), the logic silently breaks — returning a 500 instead of a 404, or a 404 when a 500 was appropriate. This anti-pattern makes exception handling non-deterministic and impossible to test correctly. |
| **Recommended fix** | Define a `class EventNotFoundError(Exception): pass` in the repository module. Raise it explicitly instead of `raise Exception(f"Event {name} not found")`. Catch `EventNotFoundError` in the route handler by type, not by string content. |

---

### CL-021 · `scripts/test_api.py` Modifies Production Data

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **File** | `sentinel_spr019/scripts/test_api.py:60–81` |
| **Problem** | The integration smoke test calls `POST /api/v1/economy/events/{event_name}/toggle-active` against a live API, mutating the active state of a real event. |
| **Why it is a problem** | If run against a production or staging environment (as intended — it defaults to `http://localhost:8000`), it permanently changes server event data. The test does not toggle back to the original state. A developer who runs this script during production troubleshooting will accidentally disable a live DayZ server event. |
| **Recommended fix** | Save the original `active` value before toggling and toggle back after the assertion. Or, remove the toggle test from the smoke script and rely on the proper integration test suite (CL-019) for write endpoint verification. |

---

### CL-022 · `sentinel_spr019/__init__.py` and Other Package `__init__` Files Serve No Purpose

| Field | Detail |
|-------|--------|
| **Severity** | Medium |
| **Files** | `sentinel_spr019/__init__.py`, `sentinel_spr019/api/__init__.py`, `sentinel_spr019/api/models/__init__.py` (comment-only), `sentinel_spr019/api/repositories/__init__.py` (comment-only), `sentinel_spr019/api/routes/__init__.py` (comment-only) |
| **Problem** | Five `__init__.py` files are either completely empty or contain only inline comments like `# Models package`. |
| **Why it is a problem** | While empty `__init__.py` files are necessary for Python package recognition, the comment-only files are noise. More importantly, `sentinel_spr019/__init__.py` and `sentinel_spr019/api/__init__.py` are completely empty with no version string, no public API exports, and no package-level docstring — a missed opportunity for self-documentation. |
| **Recommended fix** | Add at minimum a `__version__ = "0.4.0"` to `sentinel_spr019/__init__.py`. Remove meaningless inline comments from the model/repository/route `__init__` files (leave them empty or add meaningful `__all__` exports). |

---

## 🔵 Low

---

### CL-023 · Duplicate/Stale Audit Documents in `docs/copilot-audits/`

| Field | Detail |
|-------|--------|
| **Severity** | Low |
| **Files** | `docs/copilot-audits/` (8 files) |
| **Problem** | Eight audit files exist in this directory. Most document issues that have since been resolved. `types_importer_implementation_report.md` and `types_importer_final_implementation.md` document a feature that is now shipped. `architecture_audit.md`, `code_quality_audit.md`, `current_state_report.md` contain overlapping information superseded by `full_project_audit.md` and the new reports being created. |
| **Why it is a problem** | Stale documentation is actively harmful — developers reading these files will act on findings that were already resolved (e.g., AUDIT-002 through AUDIT-010). The `README.md` in this folder still lists all 13 original audits as "Open", which is false. This erodes trust in all documentation. |
| **Recommended fix** | Delete `types_importer_implementation_report.md`, `types_importer_final_implementation.md`, `current_state_report.md`. Mark `architecture_audit.md`, `code_quality_audit.md` as superseded in their headers. Update `README.md` to reflect current status (AUDIT-001 open; AUDIT-002–013 resolved). |

---

### CL-024 · Sprint Documents Contain Stale Statuses

| Field | Detail |
|-------|--------|
| **Severity** | Low |
| **Files** | `docs/sprints/sprint_020.md`, `docs/sprints/sprint_021.md`, `docs/sprints/backlog.md` |
| **Problem** | `sprint_020.md` shows all acceptance criteria as `📋 Pending`. `sprint_021.md` shows `📋 Planned`. `backlog.md` lists items like "Add `requests` to `requirements.txt`" as unscheduled, but this was resolved in SPR-021. |
| **Why it is a problem** | Sprint documents are used by developers to understand what was done and what is in progress. If they show "Pending" for work that is complete, developers will either redo the work or waste time investigating why the criterion appears unmet. |
| **Recommended fix** | Update sprint docs to reflect actual completion status. Mark SPR-020 and SPR-021 as complete. Move resolved backlog items to a "Completed" section. |

---

### CL-025 · `docs/decisions/architecture_decisions.md` and `ADR-0001` Are Redundant

| Field | Detail |
|-------|--------|
| **Severity** | Low |
| **Files** | `docs/decisions/architecture_decisions.md`, `docs/decisions/ADR-0001-economy-items-schema.md` |
| **Problem** | Two decision documents exist in the same directory covering overlapping scope. A `README.md` in `docs/decisions/` is not present to explain the structure. |
| **Why it is a problem** | Without a `README.md` index, new contributors don't know which document is canonical. If ADR format is the standard, `architecture_decisions.md` should be numbered (ADR-0000). |
| **Recommended fix** | Add `docs/decisions/README.md` listing all ADRs and their status. Rename `architecture_decisions.md` to `ADR-0000-initial-architecture.md` for consistency. |

---

### CL-026 · `sentinel_spr019/api/database.py` Does Not Use Context Manager

| Field | Detail |
|-------|--------|
| **Severity** | Low |
| **File** | `sentinel_spr019/api/database.py` |
| **Problem** | `get_connection()` returns a raw `sqlite3.Connection` with no context manager wrapping. The repositories manually call `conn.close()` in `finally` blocks. |
| **Why it is a problem** | While the `try/finally` pattern prevents connection leaks, it is not idiomatic Python. `sqlite3.Connection` is itself a context manager — `with sqlite3.connect(db_path) as conn:` provides automatic commit/rollback and cleanup. The current pattern scatters resource management logic across 9 repository methods. A bug in any one `finally` block (or a future developer forgetting to add one) causes a leak. |
| **Recommended fix** | Convert `get_connection()` to a `@contextmanager` that yields the connection and handles `conn.close()`. Refactor all 9 repository methods to use `with get_connection() as conn:`. |

---

### CL-027 · `Dockerfile` Has No Layer Caching Optimization

| Field | Detail |
|-------|--------|
| **Severity** | Low |
| **File** | `Dockerfile` |
| **Problem** | The Dockerfile copies the entire project (`COPY . /app`) before running `pip install`. |
| **Why it is a problem** | Docker layer caching is invalidated by the `COPY . /app` layer whenever any source file changes, causing `pip install` to re-run on every build even when `requirements.txt` has not changed. For a project with more dependencies, this significantly slows CI/CD pipelines. |
| **Recommended fix** | Split the copy into two steps: `COPY requirements.txt .` then `RUN pip install ...` then `COPY . .`. This caches the pip install layer and only re-installs when `requirements.txt` changes. |

---

### CL-028 · No Structured Logging Configuration

| Field | Detail |
|-------|--------|
| **Severity** | Low |
| **File** | `sentinel_spr019/api/main.py` |
| **Problem** | No logging configuration is set up at application startup. The `LOGGER = logging.getLogger(__name__)` pattern is used correctly in route handlers and repositories, but no root logger format, level, or handler is configured. |
| **Why it is a problem** | In Docker, default Python logging outputs to stderr with no format. Log lines have no timestamps, no request IDs, and no structured format compatible with log aggregation tools (ELK, Loki, etc.). The `LOGGER.exception(...)` calls in route handlers produce output, but it may not appear depending on Docker log driver configuration. |
| **Recommended fix** | Add `logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")` to `main.py` at startup, or configure JSON-format logging for production. |

---

### CL-029 · `sentinel_v1_schema.sql` Defines Tables Not Referenced in Any Importer or API

| Field | Detail |
|-------|--------|
| **Severity** | Low |
| **Files** | `sentinel_spr019/database/schema/sentinel_v1_schema.sql` (lines 119–268) |
| **Problem** | The schema defines 20+ tables across world/map, player, and server domains (`group_prototypes`, `cluster_instances`, `territory_zones`, `players`, `player_sessions`, etc.) that have no corresponding importer, repository, or API endpoint. |
| **Why it is a problem** | These tables are dead weight in the schema file. Every fresh deployment creates 20+ empty tables that serve no current purpose. While they represent planned future features, they increase cognitive load for anyone trying to understand the database structure. They also make it unclear which tables are production-active versus aspirational. |
| **Recommended fix** | Move the aspirational table definitions to a separate `sentinel_future_schema.sql` file and apply them only when the corresponding importers/APIs are implemented. Or add inline SQL comments clearly marking each table group as `-- FUTURE: not yet implemented`. |

---

### CL-030 · `docs/decisions/README.md` Missing

| Field | Detail |
|-------|--------|
| **Severity** | Low |
| **File** | `docs/decisions/` directory |
| **Problem** | The `docs/decisions/` directory contains 2 files but no `README.md` index. |
| **Why it is a problem** | Without an index, new contributors don't know how to discover or create new ADRs. The `docs/sprints/README.md` exists and sets the right precedent, but `decisions/` lacks one. |
| **Recommended fix** | Add `docs/decisions/README.md` listing all ADRs in the format used by `docs/copilot-audits/README.md`. |

---

*Last updated: 2026-06-20 · Full repository audit*
