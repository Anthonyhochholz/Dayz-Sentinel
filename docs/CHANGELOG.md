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
