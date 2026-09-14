# Changelog — DayZ Sentinel

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- `.github/workflows/ci.yml` — CI mit drei Jobs: pytest auf Python 3.11/3.12/3.13,
  ein Import-Check, der die FastAPI-App nur mit Runtime-Dependencies bootet, und
  ein Docker-Image-Build. (P1-002, OPS-001)
- `requirements-dev.txt` — Test-Dependencies getrennt vom Runtime-Set. `httpx`
  (TestClient) und `requests` (`scripts/test_api.py`) sind Dev-Dependencies und
  landen nicht mehr im Container-Image. (P1-003)
- `sentinel_spr019/persistence/` — neutrale Persistenzschicht, auf die API- und
  Importer-Layer gemeinsam zugreifen, ohne voneinander abzuhängen. Enthält
  `connection.py` (aus `api/database.py`) und die verschobene
  `import_tracking_repository.py`. (P1-001, ARCH-001)
- `persistence.connection.connect()` — setzt `PRAGMA foreign_keys = ON` für jede
  Verbindung.
- `sentinel_spr019/api/models/import_tracking.py` und `api/models/common.py` —
  Response-Modelle für Scans, Scan-Dateien, Runs, Health und Pagination. (P1-004)
- `sentinel_spr019/importer/cli.py` und `__main__.py` — Mirror-Import als
  Entry-Point: `python -m sentinel_spr019.importer <mirror-root>` mit
  `--db-path`, `--json`, `-v` und den Exit-Codes 0 (ok), 1 (Dateien fehlgeschlagen),
  2 (unbrauchbarer Mirror-Root). (P2-003)
- `sentinel_spr019/api/cors.py` — CORS-Allow-List aus `SENTINEL_CORS_ORIGINS`.
  Ohne gesetzte Variable wird keine Middleware installiert; `*` wird beim Start
  abgelehnt. (P3-002, AUDIT-012)
- `create_app()` in `api/main.py` — Konfiguration wird beim App-Bau gelesen.
  Das Modul-Level-`app` bleibt erhalten, `sentinel_spr019.api.main:app`
  funktioniert unverändert.
- `tests/test_persistence_and_layering.py` (11 Tests), `tests/test_api_contracts.py`
  (29 Tests), `tests/test_importer_cli.py` (11 Tests), `tests/test_cors.py` (17 Tests).
- `__init__.py` in `importer/` und `importer/economy/`, die zuvor implizite
  Namespace-Packages waren, während `importer/logs/` ein reguläres Package war.
- `docs/decisions/ADR-0002-shared-persistence-layer.md` — dokumentiert die
  Persistenzschicht und was sie an ADR-002 ablöst.

### Changed
- `requirements.txt` — alle Runtime-Dependencies auf exakte Versionen gepinnt.
- Alle zwölf Endpunkte nutzen typisierte Pydantic-`response_model` statt
  `response_model=dict`. (P1-004)
- `api/models/economy_item.py` und `economy_event.py` gegen das echte Schema
  neu geschrieben: alle numerischen Spalten sind nullable INTEGER/REAL, nicht
  erforderliche Floats. Die ungenutzten `*Base`/`*Response`-Dubletten entfielen.
- `events_importer.py` und `adm_importer.py` öffnen ihre Verbindung über
  `persistence.connection.connect()` und schreiben damit erstmals mit
  erzwungenen Fremdschlüsseln.
- `import_pipeline.py` nutzt `persistence.connection.default_db_path()` statt
  eines eigenen Duplikats.

### Fixed
- **Breaking (Response-Shape):** `economy_events.active` wird als Boolean
  ausgeliefert. Die Read-Endpunkte gaben den rohen INTEGER 0/1 zurück, während
  der Toggle-Endpunkt für denselben Begriff einen echten Boolean lieferte.
- **Breaking (Response-Shape):** Die Listen-Envelopes führen `search` immer mit
  (`null`, wenn nicht gefiltert), statt den Schlüssel weggelassen.
- `PRAGMA foreign_keys` in den Schema-Dateien gilt nur für die Verbindung, die
  das Skript ausgeführt hat. `events_importer.py` und `adm_importer.py`
  schrieben deshalb ohne Referenz-Integritätsprüfung.
- `toggle_active` berechnete `1 - result[0]` und lief bei einem Event mit
  `active IS NULL` in einen `TypeError`, der beim Client als 500 ankam. Ein
  ungesetztes Flag gilt nun als inaktiv.

### Verified
- `python -m pytest -q tests/`: **136 passed** (vorher 68).
- Die 68 bestehenden Tests laufen unverändert auf Python 3.11, 3.12 und 3.13
  gegen das gepinnte Dependency-Set.
- End-to-End-CLI-Lauf: `types.xml` und ein ADM-Log importiert, `.rpt` als
  `unsupported` erfasst.

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
  - Defensive schema migration: renames legacy columns (`item_name → name`, `quantmin → min_value`, `quantmax → max_value`) on first run if found
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

[Unreleased]: https://github.com/Anthonyhochholz/Dayz-Sentinel/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/Anthonyhochholz/Dayz-Sentinel/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Anthonyhochholz/Dayz-Sentinel/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Anthonyhochholz/Dayz-Sentinel/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Anthonyhochholz/Dayz-Sentinel/releases/tag/v0.1.0
