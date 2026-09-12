# DayZ-Sentinel 🎮

DayZ-Sentinel ist eine FastAPI-basierte REST-API plus Import-Pipeline für DayZ-Economy- und ADM-Log-Daten (SQLite-Backend).

## Quick Start

### Docker Compose (empfohlen)

```bash
cp .env.example .env
docker-compose up -d
```

API base URL: `http://localhost:8000`

### Manuelles Setup

```bash
pip install -r requirements.txt
uvicorn sentinel_spr019.api.main:app --host 0.0.0.0 --port 8000
```

Für Tests und Entwicklung zusätzlich:

```bash
pip install -r requirements-dev.txt
```

Interaktive API-Dokumentation: `http://localhost:8000/docs`

### CasaOS

Guide: [`CASAOS_INSTALL.md`](./CASAOS_INSTALL.md)

## Konfiguration

```env
TZ=Europe/Berlin
API_PORT=8000
SENTINEL_WRITE_API_KEY=change-me
SENTINEL_DB_PATH=sentinel_spr019/database/sqlite/sentinel.db
# SENTINEL_CORS_ORIGINS=http://localhost:5173,https://dashboard.example.com
```

- `SENTINEL_DB_PATH` ist optional; fehlt die DB-Datei, wird sie automatisch aus den Schema-Dateien gebootstrapped.
- Der Write-Endpunkt (`toggle-active`) ist nur mit korrekt gesetztem `SENTINEL_WRITE_API_KEY` nutzbar.
- `SENTINEL_CORS_ORIGINS` ist eine kommaseparierte Liste erlaubter Browser-Origins.
  Ohne die Variable wird keine CORS-Middleware installiert; ein `*` wird beim Start
  mit einem Fehler abgelehnt.

## API Usage

### Health

```http
GET /api/v1/health
```

### Economy items

```http
GET /api/v1/economy/items?limit=50&offset=0
GET /api/v1/economy/items?search=rifle&limit=20
GET /api/v1/economy/items/{item_name}
GET /api/v1/economy/items/stats/count
```

### Economy events

```http
GET /api/v1/economy/events?limit=100&offset=0
GET /api/v1/economy/events?search=zmb&active_only=true
GET /api/v1/economy/events/{event_name}
GET /api/v1/economy/events/stats/count?active_only=true
POST /api/v1/economy/events/{event_name}/toggle-active
```

Beispiel-Write-Request:

```bash
curl -X POST \
  -H "X-API-Key: change-me" \
  http://localhost:8000/api/v1/economy/events/ZmbF_Base/toggle-active
```

### Import tracking

```http
GET /api/v1/import-tracking/scans
GET /api/v1/import-tracking/scans/{scan_id}
GET /api/v1/import-tracking/scans/{scan_id}/files
GET /api/v1/import-tracking/runs
```

## Mirror-Import-Pipeline

Die Mirror-Pipeline (`sentinel_spr019/importer/import_pipeline.py`) scannt ein Mirror-Verzeichnis rekursiv, klassifiziert Dateien und importiert aktuell:

- `types.xml` → Economy-Items
- `events.xml` → Economy-Events
- `*.adm` → ADM-Log-Events

Nicht unterstützte Typen (z. B. `*.rpt`, sonstige XML-Dateien) werden als `unsupported` im Import-Tracking erfasst.

### Import ausführen

```bash
python -m sentinel_spr019.importer /pfad/zum/mirror
```

```text
Mirror import completed (scan #1)
  database: sentinel_spr019/database/sqlite/sentinel.db
  discovered:          3
  imported:            2
  skipped (unchanged): 0
  unsupported:         1
  failed:              0
```

Optionen:

| Flag | Wirkung |
|------|---------|
| `--db-path PATH` | Ziel-Datenbank. Default: `$SENTINEL_DB_PATH`, sonst der Paket-Pfad |
| `--json` | Zusammenfassung als JSON statt als Text |
| `-v`, `--verbose` | Debug-Logging |

Exit-Codes: `0` erfolgreich, `1` Scan abgeschlossen, aber einzelne Dateien
fehlgeschlagen, `2` Mirror-Root existiert nicht oder ist kein Verzeichnis.

Wiederholte Läufe überspringen unveränderte Dateien: die Idempotenz hängt am
SHA-256-Hash der Datei, der als `importer_version` im Import-Tracking landet.

## Dokumentation

- [`docs/PROJECT_MEMORY.md`](./docs/PROJECT_MEMORY.md) — aktueller Systemzustand und operative Fakten
- [`docs/ROADMAP.md`](./docs/ROADMAP.md) — offene und geplante Arbeiten
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — Architektur und Datenflüsse
- [`docs/CHANGELOG.md`](./docs/CHANGELOG.md) — Historie
- [`docs/decisions/README.md`](./docs/decisions/README.md) — ADR-Index
- [`docs/sprints/README.md`](./docs/sprints/README.md) — Sprint-Historie

## Validation

Tests vom Repo-Root ausführen:

```bash
python -m pytest -q tests/
```

Letzter lokaler Verifizierungsstand: **136 passed** (Python 3.11; die Suite läuft
ebenso auf 3.12 und 3.13).

CI führt bei jedem Push und Pull Request denselben Lauf aus, zusätzlich einen
Import-Check der App mit ausschließlich Runtime-Dependencies und einen
Docker-Image-Build: [`.github/workflows/ci.yml`](./.github/workflows/ci.yml).
