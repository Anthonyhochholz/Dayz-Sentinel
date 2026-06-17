# Dayz-Sentinel 🎮

**A comprehensive server administration and analytics tool for DayZ Standalone**

Dayz-Sentinel is a FastAPI-based REST API designed to manage, monitor, and analyze DayZ server data. It imports and persists server configuration data (economy items, events, logs) into a SQLite database and provides RESTful endpoints for querying server state.

---

## ✨ Features

- 📦 **Economy Management** — Import and query 1,900+ item types from DayZ economy
- 📅 **Event Tracking** — Monitor 50+ server events with active/inactive status
- 🔍 **REST API** — Full-featured v1 API with filtering and pagination
- 🐳 **Docker Ready** — Pre-configured Docker & Docker Compose for easy deployment
- 💾 **SQLite Backend** — Persistent data storage with schema migrations
- 🚀 **FastAPI** — Modern async Python framework for high performance

---

## 📋 Status

| Component | Status | Notes |
|-----------|--------|-------|
| Core API | ✅ Operational | FastAPI v1 endpoints live |
| Economy Items | ✅ Ready | 1,917 items imported from types.xml |
| Economy Events | ✅ Ready | 58 events imported from events.xml |
| Database | ✅ Ready | SQLite schema v1 deployed |
| Docker | ✅ Ready | Production-grade Dockerfile included |

**Current Milestone:** SPR-019 ✅ Complete  
**Next Milestone:** SPR-020 (Integration testing)

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone and navigate to repo
git clone https://github.com/Anthonyhochholz/Dayz-Sentinel.git
cd Dayz-Sentinel

# Copy environment file
cp .env.example .env

# Start the service
docker-compose up -d

# API will be available at http://localhost:8000
```

### Option 2: Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API
uvicorn sentinel_spr019.api.main:app --host 0.0.0.0 --port 8000

# Navigate to http://localhost:8000/docs for interactive API docs
```

### Option 3: CasaOS

Follow the setup guide in [CASAOS_INSTALL.md](./CASAOS_INSTALL.md)

---

## 📡 API Endpoints

### Health Check
```bash
GET /health
# Response: {"status": "operational"}
```

### Economy Items
```bash
# Get all items with pagination
GET /api/v1/economy/items?limit=50&offset=0

# Get specific item
GET /api/v1/economy/items/{item_name}

# Filter by type
GET /api/v1/economy/items?type=weapon&limit=20
```

### Economy Events
```bash
# Get all events
GET /api/v1/economy/events?limit=100&active_only=false

# Get specific event
GET /api/v1/economy/events/{event_name}

# Get only active events
GET /api/v1/economy/events?active_only=true
```

---

## 🏗️ Project Structure

```
dayz-sentinel/
├── sentinel_spr019/
│   ├── api/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── database.py          # Database connection
│   │   ├── models/              # Pydantic data models
│   │   ├── repositories/        # Database access layer
│   │   └── routes/              # API endpoint handlers
│   ├── database/
│   │   ├── schema/              # SQL schema definitions
│   │   └── sqlite/              # SQLite database files (volume-mounted)
│   ├── importer/
│   │   └── economy/             # Import scripts for economy data
│   ├── scripts/                 # Utility scripts
│   └── docs/                    # Sprint reports & documentation
├── Dockerfile                   # Container image definition
├── docker-compose.yml           # Multi-container orchestration
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
└── README.md                    # This file
```

---

## 🔧 Configuration

Edit `.env` to customize:

```env
TZ=Europe/Berlin              # Timezone
API_PORT=8000                 # API port
```

---

## 📊 Data Import

### Economy Items (types.xml)
- **Source:** DayZ mission configuration
- **Rows:** 1,917 items
- **Fields:** name, nominal, min_value, max_value, restock, lifetime, etc.

### Economy Events (events.xml)
- **Source:** DayZ mission configuration
- **Rows:** 58 events (50 active, 8 inactive)
- **Fields:** event_name, nominal, min_count, max_count, lifetime, restock, radius fields, modes, active status

---

## 📖 Documentation

- **[MILESTONE_001_REPORT](./sentinel_spr019/docs/MILESTONE_001_REPORT.md)** — End-to-end completion proof
- **[SPR-019: Economy Events Persist](./sentinel_spr019/docs/spr019_economy_events_persist.md)** — Latest implementation details
- **[CASAOS_INSTALL](./CASAOS_INSTALL.md)** — Deploy on CasaOS
- **API Docs (Interactive)** — Visit `/docs` after starting the API

---

## 🛠️ Development

### Run Tests
```bash
# Unit tests (coming soon)
pytest tests/
```

### Add New Endpoints
1. Create model in `api/models/`
2. Create repository in `api/repositories/`
3. Create route handler in `api/routes/`
4. Wire into `api/main.py`

### Database Migrations
SQL schema files are in `sentinel_spr019/database/schema/`

---

## 🐛 Troubleshooting

**Port already in use?**
```bash
# Change API_PORT in .env
API_PORT=8001
docker-compose down && docker-compose up -d
```

**Database not persisting?**
```bash
# Check volume mount in docker-compose.yml
docker volume ls
docker volume inspect dayz-sentinel_db-volume
```

**API not responding?**
```bash
# Check logs
docker-compose logs -f sentinel
```

---

## 📝 License

Private repository - Anthropic/Internal Use

---

## 🤝 Contributing

Contributions follow the SPR (Sprint Requirement) system:
1. Check open SPRs in `/docs`
2. Create a feature branch
3. Implement and test
4. Document in SPR markdown
5. Submit PR with SPR reference

---

## 📞 Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check existing SPR documentation
- Review API documentation at `/docs` endpoint

---

**Last Updated:** 2026-06-17  
**Status:** Active Development (SPR-020 in progress)
