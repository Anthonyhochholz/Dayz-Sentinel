# SPR-020 — Integration Testing & Security Fixes

**Status:** 🔄 In Progress  
**Start Date:** 2026-06-17  
**Target End:** TBD  
**Milestone:** MILESTONE-002

---

## Goal

1. Implement automated integration tests that spin up FastAPI with an in-memory DB and assert row counts and response shapes.
2. Address all P1 (Critical/High security) audit findings.
3. Fix README documentation discrepancies.

---

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `pytest` suite with ≥1 test per endpoint | 📋 Pending |
| 2 | All tests pass: `pytest tests/` | 📋 Pending |
| 3 | API-Key auth on `toggle-active` endpoint | 📋 Pending |
| 4 | HTTP 500 returns generic message (no `str(e)`) | 📋 Pending |
| 5 | All DB connections use context manager | 📋 Pending |
| 6 | f-String SQL replaced in `economy_events_repository.py` | 📋 Pending |
| 7 | `API_PORT` read from `.env` in Docker setup | 📋 Pending |
| 8 | README endpoint docs corrected | 📋 Pending |

---

## Tasks

### P1 Security (AUDIT-001 to AUDIT-005)

- [ ] **P1-001** — Create `api/auth.py` with API-Key dependency  
  Files: `api/auth.py` (new), `api/routes/economy_events.py`

- [ ] **P1-002** — Replace `detail=str(e)` with generic messages + logging  
  Files: `routes/economy_items.py:43,66,80`, `routes/economy_events.py:47,70,92,111`

- [ ] **P1-003** — Wrap `sqlite3.connect()` in `@contextmanager` in `database.py`  
  Files: `api/database.py`, all 3 repository files

- [ ] **P1-004** — Replace f-String SQL in `economy_events_repository.py`  
  Files: `repositories/economy_events_repository.py:30,36-44,107-114,130`

- [ ] **P1-005** — Fix Docker env loading  
  Files: `docker-compose.yml`, `Dockerfile`, `requirements.txt`

### Documentation

- [ ] Fix `README.md` health endpoint path (`/health` → `/api/v1/health`)
- [ ] Remove non-existent `?type=weapon` parameter from README
- [ ] Fix health check response (`"operational"` → `"ok"`)

### Testing

- [ ] Create `tests/` directory
- [ ] Create `tests/conftest.py` with in-memory DB fixture
- [ ] Create `tests/test_economy_items.py`
- [ ] Create `tests/test_economy_events.py`
- [ ] Create `tests/test_health.py`

---

## Notes

> Add implementation notes, blockers, or decisions here during the sprint.

---

*Created: 2026-06-17*
