# Changelog — DayZ Sentinel

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Planned
- API-Key authentication for write endpoints (P1-001)
- Generic error responses without internal detail (P1-002)
- SQLite connection context managers (P1-003)
- Parameterized SQL queries replacing f-String interpolation (P1-004)
- `.env`-based `API_PORT` in Docker setup (P1-005)

---

## [0.4.0] — 2026-06-17 · SPR-021 types_importer

### Added
- `sentinel_spr019/importer/economy/types_importer.py` — full implementation
  - Imports `types.xml` into `economy_items` with upsert strategy (update existing, insert new)
  - Populates `economy_item_flags` from `<flags>` attributes
  - Populates `economy_categories` / `economy_item_categories` (M:N)
  - Populates `economy_usages` / `economy_item_usages` (M:N)
  - Populates `economy_values` / `economy_item_values` (M:N)
  - Populates `economy_tags` / `economy_item_tags` (M:N)
  - Full transaction wrapping — any failure rolls back the entire import
  - Defensive schema migration: renames legacy columns (`item_name → name`,
    `quantmin → min_value`, `quantmax → max_value`) on first run if found
- `tests/test_types_importer.py` — 21 pytest unit tests (all passing)
  - Tests: basic insert, upsert strategy, flags, categories, usages, values, tags,
    multiple relations, transaction rollback, schema migration, large import (100 items)
- `docs/decisions/ADR-0001-economy-items-schema.md` — architecture decision record
  documenting the canonical `economy_items` column set

### Fixed
- AUDIT-009: `scripts/test_import_run.py` import path confirmed correct;
  `types_importer.py` now exists and is reachable

### Changed
- `docs/ARCHITECTURE.md` — updated import flow diagram and layer breakdown; removed "NOT IMPLEMENTED" note
- `docs/PROJECT_MEMORY.md` — updated component status table; AUDIT-009 marked resolved
- `docs/ROADMAP.md` — P2-004 and P2-007 marked ✅ complete

---

## [0.3.0] — 2026-06-17 · SPR-019 Complete

### Added
- `economy_events` table populated with 58 events (50 active, 8 inactive) from `events.xml`
- `GET /api/v1/economy/events` — paginated list endpoint with `active_only` and `search` filters
- `GET /api/v1/economy/events/{name}` — single event lookup
- `POST /api/v1/economy/events/{name}/toggle-active` — toggle active status
- `GET /api/v1/economy/events/stats/count` — event count endpoint
- `EconomyEventsRepository` with `get_all()`, `get_by_name()`, `search()`, `get_count()`, `toggle_active()`
- `EconomyEventBase`, `EconomyEvent`, `EconomyEventResponse` Pydantic models
- `sentinel_v1_schema_rev2.sql` — schema delta with import tracking, log event tables
- `events_importer.py` — XML parser for `events.xml` → `economy_events`
- `test_api.py` — integration test runner for all v1 endpoints
- `MILESTONE_001_REPORT.md` — end-to-end completion proof

### Changed
- `api/main.py` updated to register `events_router`

---

## [0.2.0] — 2026-06 · SPR-015 Complete

### Added
- `GET /api/v1/economy/items` — paginated items list with search
- `GET /api/v1/economy/items/{name}` — single item lookup
- `GET /api/v1/economy/items/stats/count` — item count endpoint
- `EconomyItemsRepository` with `get_all()`, `get_by_name()`, `search()`, `get_count()`
- `EconomyItemBase`, `EconomyItem`, `EconomyItemResponse` Pydantic models
- `GET /api/v1/health` health check endpoint

---

## [0.1.0] — 2026-06 · SPR-010 Initial Import

### Added
- Project scaffold: FastAPI + uvicorn + SQLite
- `sentinel_v1_schema.sql` — full initial schema (economy, world, player, server tables)
- `economy_items` table populated with 1,917 items from `types.xml`
- `Dockerfile` and `docker-compose.yml` for containerized deployment
- `.env.example` with `TZ` and `API_PORT` variables
- `EconomyRepository` (basic prototype, later superseded)

---

[Unreleased]: https://github.com/Anthonyhochholz/Dayz-Sentinel/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/Anthonyhochholz/Dayz-Sentinel/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Anthonyhochholz/Dayz-Sentinel/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Anthonyhochholz/Dayz-Sentinel/releases/tag/v0.1.0
