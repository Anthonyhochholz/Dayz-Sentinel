# Architecture — DayZ Sentinel

## System Overview

DayZ Sentinel is evolving from an economy-only import API into a DayZ Server Intelligence Platform. The current runtime is still a single-service FastAPI application backed by SQLite, but the target architecture expands ingestion from individual XML files to complete DayZ server mirrors plus operational logs.

```text
DayZ server mirror -> Mirror Scanner -> File Discovery Engine -> Import Pipeline
                  -> Parser Registry -> SQLite -> FastAPI routes / Analytics / Dashboard
```

## Runtime Topology

```text
┌──────────────────────────────────────────────────────┐
│ Docker container / local Python process             │
│                                                      │
│  Mirror Scanner                                      │
│    -> File Discovery Engine                          │
│    -> Import Pipeline                                │
│       -> Parser Registry                             │
│          -> economy XML parsers                      │
│          -> cluster XML parsers                      │
│          -> spawn XML parsers                        │
│          -> world XML parsers                        │
│          -> ADM / RPT / generic log parsers          │
│    -> Analytics Engine                               │
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
| Mirror ingestion | Planned | Mirror scanning, file discovery, import orchestration, and parser selection |
| Analytics | Planned | Derived metrics, cross-file correlation, and dashboard-facing read models |
| Schema | `sentinel_spr019/database/schema/` | Database DDL |
| Tests | `tests/` | Automated validation, currently focused on the types importer |

## Core Data Flows

### API read flow

1. A client calls an `/api/v1/economy/...` GET endpoint.
2. The route validates query/path parameters.
3. The route calls a repository method.
4. The repository opens SQLite through `get_connection()` and returns rows as dictionaries.
5. FastAPI serializes the response.

### API write flow

1. A client calls `POST /api/v1/economy/events/{event_name}/toggle-active`.
2. The event repository reads the current `active` value.
3. The repository flips the value and commits the update.
4. The route returns the new state.

### Mirror import flow

1. A mirror root is provided to the Mirror Scanner.
2. The File Discovery Engine enumerates supported files and classifies them by type.
3. The Import Pipeline records source metadata and dispatches each file through the Parser Registry.
4. The selected parser normalizes data into platform tables and import tracking tables.
5. The Analytics Engine derives higher-level intelligence from imported economy, world, cluster, and log data.
6. API routes and the future dashboard consume normalized and derived data from SQLite.

### Supported file categories

| Category | Example role in platform |
|----------|--------------------------|
| Economy XML | Item and event balancing, economy metadata |
| Cluster XML | Object/group placement and clustering intelligence |
| Spawn XML | Spawn definitions and territory-related import data |
| World XML | Static world objects, map context, and environment state |
| ADM logs | Administrative actions, player/session events, server operations |
| RPT logs | Runtime diagnostics, script/runtime errors, operational telemetry |
| Generic log files | Extensible catch-all source for future parser plugins |

## Database Domains

| Domain | Status | Notes |
|--------|--------|-------|
| Economy items | Implemented | API and importer are live |
| Economy events | Implemented | API and importer are live |
| Economy metadata tables | Partially implemented | Item metadata is populated; event metadata tables remain unused |
| Cluster and world data | Schema only | Cluster, map, and territory tables exist without importers |
| Player/session data | Schema only | Tables exist without importers or endpoints |
| Server/script logging | Schema only | ADM/RPT-style session and script tables exist without importers or endpoints |
| Import tracking | Schema only | `import_sources` and `import_runs` exist but are not yet wired in |
| Analytics/read models | Planned | No derived intelligence layer exists yet |

## Architectural Constraints and Gaps

| Area | Current fact |
|------|--------------|
| Storage model | SQLite is the only database backend in the current implementation |
| Configuration | The application has no centralized settings layer |
| Route execution | Route handlers are declared `async` while repository work is synchronous |
| API contracts | Routes still use `response_model=dict` instead of the existing typed models |
| Package naming | The package root remains sprint-coupled: `sentinel_spr019` |
| Write security | No authentication layer exists for the toggle-active endpoint |
| Mirror ingestion | No Mirror Scanner, File Discovery Engine, or Import Pipeline is implemented yet |
| Parser dispatch | There is no Parser Registry for non-economy file types |
| Analytics | No Analytics Engine or dashboard-facing aggregation layer exists yet |
