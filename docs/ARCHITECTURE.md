# Architecture — DayZ Sentinel

## System Overview

DayZ Sentinel läuft aktuell als einzelner FastAPI-Service mit SQLite und kombiniert API-Zugriff mit dateibasierter Import-Pipeline.

```text
Mirror directory -> scan_mirror -> classify_file -> run_mirror_import
                                           -> types/events/adm importers
                                           -> SQLite
Client -> FastAPI routes -> repositories -> SQLite
```

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
│  Importer                                                   │
│   -> mirror_scanner.py                                     │
│   -> file_classifier.py                                    │
│   -> import_pipeline.py                                    │
│   -> economy/types_importer.py                             │
│   -> economy/events_importer.py                            │
│   -> logs/adm_importer.py                                  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
          `sentinel_spr019/database/sqlite/sentinel.db`
```

## Application Layers

| Layer | Primary paths | Responsibility |
|------|---------------|----------------|
| Entrypoint | `sentinel_spr019/api/main.py` | App-Erstellung und Router-Registrierung |
| Routes | `sentinel_spr019/api/routes/` | HTTP-Validierung, Response-Shaping |
| Repositories | `sentinel_spr019/api/repositories/` | SQLite-Lese-/Schreibzugriffe |
| Security | `sentinel_spr019/api/security.py` | API-Key-Schutz für Write-Endpunkt |
| Import orchestration | `sentinel_spr019/importer/import_pipeline.py` | Scan-Tracking, Klassifikation, Dispatch |
| Importers | `sentinel_spr019/importer/economy/`, `sentinel_spr019/importer/logs/` | Parser + Persistenz |
| Schema | `sentinel_spr019/database/schema/` | DDL v1 + rev2 |
| Tests | `tests/` | Unit- und Integrations-Tests |

## Core Data Flows

### API read flow

1. Client ruft GET-Endpunkt auf.
2. Route validiert Parameter.
3. Route delegiert via `run_in_threadpool` an synchrones Repository.
4. Repository öffnet SQLite über `get_connection()`.
5. Ergebnis wird als JSON zurückgegeben.

### API write flow (`toggle-active`)

1. Client ruft `POST /api/v1/economy/events/{event_name}/toggle-active` auf.
2. `require_write_api_key` validiert `X-API-Key` gegen `SENTINEL_WRITE_API_KEY`.
3. Repository toggelt `active` und committed.
4. API liefert den neuen Status.

### Mirror import flow

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
| Layering | Importer-Layer hängt von `api.repositories` ab (`ImportTrackingRepository`) |
| API models | Routes nutzen weiterhin überwiegend `response_model=dict` |
| CORS | Nicht konfiguriert |
| CI automation | Keine Workflow-Dateien im Repository |
| Platform scope | Cluster-/World-/RPT-Importer und Analytics-Layer fehlen |
