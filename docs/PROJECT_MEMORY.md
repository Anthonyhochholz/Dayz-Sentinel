# Project Memory — DayZ Sentinel

> This file is the single source of truth for current project state, context, and decisions.
> Update it whenever significant changes are made.

---

## 🏷️ Project Identity

| Field | Value |
|-------|-------|
| **Project Name** | DayZ Sentinel |
| **Repository** | `Anthonyhochholz/Dayz-Sentinel` |
| **Language** | Python 3.11 |
| **Framework** | FastAPI + uvicorn |
| **Database** | SQLite (file-based, volume-mounted) |
| **Deployment** | Docker / Docker Compose / CasaOS |
| **Current Package** | `sentinel_spr019` |

---

## 📊 Current Status

**Date:** 2026-06-17
**Active Milestone:** SPR-020 (Integration Testing & Security Fixes)
**Last Completed:** SPR-019 (Economy Events Persist)

### Component Status

| Component | Status | Notes |
|-----------|--------|-------|
| Core API | ✅ Operational | FastAPI v1 endpoints live |
| Economy Items | ✅ Ready | 1,917 items imported from `types.xml` |
| Economy Events | ✅ Ready | 58 events imported from `events.xml` |
| Database Schema | ✅ Ready | SQLite `sentinel_v1_schema.sql` + `rev2` deployed |
| Docker | ✅ Ready | `Dockerfile` + `docker-compose.yml` present |
| Authentication | ❌ Missing | No auth on write endpoints (AUDIT-001) |
| Tests | 🔶 Partial | `scripts/test_api.py` is a comprehensive HTTP integration suite (requires running API); no `pytest` unit/integration suite with in-memory DB |
| `types_importer.py` | ❌ Missing | Referenced in `test_import_run.py` but not implemented |
| `economy_repository.py` | ⚠️ Dead Code | Exists at `api/repositories/economy_repository.py`; not imported or used anywhere |

---

## 🗄️ Database

- **File location (in container):** `/app/sentinel_spr019/database/sqlite/sentinel.db`
- **Volume mount:** `./sentinel_spr019/database/sqlite` → `/app/sentinel_spr019/database/sqlite`
- **Schema files:** `sentinel_spr019/database/schema/sentinel_v1_schema.sql`, `sentinel_v1_schema_rev2.sql`

> ⚠️ **Schema vs. Live DB Discrepancy:** `sentinel_v1_schema.sql` defines `economy_items` with columns `item_name`, `min_count`, `quantmin`, `quantmax`, `cost`. However, the API repositories query columns `name`, `min_value`, `max_value`, which is what the live `sentinel.db` actually contains. The original schema file reflects an earlier design iteration; the deployed DB schema diverged from it without a migration file.

### Populated Tables

| Table | Rows | Source |
|-------|------|--------|
| `economy_items` | 1,917 | `types.xml` |
| `economy_events` | 58 (50 active, 8 inactive) | `events.xml` |

### Defined but Empty Tables (from schema)

`economy_item_flags`, `economy_categories`, `economy_item_categories`, `economy_usages`,
`economy_item_usages`, `economy_values`, `economy_item_values`, `economy_tags`,
`economy_item_tags`, `economy_event_flags`, `economy_event_secondary`, `economy_event_children`,
`group_prototypes`, `group_categories`, `group_prototype_categories`, `group_usages`,
`group_prototype_usages`, `group_tags`, `group_prototype_tags`, `group_points`, `group_proxies`,
`cluster_instances`, `map_objects`, `territory_files`, `territories`, `territory_zone_types`,
`territory_zones`, `players`, `player_sessions`, `player_positions`, `player_damage_events`,
`player_actions`, `server_sessions`,
`import_sources`, `import_runs` *(rev2)*,
`localization_errors`, `network_events` *(rev2)*,
`script_sessions`, `script_engine_events`, `script_logout_events`, `script_persistence_events`, `script_errors` *(rev2)*

---

## 🔌 API Endpoints (v1)

