# Project Memory — DayZ Sentinel

> Einzige Informationsquelle für den aktuellen Projektzustand.

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
| Repository | `Anthonyhochholz/DayZ-Sentinel` |
| Runtime | Python 3.11+ |
| Framework | FastAPI + uvicorn |
| Database | SQLite |
| Package root | `sentinel_spr019/` |
| Deployment targets | Docker, Docker Compose, CasaOS |

## Current State

- API-Endpunkte für Health, Economy-Items, Economy-Events und Import-Tracking sind implementiert.
- Der Write-Endpunkt `POST /api/v1/economy/events/{event_name}/toggle-active` ist per `X-API-Key` abgesichert.
- Die Mirror-Pipeline (`run_mirror_import`) ist implementiert und verarbeitet aktuell `types.xml`, `events.xml` und `*.adm`.
- Import-Tracking (`mirror_scans`, `mirror_scan_files`, `import_runs`, `import_sources`) wird aktiv befüllt und über API readbar gemacht.
- `events_importer.py` und `types_importer.py` arbeiten mit Upsert-/Idempotenz-Logik im Pipeline-Kontext.
- ADM-Import (`importer/logs/adm_importer.py`) parst Connect/Disconnect/Kill/Death/Admin-Events und schreibt in Spieler-/Session-/Event-Tabellen.

### Component Status

| Component | Status | Notes |
|-----------|--------|-------|
| Core API | ✅ Operational | FastAPI app aus `sentinel_spr019.api.main:app` |
| Economy items | ✅ Operational | Read-Endpunkte + Importer vorhanden |
| Economy events | ✅ Operational | Read-Endpunkte + Toggle-Write-Endpunkt |
| Import tracking API | ✅ Operational | `/api/v1/import-tracking/*` verfügbar |
| Mirror scanning + pipeline | ✅ Operational | Datei-Scan, Klassifikation, Dispatch implementiert |
| ADM importer | ✅ Operational | Parser + DB-Persistenz implementiert |
| RPT importer | 🚧 Planned | Klassifikation vorhanden, Import nicht implementiert |
| Cluster/world importers | 🚧 Planned | Schema vorbereitet, Importer fehlen |
| Analytics layer | 🚧 Planned | Noch keine abgeleiteten Read-Modelle |
| Tests | ✅ Strong unit/integration | Lokaler Stand: `68 passed` |

## Important Operational Facts

- Tests vom Repo-Root: `python -m pytest -q tests/`.
- Utility-Skripte liegen unter `sentinel_spr019/scripts/`.
- SQLite-Datei liegt standardmäßig unter `sentinel_spr019/database/sqlite/sentinel.db`.
- Schema-Dateien liegen in `sentinel_spr019/database/schema/`.
- API lädt `.env` beim Start; DB wird bei fehlender Datei automatisch gebootstrapped.

## Open Findings

| ID | Severity | Current state |
|----|----------|---------------|
| AUDIT-011 | Medium | Package name ist weiterhin sprint-gekoppelt (`sentinel_spr019`) |
| AUDIT-012 | Low | Kein CORS-Middleware-Setup vorhanden |
| ARCH-001 | Medium | `import_pipeline.py` nutzt `api.repositories.ImportTrackingRepository` (Cross-Layer-Abhängigkeit) |
| INGEST-001 | Medium | Kein RPT-Importer implementiert |
| INGEST-002 | Medium | Cluster-/World-Importer fehlen weiterhin |
| OPS-001 | Low | Keine CI-Workflow-Dateien für automatisierte Tests im Repository |

## Historical Record Locations

- Change-Historie: [`docs/CHANGELOG.md`](./CHANGELOG.md)
- Architekturentscheidungen: [`docs/decisions/README.md`](./decisions/README.md)
- Sprint-Historie: [`docs/sprints/README.md`](./sprints/README.md)
