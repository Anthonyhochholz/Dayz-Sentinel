# Architecture Report — DayZ Sentinel

**Date:** 2026-06-20  
**Auditor:** Copilot Architecture Audit  
**Version:** 0.4.0 (SPR-021)

---

## 1. Current Architecture

DayZ Sentinel is a **single-container, self-hosted REST API**. It ingests DayZ server XML configuration files (`types.xml`, `events.xml`), persists parsed data into a local SQLite database, and exposes that data through a FastAPI/uvicorn HTTP interface.

### Architecture Style

**Layered Monolith** with three explicit tiers:

```
HTTP Client
    │
    ▼
┌─────────────────────────────────────────────┐
│  Transport Layer: uvicorn (ASGI server)      │
├─────────────────────────────────────────────┤
│  Application Layer: FastAPI                  │
│  ├── Routes (HTTP handlers)                  │
│  │   ├── economy_items.py  (5 endpoints)     │
│  │   └── economy_events.py (4 endpoints)     │
│  └── main.py (router registration)           │
├─────────────────────────────────────────────┤
│  Data Access Layer                           │
│  ├── Repositories (SQL query objects)        │
│  │   ├── EconomyItemsRepository              │
│  │   └── EconomyEventsRepository             │
│  └── database.py (connection factory)        │
├─────────────────────────────────────────────┤
│  Persistence Layer: SQLite (sentinel.db)     │
└─────────────────────────────────────────────┘

Separate (out-of-band) import pipeline:
┌─────────────────────────────────────────────┐
│  DayZ XML Files (types.xml, events.xml)      │
│    │                                         │
│    ├── types_importer.py   ──▶ economy_items │
│    └── events_importer.py  ──▶ economy_events│
└─────────────────────────────────────────────┘
```

---

## 2. Folder Structure Explanation

```
Dayz-Sentinel/
│
├── sentinel_spr019/               ← Main Python package (name is sprint-coupled — issue)
│   │
│   ├── __init__.py                ← Empty package marker
│   │
│   ├── api/                       ← FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py                ← App factory: creates FastAPI instance, registers routers
│   │   ├── database.py            ← Single-responsibility: connection factory + dict_factory
│   │   │
│   │   ├── models/                ← Pydantic schemas (⚠ CURRENTLY UNUSED — dead code)
│   │   │   ├── __init__.py        ← Comment-only
│   │   │   ├── economy_item.py    ← EconomyItemBase, EconomyItem, EconomyItemResponse
│   │   │   └── economy_event.py   ← EconomyEventBase, EconomyEvent, EconomyEventResponse
│   │   │
│   │   ├── repositories/          ← Data access layer (SQL queries, no business logic)
│   │   │   ├── __init__.py        ← Comment-only
│   │   │   ├── economy_items_repository.py   ← get_all(), get_by_name(), search(), get_count()
│   │   │   └── economy_events_repository.py  ← + toggle_active()
│   │   │
│   │   └── routes/                ← HTTP route handlers (thin controllers)
│   │       ├── __init__.py        ← Comment-only
│   │       ├── economy_items.py   ← GET /api/v1/economy/items (5 endpoints)
│   │       └── economy_events.py  ← GET+POST /api/v1/economy/events (4 endpoints)
│   │
│   ├── importer/                  ← Data import pipeline (⚠ missing __init__.py)
│   │   └── economy/               ← (⚠ missing __init__.py)
│   │       ├── types_importer.py  ← Full upsert importer: types.xml → economy_items
│   │       └── events_importer.py ← Basic insert importer: events.xml → economy_events
│   │
│   ├── database/
│   │   ├── schema/
│   │   │   ├── sentinel_v1_schema.sql      ← Full schema (20+ tables)
│   │   │   └── sentinel_v1_schema_rev2.sql ← Delta: import tracking, log tables
│   │   └── sqlite/
│   │       └── sentinel.db                 ← ⚠ BINARY FILE COMMITTED TO GIT
│   │
│   ├── docs/                      ← Sprint-level docs (⚠ not the main docs/ directory)
│   │   └── (MILESTONE_001_REPORT.md, spr019 report)
│   │
│   └── scripts/
│       ├── test_api.py            ← HTTP integration smoke test (requires running server)
│       └── test_import_run.py     ← Manual import bootstrap script
│
├── tests/
│   └── test_types_importer.py     ← 21 pytest unit tests (types_importer only)
│
├── docs/                          ← Project-level documentation
│   ├── ARCHITECTURE.md            ← Existing architecture doc (superseded by this report)
│   ├── CHANGELOG.md
│   ├── PROJECT_MEMORY.md          ← Single source of truth for project state
│   ├── ROADMAP.md
│   ├── copilot-audits/            ← 8 audit files (partially stale)
│   ├── decisions/                 ← ADR-0001 + architecture_decisions.md
│   └── sprints/                   ← Sprint backlog/sprint files
│
├── Dockerfile                     ← FROM python:3.11-slim; no layer cache optimization
├── docker-compose.yml             ← Single-service compose; port from ${API_PORT:-8000}
├── requirements.txt               ← ⚠ 3 unpinned dependencies
├── pytest.ini                    ← testpaths = tests
├── .env.example                   ← TZ + API_PORT only
├── .gitignore                     ← ⚠ Does not exclude sentinel.db
├── README.md
└── CASAOS_INSTALL.md              ← ⚠ Partially in German; references phantom volume
```

