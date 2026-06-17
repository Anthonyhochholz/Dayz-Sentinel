# Architecture — DayZ Sentinel

---

## 1. System Overview

DayZ Sentinel is a single-container, self-hosted REST API. It imports DayZ server configuration files (XML) into a local SQLite database and exposes them via a FastAPI HTTP interface.

```
┌────────────────────────────────────────────────────────┐
│                    Docker Container                    │
│                                                        │
│   HTTP Client ──▶ uvicorn (port 8000)                 │
│                       │                               │
│               ┌───────▼────────┐                      │
│               │   FastAPI App  │  api/main.py          │
│               └───────┬────────┘                      │
│                       │                               │
│         ┌─────────────┴──────────────┐                │
│         ▼                            ▼                │
│  ┌─────────────┐            ┌──────────────┐          │
│  │ Items Router│            │Events Router │          │
│  │ /economy/   │            │ /economy/    │          │
│  │  items      │            │  events      │          │
│  └──────┬──────┘            └──────┬───────┘          │
│         │                          │                  │
│  ┌──────▼──────────────────────────▼───────┐          │
│  │           Repository Layer              │          │
│  │  EconomyItemsRepository                 │          │
│  │  EconomyEventsRepository                │          │
│  └──────────────────┬──────────────────────┘          │
│                     │                                 │
│  ┌──────────────────▼──────────────────────┐          │
│  │        database.py — get_connection()   │          │
│  └──────────────────┬──────────────────────┘          │
│                     │ Volume mount                    │
└─────────────────────┼──────────────────────────────────┘
                      │
            ┌─────────▼──────────┐
            │   sentinel.db      │
            │   (SQLite file)    │
            └────────────────────┘

  One-time Import (manual, external):
  DayZ XML files ──▶ events_importer.py ──▶ sentinel.db
                ──▶ types_importer.py  ──▶ sentinel.db
```

---

## 2. Layer Breakdown

| Layer | Path | Responsibility |
|-------|------|----------------|
| **Entrypoint** | `sentinel_spr019/api/main.py` | FastAPI app setup, router registration |
| **Routes** | `sentinel_spr019/api/routes/economy_items.py` | HTTP handlers, input validation, response shaping |
| | `sentinel_spr019/api/routes/economy_events.py` | HTTP handlers for events, toggle endpoint |
| **Models** | `sentinel_spr019/api/models/economy_item.py` | Pydantic schemas: `EconomyItemBase`, `EconomyItem`, `EconomyItemResponse` |
| | `sentinel_spr019/api/models/economy_event.py` | Pydantic schemas: `EconomyEventBase`, `EconomyEvent`, `EconomyEventResponse` |
| **Repositories** | `sentinel_spr019/api/repositories/economy_items_repository.py` | `get_all()`, `get_by_name()`, `search()`, `get_count()` |
| | `sentinel_spr019/api/repositories/economy_events_repository.py` | `get_all()`, `get_by_name()`, `search()`, `get_count()`, `toggle_active()` |
| | `sentinel_spr019/api/repositories/economy_repository.py` | ⚠️ **Dead code** — `EconomyRepository.get_items()`; not imported or used anywhere (AUDIT-007) |
| **DB Connection** | `sentinel_spr019/api/database.py` | `get_connection()` → `sqlite3.connect(db_path)` — returns raw connection, no context manager (AUDIT-003) |
| **Importer** | `sentinel_spr019/importer/economy/events_importer.py` | XML parse → `INSERT INTO economy_events` |
| | `sentinel_spr019/importer/economy/types_importer.py` | XML parse → upsert into `economy_items` + flags/categories/usages/values/tags |
| **Tests** | `tests/test_types_importer.py` | 21 pytest unit tests for `types_importer` (in-memory SQLite) |
| **Schema** | `sentinel_spr019/database/schema/sentinel_v1_schema.sql` | Full table definitions (original design) |
| | `sentinel_spr019/database/schema/sentinel_v1_schema_rev2.sql` | Delta: import tracking, log/script event tables |

---

## 3. Data Flow

### 3.1 Read Flow (GET request)

```
Client
  └─▶ GET /api/v1/economy/items?limit=50&search=rifle
        └─▶ economy_items.py :: get_items(limit, offset, search)
              └─▶ EconomyItemsRepository.search("rifle", 50)
                    └─▶ get_connection() → sqlite3.connect(sentinel.db)
                          └─▶ SELECT name, nominal, min_value, max_value, restock, lifetime
                              FROM economy_items WHERE name LIKE '%rifle%' LIMIT 50
                                └─▶ List[dict]
                                      └─▶ JSON { data: [...], total: N, limit: 50, offset: 0 }
```

> ⚠️ `offset` is accepted as a query parameter in the search branch but is **not passed** to `EconomyItemsRepository.search()` or `EconomyEventsRepository.search()` — it is silently ignored (AUDIT-010).

### 3.2 Write Flow (POST toggle)

```
Client
  └─▶ POST /api/v1/economy/events/ZmbF_Base/toggle-active
        └─▶ economy_events.py :: toggle_event_active("ZmbF_Base")
              └─▶ EconomyEventsRepository.toggle_active("ZmbF_Base")
                    ├─▶ SELECT active FROM economy_events WHERE event_name = ?
                    └─▶ UPDATE economy_events SET active = 1-current WHERE event_name = ?
                          └─▶ JSON { event_name, active: true/false, message }
```

> ⚠️ No authentication on this endpoint (AUDIT-001).

### 3.3 Import Flow (one-time, manual)

```
DayZ Server Files
  ├── types.xml   ──▶ types_importer.import_types(xml_file, db_file)  ──▶ economy_items + flags/categories/usages/values/tags
  └── events.xml  ──▶ events_importer.import_events(xml_file, db_file) ──▶ economy_events
```

