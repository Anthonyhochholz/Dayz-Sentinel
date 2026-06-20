# Dayz-Sentinel 🎮

Dayz-Sentinel is a FastAPI-based REST API for importing, storing, and querying DayZ server economy data from `types.xml` and `events.xml`.

## Quick Start

### Docker Compose (recommended)

```bash
cp .env.example .env
docker-compose up -d
```

API base URL: `http://localhost:8000`

### Manual setup

```bash
pip install -r requirements.txt
uvicorn sentinel_spr019.api.main:app --host 0.0.0.0 --port 8000
```

Interactive API docs: `http://localhost:8000/docs`

### CasaOS

Use the existing guide in [`CASAOS_INSTALL.md`](./CASAOS_INSTALL.md).

## Configuration

Copy `.env.example` to `.env` and adjust as needed:

```env
TZ=Europe/Berlin
API_PORT=8000
MIRROR_ROOT=/absolute/path/to/dayz-mirror
```

## API Usage

### Health

```http
GET /api/v1/health
```

Response:

```json
{"status": "ok"}
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

Example write request:

```bash
curl -X POST http://localhost:8000/api/v1/economy/events/ZmbF_Base/toggle-active
```

## Documentation

- [`docs/PROJECT_MEMORY.md`](./docs/PROJECT_MEMORY.md) — current state, operational facts, and open findings
- [`docs/ROADMAP.md`](./docs/ROADMAP.md) — future work only
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — system structure and data flow
- [`docs/CHANGELOG.md`](./docs/CHANGELOG.md) — historical changes only
- [`docs/decisions/README.md`](./docs/decisions/README.md) — ADR index
- [`docs/sprints/README.md`](./docs/sprints/README.md) — sprint history and carry-over context

## Validation

Run tests from the repository root:

```bash
python -m pytest -q tests/
```

### Mirror validation (real DayZ mirror)

Keep your local DayZ mirror outside this repository (for example: `/srv/dayz/mirror`) so mirror files are never committed to git.

Run validation with a configured mirror root:

```bash
MIRROR_ROOT=/srv/dayz/mirror python sentinel_spr019/scripts/validate_mirror.py
```

Or pass a path directly:

```bash
python sentinel_spr019/scripts/validate_mirror.py --mirror-root /srv/dayz/mirror
```

The validation report includes:
- files discovered
- classification counts
- supported files
- unsupported files