---

## 3. Dependency Flow

### Production (runtime) dependencies:

```
main.py
  ├── fastapi (FastAPI, APIRouter, HTTPException, Query)
  ├── routes/economy_items.py
  │   ├── fastapi (APIRouter, HTTPException, Query)
  │   ├── typing (List, Optional)
  │   └── repositories/economy_items_repository.py
  │       ├── logging (stdlib)
  │       ├── typing (stdlib)
  │       └── api/database.py
  │           ├── sqlite3 (stdlib)
  │           └── pathlib (stdlib)
  └── routes/economy_events.py
      ├── fastapi (APIRouter, HTTPException, Query)
      ├── typing (stdlib)
      └── repositories/economy_events_repository.py
          ├── logging (stdlib)
          ├── typing (stdlib)
          └── api/database.py (same as above)

models/ ← ORPHANED: imported by nothing in the dependency graph above
```

### Import pipeline (manual, one-time):

```
types_importer.py
  ├── logging (stdlib)
  ├── sqlite3 (stdlib)
  └── xml.etree.ElementTree (stdlib)

events_importer.py
  ├── sqlite3 (stdlib)
  └── xml.etree.ElementTree (stdlib)
```

### Key observation

The models layer (`api/models/`) is **completely disconnected from the dependency graph**. It is an isolated island that nothing imports. This is the clearest architectural inconsistency in the codebase.

---

## 4. API Flow

### Read flow (GET endpoints)

```
Client → GET /api/v1/economy/items?search=rifle&limit=10&offset=0
  │
  ▼ FastAPI/uvicorn routes the request
  │
  ▼ economy_items.py::get_items(limit=10, offset=0, search="rifle")
  │  ├── Parameter validation: FastAPI Query() validates types + ranges
  │  └── (No authentication check)
  │
  ▼ EconomyItemsRepository.search("rifle", 10, 0)
  │  ├── get_connection() → sqlite3.connect(sentinel.db)
  │  ├── cursor.execute("SELECT ... FROM economy_items WHERE name LIKE '%rifle%' LIMIT 10 OFFSET 0")
  │  ├── fetchall() → List[dict]
  │  └── conn.close()  [in finally block]
  │
  ▼ Route handler builds response dict:
  │  {"data": [...], "total": len(items), "limit": 10, "offset": 0, "search": "rifle"}
  │  ⚠ NOTE: total = len(items), NOT total DB count — pagination bug
  │
  ▼ FastAPI serializes to JSON → HTTP 200
```

### Write flow (POST endpoint)

```
Client → POST /api/v1/economy/events/ZmbF_Base/toggle-active
  │
  ▼ FastAPI routes the request
  │  ⚠ NO AUTHENTICATION — any client can reach this
  │
  ▼ economy_events.py::toggle_event_active("ZmbF_Base")
  │
  ▼ EconomyEventsRepository.toggle_active("ZmbF_Base")
  │  ├── get_connection() → sqlite3.connect(sentinel.db)
  │  ├── SELECT active FROM economy_events WHERE event_name = ?
  │  ├── if not found: raise Exception("Event ZmbF_Base not found")
  │  ├── new_status = 1 - current
  │  ├── UPDATE economy_events SET active = ? WHERE event_name = ?
  │  ├── conn.commit()
  │  └── conn.close()
  │
  ▼ Route handler catches exception:
  │  if "not found" in str(e): → 404 (with str(e) leaked as detail — security issue)
  │  else: → 500 generic
  │
  ▼ Returns: {"event_name": "ZmbF_Base", "active": false, "message": "Event set to inactive"}
```