> Both importers are idempotent: re-running with the same file updates existing rows
> (upsert strategy for `types_importer`; skip-on-conflict for `events_importer`).

---

## 4. Database Schema

> ⚠️ **Schema vs. Live DB Discrepancy:** `sentinel_v1_schema.sql` defines `economy_items` with columns `item_name`, `min_count`, `quantmin`, `quantmax`, `cost`. The running API repositories query `name`, `min_value`, `max_value` instead — matching the actual `sentinel.db`. The schema file reflects an earlier iteration that was never updated to match the deployed database.

### 4.1 Core Economy Tables (as queried by the API)

```sql
economy_items  -- columns as used by the live API / repositories
  id INTEGER PK AUTOINCREMENT
  name TEXT NOT NULL UNIQUE       -- item class name
  nominal FLOAT                   -- target spawn count
  min_value FLOAT
  max_value FLOAT
  restock FLOAT                   -- respawn time (minutes)
  lifetime FLOAT                  -- despawn time (seconds)

economy_events
  id INTEGER PK AUTOINCREMENT
  event_name TEXT NOT NULL UNIQUE
  nominal INTEGER
  min_count INTEGER
  max_count INTEGER
  lifetime INTEGER
  restock INTEGER
  saferadius REAL
  distanceradius REAL
  cleanupradius REAL
  position_mode TEXT              -- e.g. "fixed", "random"
  limit_mode TEXT                 -- e.g. "child", "parent"
  active INTEGER                  -- 0 = inactive, 1 = active
```

### 4.2 Relational / Metadata Tables (schema defined, currently unpopulated)

| Table | Purpose |
|-------|---------|
| `economy_item_flags` | Count flags per item (cargo, hoarder, map, player, crafted, deloot) |
| `economy_categories` | Item categories lookup |
| `economy_item_categories` | M:N item ↔ category |
| `economy_usages` | Usage zone types |
| `economy_item_usages` | M:N item ↔ usage |
| `economy_values` | Value zone types |
| `economy_item_values` | M:N item ↔ value |
| `economy_tags` | Tag lookup |
| `economy_item_tags` | M:N item ↔ tag |
| `economy_event_flags` | Deletable, init_random, remove_damaged |
| `economy_event_secondary` | Secondary event spawns |
| `economy_event_children` | Child objects of events |

### 4.3 World / Map Tables

| Table | Purpose |
|-------|---------|
| `group_prototypes` | Spawn group definitions |
| `group_categories` | Group category lookup |
| `group_prototype_categories` | M:N group ↔ category |
| `group_usages` | Group usage lookup |
| `group_prototype_usages` | M:N group ↔ usage |
| `group_tags` | Group tag lookup |
| `group_prototype_tags` | M:N group ↔ tag |
| `group_points` | Spawn point positions within a group |
| `group_proxies` | Proxy object positions within a group |
| `cluster_instances` | 3D cluster positions |
| `map_objects` | Map static objects |
| `territory_files` | Territory file index |
| `territories` | Territory color/config |
| `territory_zone_types` | Zone type lookup |
| `territory_zones` | Zone geometries |

### 4.4 Player / Server Tables

| Table | Purpose |
|-------|---------|
| `players` | Player UID → name index |
| `player_sessions` | Connect/disconnect log |
| `player_positions` | Position history |
| `player_damage_events` | Combat log |
| `player_actions` | Action log |
| `server_sessions` | Server start/version log |

### 4.5 Import Tracking (rev2)

| Table | Purpose |
|-------|---------|
| `import_sources` | Named import source registry |
| `import_runs` | Per-run status (started, finished, status) |

### 4.6 Log / Script Event Tables (rev2)

| Table | Purpose |
|-------|---------|
| `localization_errors` | Missing localization key events |
| `network_events` | Network event log per server session |
| `script_sessions` | Script log file sessions |
| `script_engine_events` | Raw script engine event lines |
| `script_logout_events` | Player logout events from script logs |
| `script_persistence_events` | Persistence events from script logs |
| `script_errors` | Script error events |

---

## 5. Configuration

| Variable | Default | Source | Used |
|----------|---------|--------|------|
| `TZ` | `Europe/Berlin` | `.env.example` | ✅ Docker (must be copied to `.env`) |
| `API_PORT` | `8000` | `.env.example` | ⚠️ Hardcoded in `docker-compose.yml` and `Dockerfile` — `.env` is never loaded (AUDIT-005) |
| `SENTINEL_API_KEY` | — | `.env.example` | ❌ Not implemented yet (AUDIT-001) |

---

## 6. Deployment

### Docker Compose (recommended)

```
docker-compose up -d
```

- Image: `python:3.11-slim`
- Exposed port: `8000` (hardcoded)
- Volume: `./sentinel_spr019/database/sqlite` → `/app/sentinel_spr019/database/sqlite`
- Restart policy: `unless-stopped`

### Manual

```
uvicorn sentinel_spr019.api.main:app --host 0.0.0.0 --port 8000
```

---

## 7. Known Code Issues (Architecture Impact)

| Issue | Location | Impact |
|-------|----------|--------|
| `dict_factory` duplicated | `economy_items_repository.py:128`, `economy_events_repository.py:177` | Should be in `database.py` (AUDIT-006) |
| No context manager on DB connections | All 3 repository files + `database.py` | Connection leaks on unhandled exceptions (AUDIT-003) |
| f-String SQL interpolation | `economy_events_repository.py:30,36–44,107–114,130` | SQL injection risk (AUDIT-004) |
| `response_model=dict` on all routes | All route handlers | No OpenAPI response schema validation |

---

*Last updated: 2026-06-17 · SPR-021 types_importer implemented*
