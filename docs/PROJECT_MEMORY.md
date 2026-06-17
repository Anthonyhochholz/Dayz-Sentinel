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
**Active Milestone:** SPR-020 (Integration Testing)  
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
| Tests | 🔶 Partial | Manual `test_api.py` only; no pytest suite |
| `types_importer.py` | ❌ Missing | Referenced but not implemented |

---

## 🗄️ Database

- **File location (in container):** `/app/sentinel_spr019/database/sqlite/sentinel.db`
- **Volume mount:** `./sentinel_spr019/database/sqlite` → `/app/sentinel_spr019/database/sqlite`
- **Schema files:** `database/schema/sentinel_v1_schema.sql`, `sentinel_v1_schema_rev2.sql`

### Populated Tables

| Table | Rows | Source |
|-------|------|--------|
| `economy_items` | 1,917 | `types.xml` |
| `economy_events` | 58 (50 active, 8 inactive) | `events.xml` |

### Defined but Empty Tables (from schema)

`economy_item_flags`, `economy_categories`, `economy_item_categories`, `economy_usages`,
`economy_item_usages`, `economy_values`, `economy_item_values`, `economy_tags`,
`economy_event_flags`, `economy_event_secondary`, `economy_event_children`,
`group_prototypes`, `cluster_instances`, `map_objects`, `territory_files`, `territories`,
`players`, `player_sessions`, `player_positions`, `player_damage_events`, `player_actions`,
`server_sessions`, `import_sources`, `import_runs`, `script_sessions`, `script_engine_events`, etc.

---

## 🔌 API Endpoints (v1)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Health check → `{"status": "ok"}` |
| `GET` | `/api/v1/economy/items` | List items (pagination + search) |
| `GET` | `/api/v1/economy/items/{name}` | Get item by name |
| `GET` | `/api/v1/economy/items/stats/count` | Total item count |
| `GET` | `/api/v1/economy/events` | List events (pagination + search + active_only) |
| `GET` | `/api/v1/economy/events/{name}` | Get event by name |
| `POST` | `/api/v1/economy/events/{name}/toggle-active` | Toggle event active status |
| `GET` | `/api/v1/economy/events/stats/count` | Total event count |

---

## 🐛 Known Issues / Open Audit Items

| ID | Severity | Summary | Status |
|----|----------|---------|--------|
| AUDIT-001 | 🔴 Critical | No auth on `toggle-active` POST endpoint | Open |
| AUDIT-002 | 🔴 Critical | Internal error details leaked in HTTP 500 responses | Open |
| AUDIT-003 | 🟠 High | DB connection leaks (no context manager) | Open |
| AUDIT-004 | 🟠 High | f-String SQL interpolation (Bandit alert) | Open |
| AUDIT-005 | 🟠 High | `.env` / `API_PORT` never read | Open |
| AUDIT-006 | 🟡 Medium | `dict_factory` duplicated in two repositories | Open |
| AUDIT-007 | 🟡 Medium | Dead code (`economy_repository.py`, unused imports) | Open |
| AUDIT-008 | 🟡 Medium | `requests` missing from `requirements.txt` | Open |
| AUDIT-009 | 🟡 Medium | Broken import in `test_import_run.py` | Open |
| AUDIT-010 | 🟡 Medium | `offset` ignored in search endpoints | Open |
| AUDIT-011 | 🟡 Medium | Package name contains sprint number | Open |
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
| `requests` | missing ⚠️ | Used in `test_api.py` |

---

*Last updated: 2026-06-17 · Updated by: Copilot Coding Agent*
