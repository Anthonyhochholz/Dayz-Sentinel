# DayZ Sentinel — Project Status

> **Version:** 0.4.0 (SPR-021)  
> **Last Updated:** 2026-06-20  
> **Audit Date:** 2026-06-20  
> **Status:** Active Development — Security & API Stability Sprint in Progress (SPR-020/021)

---

## Feature Status by Category

### ✅ COMPLETED

| Feature | Details |
|---------|---------|
| Economy items API (GET list, search, count, by-name) | 4 endpoints live, 1,917 items |
| Economy events API (GET list, search, count, by-name) | 3 read endpoints live, 58 events |
| Economy events toggle-active endpoint | `POST /events/{name}/toggle-active` works (no auth yet) |
| `types_importer.py` — full XML import pipeline | Upsert strategy, full transaction, flags + relations |
| `events_importer.py` — basic XML import | Insert-only (no upsert on re-import — see IN PROGRESS) |
| SQLite schema v1 + rev2 | 20+ tables defined; economy domain populated |
| Docker + Docker Compose setup | Single-container, volume-mounted DB |
| pytest unit tests for types_importer | 21 tests, 100% passing |
| Integration smoke test runner | `scripts/test_api.py` (requires running server) |
| README endpoint documentation | Correct paths, response values |
| `dict_factory` centralized in `database.py` | No duplicates in repository files |
| `offset` pagination in search() | Both repositories support OFFSET in SQL |
| `requests` in `requirements.txt` | Dependency present |
| Dead code (`economy_repository.py`) removed | Deleted in SPR-021 |
| f-String SQL replaced with conditional queries | `economy_events_repository.py` safe |
| Generic HTTP 500 responses (no `str(e)`) | 500 paths return "Internal server error" |
| DB connection `try/finally` cleanup | All 9 repository methods close connections |
| `API_PORT` in Docker port mapping | `docker-compose.yml` uses `${API_PORT:-8000}` |
| Documentation: ARCHITECTURE.md, CHANGELOG.md | Present and up-to-date |
| ADR-0001 (economy items schema decision) | Documented in `docs/decisions/` |

---

### 🔄 IN PROGRESS

| Feature | Status | Blocker |
|---------|--------|---------|
| SPR-020 integration testing sprint | Acceptance criteria partially met (some P1 fixed; no TestClient tests yet) | No FastAPI TestClient tests created |
| HTTP 500 response sanitization | 500 paths fixed; 404 path in `toggle_event_active` still uses `str(e)` | 1 residual defect |
| DB connection context manager | `try/finally` in place but `@contextmanager` wrapper not implemented | Architecture debt |
| `.env` loading | Docker port mapping works; Python app never calls `load_dotenv()` | `python-dotenv` missing from requirements |

---

### ⚠️ PARTIALLY IMPLEMENTED

| Feature | What's Done | What's Missing |
|---------|------------|----------------|
| `events_importer.py` | Parses events.xml, inserts all 12 fields, handles IntegrityError | No upsert on re-import (stale data on re-run), no logging, no transaction rollback |
| Economy event metadata | Schema defines `economy_event_flags`, `_secondary`, `_children` | `events_importer.py` does not populate these tables |
| Schema migration | Two SQL files exist | No runner, no migration tracking, manual application required |
| API response schemas | Pydantic models defined (6 classes) | Models imported by nothing — all routes use `response_model=dict` |

---

### 🚫 ABANDONED

| Feature | Evidence | Notes |
|---------|---------|-------|
| Sprint-based package naming (`sentinel_spr019`) | ROADMAP P2-006 to rename, no progress | Architectural decision that was a mistake from the start; costs effort to fix but no one has done it |

---

### 📋 NOT STARTED

