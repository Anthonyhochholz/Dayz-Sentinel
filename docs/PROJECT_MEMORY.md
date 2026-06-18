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
**Active Milestone:** SPR-021 (types_importer + Tests)
**Last Completed:** SPR-020 (Integration Testing & Security Fixes)

### Component Status

| Component | Status | Notes |
|-----------|--------|-------|
| Core API | ✅ Operational | FastAPI v1 endpoints live |
| Economy Items | ✅ Ready | 1,917 items imported from `types.xml` |
| Economy Events | ✅ Ready | 58 events imported from `events.xml` |
| Database Schema | ✅ Ready | SQLite `sentinel_v1_schema.sql` + `rev2` deployed |
| Docker | ✅ Ready | `Dockerfile` + `docker-compose.yml` present; `API_PORT` reads from `.env` |
| Authentication | ❌ Missing | No auth on write endpoints (AUDIT-001) |
| Tests | ✅ Added | `tests/test_types_importer.py` — 21 pytest unit tests; no running API needed |
| `types_importer.py` | ✅ Implemented | `importer/economy/types_importer.py` — upsert strategy, full transaction, flags + relations |
| `economy_repository.py` | ✅ Removed | Dead code removed (was at `api/repositories/economy_repository.py`) |

---

## 🗄️ Database

- **File location (in container):** `/app/sentinel_spr019/database/sqlite/sentinel.db`
- **Volume mount:** `./sentinel_spr019/database/sqlite` → `/app/sentinel_spr019/database/sqlite`
- **Schema files:** `sentinel_spr019/database/schema/sentinel_v1_schema.sql`, `sentinel_v1_schema_rev2.sql`

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
| AUDIT-002 | 🔴 Critical | Internal error details leaked in HTTP 500 responses (`detail=str(e)` in all route handlers) | ✅ Resolved — generic messages + server-side logging |
| AUDIT-003 | 🟠 High | DB connection leaks — repositories now use `try/finally` blocks | ✅ Resolved |
| AUDIT-004 | 🟠 High | f-String SQL interpolation in `economy_events_repository.py` — replaced with safe conditional queries | ✅ Resolved |
| AUDIT-005 | 🟠 High | `API_PORT` now read from `.env` via `${API_PORT:-8000}` in `docker-compose.yml` | ✅ Resolved |
| AUDIT-006 | 🟡 Medium | `dict_factory` centralized in `database.py`; removed from repository files | ✅ Resolved |
| AUDIT-007 | 🟡 Medium | `economy_repository.py` deleted (dead code) | ✅ Resolved |
| AUDIT-008 | 🟡 Medium | `requests` added to `requirements.txt` | ✅ Resolved |
| AUDIT-009 | 🟢 Resolved | `scripts/test_import_run.py` import path correct; `types_importer.py` implemented | ✅ Resolved |
| AUDIT-010 | 🟡 Medium | `offset` now passed to `search()` in both repositories | ✅ Resolved |
| AUDIT-011 | 🔵 Low | Package name contains sprint number (`sentinel_spr019`) — not a stable package name | Open |
| AUDIT-012 | 🔵 Low | No CORS middleware | Open |
| AUDIT-013 | 🔵 Low | README endpoint docs fixed (correct health path, removed phantom `?type=` param) | ✅ Resolved |

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
| `requests` | unpinned | HTTP client — used in `scripts/test_api.py` |

---

*Last updated: 2026-06-17 · Updated by: Copilot Coding Agent · SPR-021*
