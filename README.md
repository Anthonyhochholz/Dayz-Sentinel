# Dayz-Sentinel 🎮

Dayz-Sentinel ist eine FastAPI-basierte REST-API plus Import-Pipeline für DayZ-Economy- und ADM-Log-Daten (SQLite-Backend).

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

Interaktive API-Dokumentation: `http://localhost:8000/docs`

### CasaOS

Guide: [`CASAOS_INSTALL.md`](./CASAOS_INSTALL.md)

## Konfiguration

```env
TZ=Europe/Berlin
API_PORT=8000
SENTINEL_WRITE_API_KEY=change-me
SENTINEL_DB_PATH=sentinel_spr019/database/sqlite/sentinel.db
```

- `SENTINEL_DB_PATH` ist optional; fehlt die DB-Datei, wird sie automatisch aus den Schema-Dateien gebootstrapped.
- Der Write-Endpunkt (`toggle-active`) ist nur mit korrekt gesetztem `SENTINEL_WRITE_API_KEY` nutzbar.

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

Letzter lokaler Verifizierungsstand: **68 passed**.