| Feature | Priority | Notes |
|---------|----------|-------|
| **API-Key authentication for toggle-active** | 🔴 P1-CRITICAL | Single biggest production blocker. All prerequisites identified. |
| CORS middleware | 🟡 P3-001 | Blocks Web UI |
| Player log import pipeline | 🟡 P3-003 | Schema exists; importer not written |
| Server session log import | 🟡 P3-004 | Schema exists; importer not written |
| Damage event import + analytics endpoint | 🟡 P3-005 | Schema exists; no importer or API |
| FastAPI TestClient integration tests | 🟠 P2 | `tests/test_types_importer.py` only; no route tests |
| Tests for `events_importer.py` | 🟠 High | 0 tests vs 21 for types_importer — asymmetric coverage |
| Pinned dependency versions | 🟠 P2-008 | `requirements.txt` has 3 unpinned packages |
| Package rename (`sentinel` from `sentinel_spr019`) | 🟠 P2-006 | Breaking change requiring all import updates |
| Typed OpenAPI response schemas | 🟡 P3-007 | Replace `response_model=dict` |
| Rate limiting (`slowapi`) | 🟡 P3-008 | No DoS protection |
| Schema migration tooling | 🟡 P3-006 | `scripts/db_init.py` or Alembic |
| Remove `sentinel.db` from git | 🔴 Critical | Binary DB file committed; not in `.gitignore` |
| Web UI dashboard | 💡 Future | Also blocked by CORS |
| PostgreSQL backend option | 💡 Future | |
| WebSocket real-time log streaming | 💡 Future | |
| Discord bot integration | 💡 Future | |
| Map visualization (heat-map) | 💡 Future | |

