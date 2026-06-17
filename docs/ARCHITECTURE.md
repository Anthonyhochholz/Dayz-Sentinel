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
```

---

## 2. Layer Breakdown

| Layer | Path | Responsibility |
|-------|------|----------------|
| **Entrypoint** | `api/main.py` | FastAPI app setup, router registration |
| **Routes** | `api/routes/economy_items.py` | HTTP handlers, input validation, response shaping |
| | `api/routes/economy_events.py` | HTTP handlers for events, toggle endpoint |
| **Models** | `api/models/economy_item.py` | Pydantic schemas: `EconomyItemBase`, `EconomyItem`, `EconomyItemResponse` |
| | `api/models/economy_event.py` | Pydantic schemas: `EconomyEventBase`, `EconomyEvent`, `EconomyEventResponse` |
| **Repositories** | `api/repositories/economy_items_repository.py` | `get_all()`, `get_by_name()`, `search()`, `get_count()` |
| | `api/repositories/economy_events_repository.py` | `get_all()`, `get_by_name()`, `search()`, `get_count()`, `toggle_active()` |
| **DB Connection** | `api/database.py` | `get_connection()` → `sqlite3.connect(db_path)` |
| **Importer** | `importer/economy/events_importer.py` | XML parse → INSERT INTO `economy_events` |
| **Schema** | `database/schema/sentinel_v1_schema.sql` | Full table definitions |
| | `database/schema/sentinel_v1_schema_rev2.sql` | Delta: import tracking, log events |

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

### 3.3 Import Flow (one-time, manual)

```
DayZ Server Files
  ├── types.xml   ──▶ [types_importer.py — NOT YET IMPLEMENTED]  ──▶ economy_items
  └── events.xml  ──▶ events_importer.import_events(xml_file, db_file) ──▶ economy_events
```

---

## 4. Database Schema

### 4.1 Core Economy Tables

```sql
economy_items
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
  nominal FLOAT
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
| `economy_item_flags` | Count flags per item (cargo, map, player, crafted, deloot) |
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
| `cluster_instances` | 3D cluster positions |
| `map_objects` | Map static objects |
| `territory_files` | Territory file index |
| `territories` | Territory color/config |
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

---

## 5. Configuration

| Variable | Default | Source | Used |
|----------|---------|--------|------|
| `TZ` | `Europe/Berlin` | `.env` | ✅ Docker |
| `API_PORT` | `8000` | `.env` | ⚠️ Hardcoded in `docker-compose.yml` — not read |
| `SENTINEL_API_KEY` | — | `.env` | ❌ Not implemented yet |

---

## 6. Deployment

### Docker Compose (recommended)

```
docker-compose up -d
```

- Image: `python:3.11-slim`
- Exposed port: `8000`
- Volume: `./sentinel_spr019/database/sqlite` → `/app/sentinel_spr019/database/sqlite`
- Restart policy: `unless-stopped`

### Manual

```
uvicorn sentinel_spr019.api.main:app --host 0.0.0.0 --port 8000
```

---

*Last updated: 2026-06-17*