### Import flow (manual, out-of-band)

```
DayZ Server
  ├── types.xml ──▶ types_importer.import_types(xml_file, db_file)
  │                  ├── Parse XML with ET
  │                  ├── Ensure/migrate schema
  │                  ├── For each <type>:
  │                  │   ├── UPSERT economy_items
  │                  │   ├── SYNC economy_item_flags
  │                  │   └── SYNC categories/usages/values/tags
  │                  └── COMMIT (or ROLLBACK on error)
  │
  └── events.xml ──▶ events_importer.import_events(xml_file, db_file)
                      ├── Parse XML with ET
                      ├── For each <event>:
                      │   └── INSERT (skip on IntegrityError — no UPDATE path ⚠)
                      └── COMMIT (no rollback on partial failure ⚠)
```

---

## 5. Database Flow

### Active tables (currently populated)

```
economy_items (1,917 rows)
  │ id, name, nominal, lifetime, restock, min_value, max_value
  │
  ├── economy_item_flags (one-to-one, populated by types_importer)
  │     item_id → count_in_cargo, count_in_hoarder, count_in_map, ...
  │
  ├── economy_categories → economy_item_categories (M:N)
  ├── economy_usages → economy_item_usages (M:N)
  ├── economy_values → economy_item_values (M:N)
  └── economy_tags → economy_item_tags (M:N)

economy_events (58 rows: 50 active, 8 inactive)
  │ id, event_name, nominal, min_count, max_count, lifetime, restock,
  │ saferadius, distanceradius, cleanupradius, position_mode, limit_mode, active
  │
  ├── economy_event_flags (defined, empty — events_importer does not populate)
  ├── economy_event_secondary (defined, empty)
  └── economy_event_children (defined, empty)
```

### Defined but empty tables (aspirational schema)

```
World/Map domain:
  group_prototypes, group_categories, group_prototype_categories,
  group_usages, group_prototype_usages, group_tags, group_prototype_tags,
  group_points, group_proxies, cluster_instances, map_objects,
  territory_files, territories, territory_zone_types, territory_zones

Player domain:
  players, player_sessions, player_positions,
  player_damage_events, player_actions

Server/Logging domain (rev2):
  server_sessions, script_sessions, script_engine_events,
  script_logout_events, script_persistence_events, script_errors,
  localization_errors, network_events

Import tracking (rev2):
  import_sources, import_runs
```

### Connection management

- Each repository method calls `get_connection()` (opens a new `sqlite3.connect()`)
- Connection is manually closed in `try/finally` blocks
- No connection pooling (not needed for SQLite single-file, but no context manager)
- SQLite default isolation: deferred transactions; each repository method is its own transaction
- Foreign keys: ENABLED in `types_importer.py` via `PRAGMA foreign_keys = ON`
- Foreign keys: NOT explicitly enabled in `get_connection()` — API queries run without FK enforcement

---

## 6. Missing Architectural Components

### 6.1 Authentication Layer (Critical Gap)

There is no authentication mechanism anywhere in the application. The planned API-key authentication for the `toggle-active` endpoint has been in the roadmap since AUDIT-001 was filed but remains unimplemented. Without an auth layer:
- The architecture cannot support role-based access (read vs. write permissions)
- Adding authentication later requires touching every route
- **Recommended:** Add `sentinel_spr019/api/auth.py` as a FastAPI dependency used across all write endpoints. Future expansion to JWT or OAuth2 can replace the header without changing route signatures.

### 6.2 Service / Business Logic Layer (Architecture Gap)

There is no service layer between routes and repositories. Routes call repositories directly:

```
Current:  Route → Repository → SQLite
Better:   Route → Service → Repository → SQLite
```

The `toggle_active` logic (read-modify-write within the repository) is a business operation that belongs in a service layer, not a data access layer. As the application grows (e.g., validation rules for toggling, side effects like webhook notifications), business logic will accumulate in repositories, violating separation of concerns.

### 6.3 Configuration / Settings Management (Critical Gap)

There is no centralized settings object. Configuration values are:
- Hardcoded in `Dockerfile` (port 8000)
- Read from environment variables manually (currently broken — no `load_dotenv()`)
- Scattered across files

