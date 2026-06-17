# Roadmap — DayZ Sentinel

> Prioritized list of planned improvements and features.
> Updated after each sprint review.

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Complete |
| 🔄 | In Progress |
| 📋 | Planned |
| ❌ | Blocked |
| 💡 | Idea / Under Discussion |

---

## 🔴 P1 — Critical / Security (Do First)

These items address security vulnerabilities or production-blocking bugs identified in the audit.

| ID | Task | Audit Ref | Sprint |
|----|------|-----------|--------|
| P1-001 | Add API-Key authentication for all write (POST/PUT/DELETE) endpoints | AUDIT-001 | SPR-020 |
| P1-002 | Replace `detail=str(e)` with generic 500 messages; log full error server-side | AUDIT-002 | SPR-020 |
| P1-003 | Wrap all `sqlite3.connect()` calls in context managers to prevent connection leaks | AUDIT-003 | SPR-020 |
| P1-004 | Replace f-String SQL interpolation with parameterized queries in `economy_events_repository.py` (lines 30, 36–44, 107–114, 130) | AUDIT-004 | SPR-020 |
| P1-005 | Read `API_PORT` from `.env` in `docker-compose.yml` and `Dockerfile` | AUDIT-005 | SPR-020 |

---

## 🟠 P2 — High / Code Quality (Do Soon)

These items improve maintainability, correctness, and developer experience.

| ID | Task | Audit Ref | Sprint |
|----|------|-----------|--------|
| P2-001 | Centralize `dict_factory` in `database.py`; remove duplicates from `economy_items_repository.py:128` and `economy_events_repository.py:177` | AUDIT-006 | SPR-021 |
| P2-002 | Delete `economy_repository.py` (dead code at `api/repositories/economy_repository.py`); remove unused model imports | AUDIT-007 | SPR-021 |
| P2-003 | Add `requests` to `requirements.txt` | AUDIT-008 | SPR-021 |
| P2-004 | ✅ Fix broken import in `scripts/test_import_run.py` and implement `types_importer.py` to import `types.xml` economy items | AUDIT-009 | SPR-021 |
| P2-005 | Add `offset` parameter to `search()` methods in both repositories (currently ignored despite being accepted by routes) | AUDIT-010 | SPR-021 |
| P2-006 | Rename package from `sentinel_spr019` to `sentinel` | AUDIT-011 | SPR-022 |
| P2-007 | ✅ Add `pytest` test suite with in-memory SQLite fixtures (`tests/test_types_importer.py`, 21 tests) | — | SPR-021 |
| P2-008 | Pin dependency versions in `requirements.txt` | — | SPR-021 |

---

## 🟡 P3 — Medium / Features (Plan Ahead)

These items expand functionality and set up future scale.

| ID | Task | Notes | Sprint |
|----|------|-------|--------|
| P3-001 | Add CORS middleware with configurable allowed origins | AUDIT-012 | SPR-023 |
| P3-002 | Fix README endpoint documentation (wrong paths, non-existent `?type=` param) | AUDIT-013 | SPR-020 |
| P3-003 | Implement player log import pipeline (`players`, `player_sessions`, `player_positions`) | Schema exists | SPR-023 |
| P3-004 | Implement server session log import (`server_sessions`, `script_sessions`) | Schema exists | SPR-023 |
| P3-005 | Implement damage event import and analytics endpoint | Schema exists | SPR-024 |
| P3-006 | Add schema migration tooling (Alembic or custom runner) and fix `sentinel_v1_schema.sql` to match deployed DB column names (`item_name` → `name`, etc.) | Schema/live DB mismatch | SPR-022 |
| P3-007 | Add Swagger/OpenAPI response schemas (replace `response_model=dict`) | — | SPR-023 |
| P3-008 | Rate limiting via `slowapi` | — | SPR-024 |
| P3-009 | Repository methods return typed Pydantic models instead of plain `dict` | — | SPR-023 |

---

## 💡 Future / Under Discussion

| Idea | Description |
|------|-------------|
| Web UI | Minimal admin dashboard for event management |
| PostgreSQL option | Optional PG backend for high-traffic deployments |
| Real-time log streaming | WebSocket endpoint for live server log monitoring |
| Discord bot integration | Push notifications on player events |
| Map visualization | 2D heat-map of player positions |

---

## ✅ Completed

| ID | Task | Sprint |
|----|------|--------|
| — | `types_importer.py` implemented (upsert, transactions, flags + relations) | SPR-021 |
| — | `tests/test_types_importer.py` — 21 pytest unit tests (in-memory SQLite) | SPR-021 |
| — | `docs/decisions/ADR-0001-economy-items-schema.md` — schema decision documented | SPR-021 |
| — | AUDIT-009 resolved | SPR-021 |
| — | Initial FastAPI scaffold | SPR-010 |
| — | Economy items import from `types.xml` | SPR-010 |
| — | Items API endpoints (GET list, GET by name, count) | SPR-015 |
| — | Economy events import from `events.xml` | SPR-016 – SPR-018 |
| — | Events API endpoints (GET list, GET by name, toggle, count) | SPR-019 |
| — | Docker + Docker Compose setup | SPR-019 |
| — | Comprehensive HTTP integration test suite (`scripts/test_api.py`) | SPR-020 |

---

*Last updated: 2026-06-17 · SPR-021*
