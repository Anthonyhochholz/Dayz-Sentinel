# Roadmap — DayZ Sentinel

> Future work only. Completed work belongs in `docs/CHANGELOG.md`; current state belongs in `docs/PROJECT_MEMORY.md`.

## P1 — Critical / Security / Production Readiness

| ID | Task | Why it matters | References |
|----|------|----------------|------------|
| P1-001 | Add authentication to `POST /api/v1/economy/events/{event_name}/toggle-active` | The only write endpoint is currently unauthenticated | AUDIT-001, SEC-001 |
| P1-002 | Load application settings from `.env` and wire Docker env loading end-to-end | Future secrets and configuration are not available to Python code | SEC-002 |
| P1-003 | Stop tracking the live SQLite database in git and add a reproducible DB bootstrap path | Current repo contains `sentinel.db`, which is a data exposure and maintenance risk | SEC-003 |
| P1-004 | Finish the generic error-response cleanup for the toggle-active not-found path | One route still exposes `str(e)` in a 404 response | SEC-004 |
| P1-005 | Move synchronous SQLite work off the async event loop | Current handlers can block concurrent requests | SEC-006 |

## P2 — Near-Term Engineering Work

| ID | Task | Why it matters | References |
|----|------|----------------|------------|
| P2-001 | Pin dependency versions in `requirements.txt` | Reproducible installs and safer upgrades | Former P2-008 |
| P2-002 | Rename `sentinel_spr019` to a stable package name | Current package name is sprint-coupled and brittle | AUDIT-011 |
| P2-003 | Wire existing Pydantic models into route `response_model` declarations | Restores typed OpenAPI output and removes model dead-weight | P3-007, P3-009 |
| P2-004 | Harden `events_importer.py` with upsert behavior, transaction safety, and logging | Re-imports currently skip duplicates and provide limited operational feedback | Audit follow-up |
| P2-005 | Add API route and integration tests beyond the importer suite | Current automated coverage is concentrated on `types_importer.py` | Sprint carry-over |

## P3 — Planned Expansion

| ID | Task | Why it matters | References |
|----|------|----------------|------------|
| P3-001 | Add configurable CORS middleware | Required before any browser-based UI can call the API | AUDIT-012 |
| P3-002 | Add rate limiting for read and write endpoints | Reduces abuse and complements future authentication | SEC-007 |
| P3-003 | Add schema migration tooling | Database changes are still manual | P3-006 |
| P3-004 | Implement player log import pipeline | Player/session tables exist but have no importer | Existing schema |
| P3-005 | Implement server session and script log import | Logging/session tables exist but have no importer | Existing schema |
| P3-006 | Implement damage-event import and analytics | Combat-related tables exist but are unused | Existing schema |
| P3-007 | Improve health checks and operational readiness metadata | Current health endpoint does not verify backing services | Security audit follow-up |

## Future Ideas

- Web UI for event management and server visibility
- PostgreSQL backend option for larger deployments
- Real-time log streaming
- Discord notifications
- Map visualization
