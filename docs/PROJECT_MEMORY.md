# Project Memory — DayZ Sentinel

> Single source of truth for current project state and important operational facts.

## Documentation Ownership

| File | Canonical purpose |
|------|-------------------|
| `README.md` | Installation, quick start, API usage |
| `docs/PROJECT_MEMORY.md` | Current state and important facts |
| `docs/ROADMAP.md` | Future work only |
| `docs/ARCHITECTURE.md` | Architecture only |
| `docs/CHANGELOG.md` | Historical changes only |

## Project Identity

| Field | Value |
|-------|-------|
| Product | DayZ Server Intelligence Platform |
| Repository | `Anthonyhochholz/Dayz-Sentinel` |
| Runtime | Python 3.11 |
| Framework | FastAPI + uvicorn |
| Database | SQLite |
| Current package root | `sentinel_spr019/` |
| Deployment targets | Docker, Docker Compose, CasaOS |

## Long-Term Vision

- DayZ Sentinel is intended to become a DayZ Server Intelligence Platform, not only an economy import API.
- The target platform ingests complete DayZ server mirrors, classifies discovered files, imports multiple data domains, and derives analytics for operators.
- Planned ingestion scope includes economy XML, cluster XML, spawn XML, world XML, ADM logs, RPT logs, and generic log files.

## Current State

- Current documentation cleanup completed on `2026-06-20`.
- The current implementation is still economy-centric and exposes health, economy items, and economy events endpoints.
- `types_importer.py` is implemented with upsert behavior and relational table syncing.
- `events_importer.py` exists, but still performs insert-only imports and skips duplicates on re-run.
- Mirror scanning, multi-type file discovery, analytics, and dashboard capabilities are planned but not yet implemented.
- Sprint records for SPR-020 and SPR-021 are archived with carry-over work moved to the roadmap.

### Component Status

| Component | Status | Notes |
|-----------|--------|-------|
| Core API | ✅ Operational | FastAPI app boots from `sentinel_spr019.api.main:app` |
| Economy items | ✅ Ready | Read endpoints and importer are implemented |
| Economy events | ✅ Ready with caveats | Read endpoints and toggle endpoint exist |
| Mirror ingestion platform | 🚧 Planned | Mirror Scanner, file discovery, and parser orchestration are not implemented yet |
| Analytics engine | 🚧 Planned | No derived server intelligence layer exists yet |
| Tests | ⚠️ Partial | Importer unit tests exist; route/integration coverage is incomplete |
| Docker setup | ✅ Ready with caveats | `docker-compose.yml` maps `${API_PORT:-8000}:8000` |
| Documentation | ✅ Consolidated | Canonical ownership defined in this file |

## Important Operational Facts

- Run tests from the repository root with `python -m pytest -q tests/`.
- Utility scripts live under `sentinel_spr019/scripts/`.
- SQLite data files live under `sentinel_spr019/database/sqlite/`.
- Schema files live under `sentinel_spr019/database/schema/`.
- ADRs live in `docs/decisions/`; sprint history lives in `docs/sprints/` and `sentinel_spr019/docs/`.
- Existing schema already includes placeholders for cluster/world data, player/session data, server/script logs, and import tracking.

## Open Findings

| ID | Severity | Current state |
|----|----------|---------------|
| AUDIT-001 / SEC-001 | Critical | `POST /api/v1/economy/events/{event_name}/toggle-active` has no authentication |
| SEC-002 | Critical | The app does not load `.env`; future secrets and settings are not available to Python code |
| SEC-003 | Critical | `sentinel_spr019/database/sqlite/sentinel.db` is still committed to git |
| SEC-004 | High | `toggle_event_active` still returns `detail=str(e)` for not-found errors |
| SEC-006 | High | Route handlers are `async def` but use synchronous SQLite calls |
| AUDIT-011 | Medium | Package name is still sprint-coupled: `sentinel_spr019` |
| AUDIT-012 | Low | No CORS middleware is configured |
| P3 schema work | Medium | Migration tooling and most non-economy import pipelines are not implemented for the target server intelligence platform |

## Recently Completed Work

- `dict_factory` was centralized in `sentinel_spr019/api/database.py`.
- Dead repository code (`economy_repository.py`) was removed.
- `requests` is present in `requirements.txt`.
- `types_importer.py` and `tests/test_types_importer.py` were delivered in SPR-021.
- Search endpoints now pass `offset` into repository SQL queries.
- README endpoint examples were corrected before this cleanup pass.

## Historical Record Locations

- Use [`docs/CHANGELOG.md`](./CHANGELOG.md) for dated change history.
- Use [`docs/decisions/README.md`](./decisions/README.md) for architecture decisions.
- Use [`docs/sprints/README.md`](./sprints/README.md) for archived sprint summaries.
