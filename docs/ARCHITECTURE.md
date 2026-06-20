# Architecture — DayZ Sentinel

## System Overview

DayZ Sentinel is a single-service FastAPI application that imports DayZ XML configuration data into SQLite and exposes the stored data over HTTP.

```text
DayZ XML files -> Importers -> SQLite -> FastAPI routes -> HTTP clients
```

## Runtime Topology

```text
┌──────────────────────────────────────────────────────┐
│ Docker container / local Python process             │
│                                                      │
│  uvicorn                                             │
│    -> FastAPI app (`sentinel_spr019/api/main.py`)   │
│       -> item routes                                │
│       -> event routes                               │
│       -> repository layer                           │
│       -> SQLite connection factory                  │
└──────────────────────────────────────────────────────┘
                         │
                         ▼
              `sentinel_spr019/database/sqlite/sentinel.db`
```

## Application Layers

| Layer | Primary paths | Responsibility |
|------|---------------|----------------|
| Entrypoint | `sentinel_spr019/api/main.py` | FastAPI app creation and router registration |
| Routes | `sentinel_spr019/api/routes/` | HTTP parameter handling and response shaping |
| Models | `sentinel_spr019/api/models/` | Pydantic response/data models |
| Repositories | `sentinel_spr019/api/repositories/` | SQLite queries and persistence operations |
| Importers | `sentinel_spr019/importer/economy/` | XML parsing and database population |
| Schema | `sentinel_spr019/database/schema/` | Database DDL |
| Tests | `tests/` | Automated validation, currently focused on the types importer |

## Core Data Flows

### Read flow

1. A client calls an `/api/v1/economy/...` GET endpoint.
2. The route validates query/path parameters.
3. The route calls a repository method.
4. The repository opens SQLite through `get_connection()` and returns rows as dictionaries.
5. FastAPI serializes the response.

### Write flow

1. A client calls `POST /api/v1/economy/events/{event_name}/toggle-active`.
2. The event repository reads the current `active` value.
3. The repository flips the value and commits the update.
4. The route returns the new state.

### Import flow

1. `types_importer.py` parses `types.xml` and upserts `economy_items` plus related metadata tables.
2. `events_importer.py` parses `events.xml` and inserts rows into `economy_events`.
3. Importers operate out-of-band from the HTTP API.

## Database Domains

| Domain | Status | Notes |
|--------|--------|-------|
| Economy items | Implemented | API and importer are live |
| Economy events | Implemented | API and importer are live |
| Economy metadata tables | Partially implemented | Item metadata is populated; event metadata tables remain unused |
| Player/session data | Schema only | Tables exist without importers or endpoints |
| Server/script logging | Schema only | Tables exist without importers or endpoints |
| Import tracking | Schema only | `import_sources` and `import_runs` exist but are not yet wired in |

## Architectural Constraints and Gaps

| Area | Current fact |
|------|--------------|
| Storage model | SQLite is the only database backend in the current implementation |
| Configuration | The application has no centralized settings layer |
| Route execution | Route handlers are declared `async` while repository work is synchronous |
| API contracts | Routes still use `response_model=dict` instead of the existing typed models |
| Package naming | The package root remains sprint-coupled: `sentinel_spr019` |
| Write security | No authentication layer exists for the toggle-active endpoint |