**Recommended:** Create `sentinel_spr019/api/config.py` using Pydantic `BaseSettings` (or `python-dotenv`) to load all configuration from environment variables with typed defaults. All components import from `config.py`.

### 6.4 Error Handling Strategy (Design Gap)

There is no centralized exception hierarchy. Custom exceptions (e.g., `EventNotFoundError`) don't exist. Error handling is:
- Inconsistent: some paths leak `str(e)`, others return generic messages
- Fragile: 404 detection via string matching

**Recommended:** Define custom exception classes in `sentinel_spr019/api/exceptions.py`. Register FastAPI exception handlers in `main.py` using `@app.exception_handler()` to guarantee consistent error response format across all endpoints.

### 6.5 Health Check Completeness (Minor Gap)

`GET /api/v1/health` returns `{"status": "ok"}` unconditionally. It does not check whether the SQLite database is reachable. A health check that returns `ok` even when the DB file is missing or corrupt is misleading to container orchestrators (Docker health checks, Kubernetes probes).

**Recommended:** Add a lightweight `SELECT 1 FROM economy_items LIMIT 1` check to the health endpoint. Return HTTP 503 if it fails.

### 6.6 Request Tracing / Correlation IDs (Observability Gap)

No request IDs are generated or logged. When debugging a specific failed API call from logs, there is no way to correlate the log entry with the request.

**Recommended:** Add middleware that generates a `X-Request-ID` header (or accepts one from the client) and includes it in all log messages.

---

## 7. Suggested Improvements

### Priority 1 — Production Blockers (Must fix before any external exposure)

1. **Add API key authentication** to `toggle-active` (see CLEANUP_REPORT CL-002)
2. **Load `.env`** at startup (see CLEANUP_REPORT CL-003)
3. **Remove `sentinel.db` from git** (see CLEANUP_REPORT CL-001)
4. **Fix search `total` pagination** (see CLEANUP_REPORT CL-011)
5. **Fix route handlers**: convert `async def` to `def` to prevent event loop blocking (see CLEANUP_REPORT CL-005)

### Priority 2 — Structural Improvements (High ROI, low risk)

6. **Wire Pydantic models into routes**: Replace `response_model=dict` with typed schemas. This activates OpenAPI documentation, enables response validation, and makes the existing models/ directory non-dead-code.
7. **Add CORS middleware**: Required before any web UI can call the API.
8. **Centralize error handling**: Add custom exception classes + FastAPI exception handlers.
9. **Add `__init__.py` to importer packages**: Consistency with the rest of the codebase.
10. **Fix `events_importer.py`**: Add upsert strategy, proper logging, transaction wrapping.

### Priority 3 — Architecture Evolution (Future sprints)

11. **Add service layer**: Introduce `api/services/` for business logic as the application grows.
12. **Add Pydantic `BaseSettings`**: Centralize all configuration in `api/config.py`.
13. **Schema migration tooling**: Create `scripts/db_init.py` or integrate Alembic.
14. **Implement remaining data pipelines**: Player/server importers, analytics endpoints.
15. **Rename package**: `sentinel_spr019` → `sentinel` when the import pipeline is stable.
16. **Add health check with DB probe**: Make the health endpoint actually useful for monitoring.

### Architecture Target State

```
sentinel/
├── api/
│   ├── config.py          ← Pydantic BaseSettings (NEW)
│   ├── main.py            ← + load_dotenv(), logging config, exception handlers
│   ├── auth.py            ← API key dependency (NEW — fixes P1-001)
│   ├── exceptions.py      ← Custom exception classes (NEW)
│   ├── database.py        ← @contextmanager get_connection() (refactored)
│   ├── models/            ← Pydantic schemas (WIRED INTO routes)
│   ├── services/          ← Business logic layer (NEW)
│   ├── repositories/      ← Data access layer (unchanged contract)
│   └── routes/            ← def (not async) route handlers (refactored)
├── importer/
│   └── economy/
│       ├── types_importer.py   ← (unchanged)
│       └── events_importer.py  ← (add upsert + logging)
├── scripts/
│   └── db_init.py         ← Schema bootstrapper (NEW)
└── tests/
    ├── test_types_importer.py  ← (existing)
    ├── test_events_importer.py ← (NEW)
    ├── test_api_items.py       ← (NEW)
    └── test_api_events.py      ← (NEW)
```

---

*Last updated: 2026-06-20 · Full repository audit*