---

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Current Features](#2-current-features)
3. [Missing Features](#3-missing-features)
4. [Technical Debt](#4-technical-debt)
5. [Bugs](#5-bugs)
6. [TODO List](#6-todo-list)

---

## 1. Architecture Overview

### Project Type

FastAPI-based REST API for DayZ server administration and analytics. Ingests DayZ economy XML files (`types.xml`, `events.xml`), stores data in SQLite, and exposes query/management endpoints.

### High-Level Data Flow

```
HTTP Client → FastAPI (uvicorn:8000) → Routes → Repositories → SQLite Database
                                         ↓
                                      Models (Pydantic)

XML Files → Importers → SQLite Database
```

### Key Components

| Layer | Location | Responsibility |
|---|---|---|
| **API Entry** | `sentinel_spr019/api/main.py` | FastAPI app creation, router registration |
| **Database** | `sentinel_spr019/api/database.py` | SQLite connection factory + `dict_factory` |
| **Routes** | `sentinel_spr019/api/routes/` | HTTP endpoint handlers (2 router files, ~9 endpoints) |
| **Repositories** | `sentinel_spr019/api/repositories/` | Data access layer, parameterized SQL queries |
| **Models** | `sentinel_spr019/api/models/` | Pydantic schemas for economy items and events |
| **Importers** | `sentinel_spr019/importer/economy/` | XML → SQLite pipeline (`types_importer.py`, `events_importer.py`) |
| **Database Schema** | `sentinel_spr019/database/schema/` | SQL DDL files (`sentinel_v1_schema.sql`, `rev2.sql`) |
| **Tests** | `tests/` | pytest unit tests (21 tests, 100% passing) |
| **Scripts** | `sentinel_spr019/scripts/` | Dev utilities (`test_api.py`, `test_import_run.py`) |
| **Docs** | `docs/` | Sprint reports, audits, architecture decisions |

### Technology Stack

| Concern | Technology |
|---|---|
| Web Framework | FastAPI + Uvicorn |
| Database | SQLite (file: `sentinel_spr019/database/sqlite/sentinel.db`) |
| Data Validation | Pydantic v2 |
| XML Parsing | `xml.etree.ElementTree` (stdlib) |
| Testing | pytest + in-memory SQLite fixtures |
| Deployment | Docker / Docker Compose |
| Python Version | 3.11 |

### Directory Structure

```
Dayz-Sentinel/
├── sentinel_spr019/            # Main package (name coupled to sprint number)
│   ├── api/
│   │   ├── main.py             # FastAPI app entrypoint
│   │   ├── database.py         # Connection factory + dict_factory
│   │   ├── models/
│   │   │   ├── economy_item.py
│   │   │   └── economy_event.py
│   │   ├── repositories/
│   │   │   ├── economy_items_repository.py
│   │   │   └── economy_events_repository.py
│   │   └── routes/
│   │       ├── economy_items.py
│   │       └── economy_events.py
│   ├── importer/
│   │   └── economy/
│   │       ├── types_importer.py   # types.xml → economy_items (1,917 items)
│   │       └── events_importer.py  # events.xml → economy_events (58 events)
│   ├── scripts/
│   │   ├── test_api.py             # Integration smoke tests
│   │   └── test_import_run.py      # Importer bootstrap script
│   └── database/
│       ├── schema/
│       │   ├── sentinel_v1_schema.sql
│       │   └── rev2.sql
│       └── sqlite/
│           └── sentinel.db         # Live SQLite database (135 KB)
├── tests/
│   └── test_types_importer.py      # 21 unit tests
├── docs/                           # Sprint reports, ADRs, audits
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
└── README.md
```

### Database Schema Summary

The schema defines 20+ tables across four domains. Only the Economy domain is currently populated.

| Domain | Tables | Status |
|---|---|---|
| **Economy** | `economy_items`, `economy_events`, `economy_item_flags`, `economy_item_categories`, `economy_item_usages`, `economy_item_values`, `economy_item_tags` | ✅ Populated (1,917 items, 58 events) |
| **World/Map** | `world_groups`, `world_clusters`, `world_territories` | Schema defined, no data |
| **Player** | `players`, `player_sessions`, `player_positions`, `player_damage_events` | Schema defined, no data |
| **Server/Logging** | `server_sessions`, `script_sessions`, `server_logs` | Schema defined, no data |

---

## 2. Current Features

### REST API (`/api/v1/`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Health check → `{"status": "ok"}` |
| `GET` | `/api/v1/economy/items` | Paginated item list (params: `limit`, `offset`, `search`) |
| `GET` | `/api/v1/economy/items/{item_name}` | Single item lookup by name |
| `GET` | `/api/v1/economy/items/stats/count` | Total item count |
| `GET` | `/api/v1/economy/events` | Paginated event list (params: `limit`, `offset`, `search`, `active_only`) |
| `GET` | `/api/v1/economy/events/{event_name}` | Single event lookup by name |
| `POST` | `/api/v1/economy/events/{event_name}/toggle-active` | Toggle event active/inactive |
| `GET` | `/api/v1/economy/events/stats/count` | Event count (supports `active_only` filter) |

### Data Import Pipeline

- **Types Importer** (`types_importer.py`) — Parses `types.xml`, upserts 1,917 economy items with full relational breakdown (categories, usages, values, tags, flags). Full transaction wrapping with rollback on error. Auto-handles legacy column rename migration.
- **Events Importer** (`events_importer.py`) — Parses `events.xml`, upserts 58 economy events with all fields (nominal, min/max counts, lifetime, restock, radii, modes, active status).

### Infrastructure & Deployment

- Docker image (`python:3.11-slim`) with volume mount for the SQLite database
- `docker-compose.yml` for single-command startup
- `.env.example` with `TZ` and `API_PORT` placeholders
- CasaOS installation guide (`CASAOS_INSTALL.md`)

### Testing

- 21 pytest unit tests for `types_importer.py` — 100% passing
- In-memory SQLite fixtures for reproducible, isolated tests
- Integration smoke test runner (`scripts/test_api.py`)

### Documentation

- `README.md` — Setup, usage, endpoint reference
- `docs/ARCHITECTURE.md` — Component diagrams and design rationale
- `docs/CHANGELOG.md` — Version history
- `docs/` — Sprint reports (SPR-019, SPR-020, SPR-021), code quality audit, security audit, ADR-0001

---

## 3. Missing Features

### Security (P1 — Critical, SPR-020 In Progress)

- ❌ **API-Key authentication** on the `toggle-active` write endpoint — anyone on the network can change event states
- ❌ **Generic error responses** — internal exceptions are currently serialized and sent to clients
- ❌ **`.env` loading** — `python-dotenv` not installed; `API_PORT` and future secrets like `SENTINEL_API_KEY` are silently ignored

### Code Quality & API Correctness (P2 — SPR-021 Planned)

- ❌ `offset` pagination parameter is accepted by the items search route but ignored in the repository query (see Bug #1)
- ❌ `requests` library is used in `scripts/test_api.py` but missing from `requirements.txt`
- ❌ Dependency versions unpinned in `requirements.txt` — breaking upstream releases could silently break builds
- ❌ Package named `sentinel_spr019` couples to a sprint number — all imports break on each package rename

### Database Management (P3 — Future)

- ❌ No schema migration tooling — fresh deployments require manually applying two SQL files in order
- ❌ Schema file (`sentinel_v1_schema.sql`) does not match the live database (column `item_name` vs `name`)
- ❌ CORS middleware not configured — required before any web UI can call the API

### Analytics & Data Pipelines (P3 — Future)

- ❌ Player log import pipeline (schema exists, importer not written)
- ❌ Server session log import (schema exists, importer not written)
- ❌ Damage event import + analytics endpoint
- ❌ Script error log parsing

### API & Developer Experience (P3 — Future)

- ❌ Typed Pydantic `response_model` on all routes — currently `response_model=dict`, disabling OpenAPI schema generation
- ❌ Repositories return raw `dict` instead of Pydantic model instances
- ❌ Rate limiting

### Future / Under Discussion

- ❌ Web UI dashboard for event management
- ❌ PostgreSQL backend option for high-traffic deployments
- ❌ WebSocket real-time log streaming
- ❌ Discord bot integration for event notifications
- ❌ Player-position heat-map visualization
- ❌ Scheduled XML re-import from configured paths

---

## 4. Technical Debt

### 🔴 Critical

| ID | Location | Issue |
|---|---|---|
| **SEC-001** | `routes/economy_events.py:77–98` | `POST toggle-active` has **no authentication** — unauthenticated write endpoint |
| **SEC-002** | `routes/economy_events.py:94–95`, `routes/economy_items.py:43,66,80` | `HTTPException(detail=str(e))` **leaks DB paths, table names, and SQLite internals** to clients |
| **SEC-003** | `repositories/economy_events_repository.py:36–44, 103–114` | f-String SQL interpolation (`f"... {where_clause}"`) — currently low-risk but violates parameterized-query policy and is flagged by security linters (Bandit) |
| **SEC-004** | `docker-compose.yml`, `api/main.py` | `.env` is **never loaded** — `env_file` directive missing from docker-compose; no `load_dotenv()` in app startup |

### 🟠 High

| ID | Location | Issue |
|---|---|---|
| **ARCH-002** | All repository methods (9 total) | DB connections managed with explicit `try/finally conn.close()` instead of a context manager — not idiomatic Python and fragile |
| **ARCH-003** | `database/schema/sentinel_v1_schema.sql:5` vs `repositories/economy_items_repository.py:33` | Schema DDL file defines column `item_name`; live DB and all code use `name` — **schema file is stale** |
| **CQ-003** | `requirements.txt` | `requests` package used in `scripts/test_api.py` but **not listed as a dependency** |

### 🟡 Medium

| ID | Location | Issue |
|---|---|---|
| **ARCH-001** | `Dockerfile:6`, `docker-compose.yml:4`, all `import` statements | Package named `sentinel_spr019` — **name couples to sprint number**; every rename breaks 10+ import paths |
| **ARCH-004** | `database/schema/` | Two schema files with no runner — **no reproducible migration path** for fresh deployments |
| **CQ-005** | `requirements.txt:1–3` | `fastapi`, `uvicorn[standard]` have **no version pins** — silent breakage risk |
| **CQ-007** | `routes/*.py` (all 7+ route handlers) | All routes declare `response_model=dict` — **disables OpenAPI schema generation** and response validation |

### 🔵 Low

| ID | Location | Issue |
|---|---|---|
| **CQ-006** | `README.md:75–77, 88` | Health endpoint documented as `/health` (should be `/api/v1/health`); response value documented as `"operational"` (should be `"ok"`); non-existent `?type=weapon` query parameter documented |
| **CQ-008** | `repositories/economy_events_repository.py:2`, `repositories/economy_items_repository.py:2` | Unused Pydantic model imports (`EconomyEvent`, `EconomyEventResponse`) — repositories return `dict`, not model instances |
| **CQ-009** | `routes/*.py` | `async` route handlers call synchronous repository/SQLite operations without `run_in_executor` — blocks the event loop under concurrent load |

---

## 5. Bugs

### Bug #1 — `offset` Parameter Ignored in Search (Medium)

**Files:** `routes/economy_items.py:11–43`, `repositories/economy_items_repository.py:77–108`

The `/economy/items` route accepts an `offset` query parameter, includes it in the JSON response, and passes it to `EconomyItemsRepository.search()`. However, the `search()` method signature only accepts `query` and `limit` — `offset` is silently dropped. The SQL query has no `OFFSET` clause. Result: search pagination is broken; the same first page is always returned regardless of the `offset` value sent by the client.

```python
# routes/economy_items.py — passes offset
items = EconomyItemsRepository.search(search, limit, offset)  # 3 args

# repositories/economy_items_repository.py — ignores offset
def search(query: str, limit: int = 50) -> List[dict]:  # only 2 params
    cursor.execute("SELECT ... LIMIT ?", (f"%{query}%", limit))  # no OFFSET
```

---

### Bug #2 — Internal Error Details Leaked to Clients (Critical / Security)

**Files:** `routes/economy_events.py:93–96`, `routes/economy_items.py:68–70`

All `except Exception as e` blocks in route handlers pass `str(e)` directly into `HTTPException(detail=...)`. This serializes raw SQLite exception messages (which contain table names, file paths, and column names) into API responses visible to any caller.

```python
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))  # leaks internals
```

---

### Bug #3 — `toggle-active` Endpoint Has No Authentication (Critical / Security)

**File:** `routes/economy_events.py:77–98`

The `POST /api/v1/economy/events/{event_name}/toggle-active` endpoint performs a write operation with zero authentication. Any client that can reach the API port can disable or re-enable any DayZ server event (zombie spawns, vehicle spawns, contaminated zones, etc.).

---

### Bug #4 — `.env` Variables Never Loaded (High / Configuration)

**Files:** `docker-compose.yml`, `api/main.py`, `requirements.txt`

`docker-compose.yml` references `${API_PORT:-8000}` in the ports mapping but does not include `env_file: .env`. The Python application has no `python-dotenv` dependency and never calls `load_dotenv()`. The documented `.env`-based configuration workflow does not function — `API_PORT` always resolves to `8000`, and future secrets (`SENTINEL_API_KEY`) would be silently ignored at runtime.

---

### Bug #5 — f-String SQL in Events Repository (High / Security Pattern)

**File:** `repositories/economy_events_repository.py:36–44, 103–114, 127–131`

The `active_only` boolean is used to build a raw SQL `WHERE` clause via an f-string before passing it to `cursor.execute()`. While the current source of the value is a typed `bool`, this pattern is flagged by Bandit and creates a risky precedent if the pattern is extended to accept user-controlled filter strings in the future.

```python
where_clause = "WHERE active = 1" if active_only else ""
cursor.execute(f"SELECT COUNT(*) FROM economy_events {where_clause}")
```

---

### Bug #6 — Unused Model Imports (Low / Code Quality)

**Files:** `repositories/economy_items_repository.py:2`, `repositories/economy_events_repository.py:2`

Both repository files import Pydantic model classes (`EconomyItem`, `EconomyEvent`, `EconomyEventResponse`) that are never used — repositories return raw `dict` objects. These dead imports cause linter warnings and mislead maintainers about the intended return types.

---

## 6. TODO List

### 🔴 P1 — Critical / Security

- [ ] **P1-001** Add API-Key authentication to `POST /api/v1/economy/events/{event_name}/toggle-active`
  - Create `sentinel_spr019/api/auth.py` with `get_api_key` FastAPI dependency
  - Add `SENTINEL_API_KEY` to `.env.example`
  - Apply `Depends(get_api_key)` to the toggle route

- [ ] **P1-002** Replace `detail=str(e)` with generic error messages in all route `except` blocks
  - Log the full exception server-side
  - Return `"An internal server error occurred."` to the client
  - Affected files: `routes/economy_items.py:43,66,80`, `routes/economy_events.py:47,70,92,111`

- [ ] **P1-003** Replace f-String SQL with parameterized queries in `economy_events_repository.py`
  - Use conditional parameter binding instead of string interpolation
  - Affected lines: `economy_events_repository.py:30, 36–44, 103–114, 127–131`

- [ ] **P1-004** Load `.env` at application startup
  - Add `python-dotenv` to `requirements.txt`
  - Call `load_dotenv()` at the top of `api/main.py`
  - Add `env_file: .env` directive to `docker-compose.yml`

- [ ] **P1-005** Wrap SQLite connections in a context manager
  - Refactor `api/database.py` with `@contextmanager def get_connection()`
  - Update all 9 repository methods to use `with get_connection() as conn:`

### 🟠 P2 — High / Code Quality

- [ ] **P2-001** Fix `offset` pagination in `economy_items` search
  - Update `EconomyItemsRepository.search()` signature to accept `offset: int = 0`
  - Add `OFFSET ?` to the SQL query
  - Verify `economy_events` search has the same fix

- [ ] **P2-002** Add `requests` to `requirements.txt`

- [ ] **P2-003** Pin all dependency versions in `requirements.txt`
  - `fastapi`, `uvicorn[standard]`, `requests`, `python-dotenv`

- [ ] **P2-004** Remove unused Pydantic model imports from both repository files

- [ ] **P2-005** Add integration tests for all API route handlers
  - Use FastAPI `TestClient` + in-memory SQLite fixture
  - Cover happy paths and 404/500 edge cases

- [ ] **P2-006** Rename package `sentinel_spr019` → `sentinel` (breaking change, plan carefully)
  - Update `Dockerfile`, `docker-compose.yml`, `pytest.ini`, and all `import` statements

### 🟡 P3 — Medium / Features & Polish

- [ ] **P3-001** Add CORS middleware with configurable allowed origins
  - Use `CORSMiddleware` from `fastapi.middleware.cors`
  - Read allowed origins from `.env`

- [ ] **P3-002** Fix README inaccuracies
  - Health endpoint: `/health` → `/api/v1/health`
  - Health response value: `"operational"` → `"ok"`
  - Remove non-existent `?type=weapon` query parameter

- [ ] **P3-003** Replace `response_model=dict` with typed Pydantic response models on all routes
  - Create `models/responses.py` with `PaginatedItemsResponse`, `PaginatedEventsResponse`, etc.
  - Enables OpenAPI schema validation and `/docs` response schemas

- [ ] **P3-004** Sync `sentinel_v1_schema.sql` with live database column names
  - Rename `item_name` → `name`, etc.
  - Or replace both schema files with a single authoritative DDL

- [ ] **P3-005** Add schema migration tooling
  - Create `scripts/db_init.py` that applies schema files in order on startup
  - Or integrate Alembic for versioned migrations

- [ ] **P3-006** Implement player log import pipeline
  - Create `importer/player/player_importer.py`
  - Target tables: `players`, `player_sessions`, `player_positions`

- [ ] **P3-007** Implement server session log import
  - Create `importer/server/session_importer.py`
  - Target tables: `server_sessions`, `script_sessions`

- [ ] **P3-008** Implement damage event import and analytics endpoint
  - Create `importer/events/damage_importer.py`
  - New endpoint: `GET /api/v1/analytics/damage`

- [ ] **P3-009** Add rate limiting via `slowapi`

- [ ] **P3-010** Make repositories return Pydantic model instances instead of raw `dict`

### 💡 Future / Under Discussion

- [ ] Web UI dashboard for event management
- [ ] PostgreSQL backend support for high-traffic deployments
- [ ] WebSocket endpoint for real-time log streaming
- [ ] Discord bot integration for event notifications
- [ ] Player-position heat-map visualization
- [ ] Scheduled automatic XML re-import from configured server paths

---

## Summary

| Category | Rating | Notes |
|---|---|---|
| **Architecture** | 🟢 Solid | Clean route → repository → DB layering; minor connection management anti-patterns |
| **Security** | 🔴 Critical Issues | Unauthenticated write endpoint, error detail leakage, env not loaded |
| **Code Quality** | 🟡 Mixed | Tests passing (21/21), good docstrings; unused imports, no version pinning, stale schema file |
| **Database** | 🟢 Good | Comprehensive schema (20+ tables); economy data fully loaded; schema/code mismatch in DDL file |
| **Documentation** | 🟢 Excellent | ARCHITECTURE.md, audits, sprint reports all present; README has minor inaccuracies |
| **Testing** | 🟢 Good | 21 unit tests (100% passing); no API route integration tests yet |
| **Deployment** | 🟡 Mostly Ready | Docker/Compose functional; env loading fix required before secrets work |
