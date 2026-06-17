# Backlog — Unscheduled Items

Items that have been identified but not yet assigned to a sprint.

---

## P2 — High Priority (Unscheduled)

| ID | Task | Audit Ref | Notes |
|----|------|-----------|-------|
| P2-006 | Rename package `sentinel_spr019` → `sentinel` | AUDIT-011 | Breaking change; requires updating all imports, Dockerfile, docker-compose |
| P2-007 | Add `pytest` suite with in-memory SQLite fixtures | — | Requires `httpx` as test client |
| P2-008 | Pin dependency versions in `requirements.txt` | — | |

---

## P3 — Medium Priority (Unscheduled)

| ID | Task | Notes |
|----|------|-------|
| P3-001 | Add `CORSMiddleware` with configurable origins | AUDIT-012 |
| P3-003 | Player log import pipeline | Schema exists: `players`, `player_sessions`, `player_positions` |
| P3-004 | Server session log import | Schema exists: `server_sessions`, `script_sessions` |
| P3-005 | Damage event import + analytics endpoint | Schema exists: `player_damage_events` |
| P3-006 | Schema migration tooling (Alembic or custom runner) | Two schema files, no runner |
| P3-007 | Typed OpenAPI response schemas (replace `response_model=dict`) | |
| P3-008 | Rate limiting (`slowapi`) | |
| P3-009 | Repository methods return Pydantic models instead of `dict` | |

---

## 💡 Future Ideas

| Idea | Description | Effort |
|------|-------------|--------|
| Web UI | Minimal admin dashboard for event management | Large |
| PostgreSQL option | Optional PG backend for high-traffic deployments | Large |
| Real-time log streaming | WebSocket endpoint for live server log monitoring | Medium |
| Discord integration | Push notifications on player events | Medium |
| Map visualization | 2D heat-map of player positions | Large |
| Scheduled XML re-import | Periodic re-import from configured XML paths | Small |

---

## Completed (Reference)

| Task | Sprint |
|------|--------|
| Economy items import (1,917 items) | SPR-010 |
| Economy items API endpoints | SPR-015 |
| Economy events import (58 events) | SPR-016–018 |
| Economy events API + toggle | SPR-019 |
| Docker + Compose setup | SPR-019 |

---

*Last updated: 2026-06-17*
