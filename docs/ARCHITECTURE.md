# Architecture — DayZ Sentinel

## System Overview

DayZ Sentinel läuft aktuell als einzelner FastAPI-Service mit SQLite und kombiniert API-Zugriff mit dateibasierter Import-Pipeline.

```text
Mirror directory -> scan_mirror -> classify_file -> run_mirror_import
                                           -> types/events/adm importers
                                           -> persistence -> SQLite
Client -> FastAPI routes -> repositories -> persistence -> SQLite
```

Der Importer- und der API-Layer teilen sich die neutrale Persistenzschicht
(`sentinel_spr019/persistence/`) und kennen einander nicht.

## Runtime Topology

```text
┌─────────────────────────────────────────────────────────────┐
│ Docker container / local Python process                    │
│                                                             │
│  uvicorn                                                    │
│   -> FastAPI app (`sentinel_spr019/api/main.py`)           │
│      -> /api/v1/health                                     │
│      -> /api/v1/economy/items*                             │
│      -> /api/v1/economy/events*                            │
│      -> /api/v1/import-tracking/*                          │
│                                                             │
│  Importer (`python -m sentinel_spr019.importer`)           │
│   -> cli.py                                                │
│   -> mirror_scanner.py                                     │
│   -> file_classifier.py                                    │
│   -> import_pipeline.py                                    │
│   -> economy/types_importer.py                             │
│   -> economy/events_importer.py                            │
│   -> logs/adm_importer.py                                  │
│                                                             │
│  Shared persistence (`persistence/`)                        │
│   -> connection.py (bootstrap + PRAGMA foreign_keys)        │
│   -> import_tracking_repository.py                          │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
          `sentinel_spr019/database/sqlite/sentinel.db`
```

## Application Layers

| Layer | Primary paths | Responsibility |
|------|---------------|----------------|
| Entrypoint | `sentinel_spr019/api/main.py` | `create_app()` plus ASGI-Objekt `app` |
| Routes | `sentinel_spr019/api/routes/` | HTTP-Validierung, Response-Shaping |
| Response models | `sentinel_spr019/api/models/` | Typisierte API-Verträge (OpenAPI) |
| Repositories | `sentinel_spr019/api/repositories/` | Economy-Lese-/Schreibzugriffe |
| Security | `sentinel_spr019/api/security.py` | API-Key-Schutz für Write-Endpunkt |
| CORS | `sentinel_spr019/api/cors.py` | Origin-Allow-List aus `SENTINEL_CORS_ORIGINS` |
| Import CLI | `sentinel_spr019/importer/cli.py` | Operativer Entry-Point für Mirror-Importe |
| Import orchestration | `sentinel_spr019/importer/import_pipeline.py` | Scan-Tracking, Klassifikation, Dispatch |
| Importers | `sentinel_spr019/importer/economy/`, `sentinel_spr019/importer/logs/` | Parser + Persistenz |
| Persistence | `sentinel_spr019/persistence/` | Verbindungsaufbau, Bootstrap, Import-Tracking |
| Schema | `sentinel_spr019/database/schema/` | DDL v1 + rev2 |
| Tests | `tests/` | Unit-, Integrations- und Contract-Tests |

## Core Data Flows

### API read flow

1. Client ruft GET-Endpunkt auf.
2. Route validiert Parameter.
3. Route delegiert via `run_in_threadpool` an synchrones Repository.
4. Repository öffnet SQLite über `persistence.connection.get_connection()`.
5. Ergebnis wird gegen das `response_model` der Route validiert und als JSON zurückgegeben.

### API write flow (`toggle-active`)

1. Client ruft `POST /api/v1/economy/events/{event_name}/toggle-active` auf.
2. `require_write_api_key` validiert `X-API-Key` gegen `SENTINEL_WRITE_API_KEY`.
3. Repository toggelt `active` und committed.
4. API liefert den neuen Status.

### Mirror import flow

0. Einstieg entweder über die CLI (`python -m sentinel_spr019.importer <mirror-root>`)
   oder direkt über `run_mirror_import`.
1. `run_mirror_import(mirror_root, db_file)` scannt rekursiv alle Dateien.
2. Jede Datei wird klassifiziert (`types.xml`, `events.xml`, `*.adm`, unsupported).
3. Für jede Datei werden Scan- und Run-Metadaten in Import-Tracking-Tabellen geschrieben.
4. Unterstützte Dateien werden an passenden Importer dispatcht.
5. Idempotenz erfolgt über `importer_version` mit Datei-Hash.
6. Scan-Abschlussstatus wird als `completed` oder `completed_with_errors` persistiert.

## Supported File Categories (current)

| File type | Status | Import target |
|-----------|--------|---------------|
| `types.xml` | ✅ Implemented | Economy-Items + Relationen |
| `events.xml` | ✅ Implemented | Economy-Events |
| `*.adm` | ✅ Implemented | Player-/Session-/Action-/Damage-Tabellen |
| `*.rpt` | 🚧 Planned | Noch kein Importer |
| Other XML / unknown files | ⚠️ Tracked as unsupported | Nur Klassifikation/Tracking |

## Architectural Constraints and Gaps

| Area | Current fact |
|------|--------------|
| Storage model | SQLite ist aktuell der einzige Backend-Store |
| Package naming | `sentinel_spr019` bleibt sprint-gekoppelt |
| Layering | Aufgelöst: gemeinsame `persistence`-Schicht, durch Tests abgesichert |
| API models | Alle Endpunkte sind an Pydantic-`response_model` gebunden |
| CORS | Konfigurierbar über `SENTINEL_CORS_ORIGINS`, standardmäßig aus |
| CI automation | `.github/workflows/ci.yml` (pytest 3.11/3.12/3.13, Import-Check, Docker-Build) |
| Connection handling | Pro Anfrage eine neue SQLite-Verbindung, kein Pooling und kein WAL |
| Platform scope | Cluster-/World-/RPT-Importer und Analytics-Layer fehlen |
