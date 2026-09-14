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
| `.github/workflows/ci.yml` | Automated test, import and image-build checks |

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

- API-Endpunkte für Health, Economy-Items, Economy-Events und Import-Tracking sind implementiert
  und alle an typisierte Pydantic-`response_model`-Verträge gebunden.
- Der Write-Endpunkt `POST /api/v1/economy/events/{event_name}/toggle-active` ist per `X-API-Key` abgesichert.
- Die Mirror-Pipeline (`run_mirror_import`) ist implementiert und verarbeitet aktuell `types.xml`, `events.xml` und `*.adm`.
- Import-Tracking (`mirror_scans`, `mirror_scan_files`, `import_runs`, `import_sources`) wird aktiv befüllt und über API readbar gemacht.
- `events_importer.py` und `types_importer.py` arbeiten mit Upsert-/Idempotenz-Logik im Pipeline-Kontext.
- ADM-Import (`importer/logs/adm_importer.py`) parst Connect/Disconnect/Kill/Death/Admin-Events und schreibt in Spieler-/Session-/Event-Tabellen.
- Der Mirror-Import ist als CLI nutzbar: `python -m sentinel_spr019.importer <mirror-root>`.
- `sentinel_spr019/persistence/` ist die gemeinsame Persistenzschicht von API- und Importer-Layer;
  jede Verbindung wird über `connect()` geöffnet und erzwingt `PRAGMA foreign_keys = ON`.
- CORS ist über `SENTINEL_CORS_ORIGINS` konfigurierbar und standardmäßig deaktiviert.
- CI läuft über GitHub Actions: pytest auf Python 3.11/3.12/3.13, ein Import-Check mit
  ausschließlich Runtime-Dependencies und ein Docker-Image-Build.

### Component Status

| Component | Status | Notes |
|-----------|--------|-------|
| Core API | ✅ Operational | FastAPI app aus `sentinel_spr019.api.main:app` |
| Economy items | ✅ Operational | Read-Endpunkte + Importer vorhanden |
| Economy events | ✅ Operational | Read-Endpunkte + Toggle-Write-Endpunkt |
| Import tracking API | ✅ Operational | `/api/v1/import-tracking/*` verfügbar |
| Mirror scanning + pipeline | ✅ Operational | Datei-Scan, Klassifikation, Dispatch implementiert |
| ADM importer | ✅ Operational | Parser + DB-Persistenz implementiert |
| Import CLI | ✅ Operational | `python -m sentinel_spr019.importer`, Exit-Codes 0/1/2 |
| CORS | ✅ Configurable | Allow-List via `SENTINEL_CORS_ORIGINS`, Default aus |
| CI pipeline | ✅ Operational | `.github/workflows/ci.yml` |
| RPT importer | 🚧 Planned | Klassifikation vorhanden, Import nicht implementiert |
| Cluster/world importers | 🚧 Planned | Schema vorbereitet, Importer fehlen |
| Analytics layer | 🚧 Planned | Noch keine abgeleiteten Read-Modelle |
| Tests | ✅ Strong unit/integration/contract | Lokaler Stand: `136 passed` |

## Important Operational Facts

- Tests vom Repo-Root: `python -m pytest -q tests/`.
- Test-Dependencies: `pip install -r requirements-dev.txt` (Runtime-Set steht in `requirements.txt`).
- Mirror-Import operativ: `python -m sentinel_spr019.importer <mirror-root> [--db-path ...] [--json]`.
- Utility-Skripte liegen unter `sentinel_spr019/scripts/`.
- SQLite-Datei liegt standardmäßig unter `sentinel_spr019/database/sqlite/sentinel.db`.
- Schema-Dateien liegen in `sentinel_spr019/database/schema/`.
- API lädt `.env` beim Start; DB wird bei fehlender Datei automatisch gebootstrapped.

## Open Findings

| ID | Severity | Current state |
|----|----------|---------------|
| AUDIT-011 | Medium | Package name ist weiterhin sprint-gekoppelt (`sentinel_spr019`) |
| INGEST-001 | Medium | Kein RPT-Importer implementiert |
| INGEST-002 | Medium | Cluster-/World-Importer fehlen weiterhin |
| PERF-001 | Low | Pro Request wird eine neue SQLite-Verbindung geöffnet; kein Pooling, kein WAL |
| DOCS-001 | Low | `sentinel_spr019/docs/` enthält Sprint-Altdokumente parallel zu `docs/` |
| TEST-001 | Low | `sentinel_spr019/scripts/test_*.py` sind manuelle Runner, keine pytest-Tests; die Namensgleichheit ist irreführend |

### Resolved since the last revision

| ID | Resolution |
|----|------------|
| AUDIT-012 | CORS über `SENTINEL_CORS_ORIGINS` konfigurierbar (`api/cors.py`) |
| ARCH-001 | Importer hängt nicht mehr an `api.repositories`; gemeinsame `persistence`-Schicht, per Layering-Test abgesichert |
| OPS-001 | `.github/workflows/ci.yml` eingeführt |

## Historical Record Locations

- Change-Historie: [`docs/CHANGELOG.md`](./CHANGELOG.md)
- Architekturentscheidungen: [`docs/decisions/README.md`](./decisions/README.md)
- Sprint-Historie: [`docs/sprints/README.md`](./sprints/README.md)