| Method | Path | Description | Default limit |
|--------|------|-------------|---------------|
| `GET` | `/api/v1/health` | Health check → `{"status": "ok"}` | — |
| `GET` | `/api/v1/economy/items` | List items (pagination + search) | 50 |
| `GET` | `/api/v1/economy/items/{name}` | Get item by name | — |
| `GET` | `/api/v1/economy/items/stats/count` | Total item count | — |
| `GET` | `/api/v1/economy/events` | List events (pagination + search + active_only) | 100 |
| `GET` | `/api/v1/economy/events/{name}` | Get event by name | — |
| `POST` | `/api/v1/economy/events/{name}/toggle-active` | Toggle event active status | — |
| `GET` | `/api/v1/economy/events/stats/count` | Total event count (supports `active_only`) | — |

> ⚠️ Note: `/api/v1/economy/events/stats/count` and `/api/v1/economy/events/{event_name}` share the same path prefix. FastAPI resolves `stats/count` correctly because it is registered before the `{event_name}` route in `economy_events.py`.

---

## 🐛 Known Issues / Open Audit Items

| ID | Severity | Summary | Status |
|----|----------|---------|--------|
| AUDIT-001 | 🔴 Critical | No auth on `toggle-active` POST endpoint | Open |
| AUDIT-002 | 🔴 Critical | Internal error details leaked in HTTP 500 responses (`detail=str(e)` in all route handlers) | Open |
| AUDIT-003 | 🟠 High | DB connection leaks — `get_connection()` returns a raw `sqlite3.Connection`; no context manager; no `try/finally` in repositories | Open |
| AUDIT-004 | 🟠 High | f-String SQL interpolation in `economy_events_repository.py` (lines 30, 36–44, 107–114, 130) — Bandit B608 alert | Open |
| AUDIT-005 | 🟠 High | `API_PORT` defined in `.env.example` and hardcoded in `docker-compose.yml` and `Dockerfile` — `.env` is never loaded | Open |
| AUDIT-006 | 🟡 Medium | `dict_factory` duplicated in `economy_items_repository.py:128` and `economy_events_repository.py:177`; not in `database.py` | Open |
| AUDIT-007 | 🟡 Medium | `economy_repository.py` is dead code — not imported or used anywhere | Open |
| AUDIT-008 | 🟡 Medium | `requests` missing from `requirements.txt` (used in `scripts/test_api.py`) | Open |
| AUDIT-009 | 🟡 Medium | `scripts/test_import_run.py` imports `from importer.economy.types_importer import import_types` — missing package prefix (`sentinel_spr019.`) and `types_importer.py` does not exist | Open |
| AUDIT-010 | 🟡 Medium | `offset` parameter accepted by search routes but ignored in `EconomyItemsRepository.search()` and `EconomyEventsRepository.search()` | Open |
| AUDIT-011 | 🟡 Medium | Package name contains sprint number (`sentinel_spr019`) — not a stable package name | Open |
| AUDIT-012 | 🔵 Low | No CORS middleware | Open |
| AUDIT-013 | 🔵 Low | README contains incorrect endpoint docs | Open |

> Full details: [`copilot-audits/full_project_audit.md`](./copilot-audits/full_project_audit.md)

---

## 🔑 Key Decisions

| Decision | Rationale | ADR |
|----------|-----------|-----|
| SQLite over PostgreSQL | Self-hosted, single-node, no infra overhead | ADR-001 |
| Repository pattern for DB access | Separation of concerns, testability | ADR-002 |
| Sprint-numbered package (`sentinel_spr019`) | Sprint-based iteration tracking | ADR-003 |

> Full ADRs: [`decisions/architecture_decisions.md`](./decisions/architecture_decisions.md)

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | unpinned | Web framework |
| `uvicorn[standard]` | unpinned | ASGI server |
| `requests` | missing ⚠️ | Used in `scripts/test_api.py` — not in `requirements.txt` |

---

*Last updated: 2026-06-17 · Updated by: Copilot Coding Agent*
