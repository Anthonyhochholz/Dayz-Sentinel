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

## P2 — Near-Term Platform Expansion

| ID | Task | Why it matters | References |
|----|------|----------------|------------|
| P2-001 | Build the Mirror Scanner framework | Establishes the entrypoint for ingesting a full DayZ server mirror instead of ad hoc single-file imports | Platform vision |
| P2-002 | Add file type detection in the File Discovery Engine | Required to classify economy XML, cluster XML, spawn XML, world XML, ADM logs, RPT logs, and generic logs | Platform vision |
| P2-003 | Implement cluster and world importers | Activates existing schema for cluster instances, map objects, and territory-related data | Existing schema |
| P2-004 | Implement log importers for ADM, RPT, and generic log sources | Unlocks server intelligence beyond static economy data | Existing schema, `sentinel_v1_schema_rev2.sql` |
| P2-005 | Create the Analytics Engine foundation | Needed for cross-source correlation, derived metrics, and intelligence outputs | Platform vision |
| P2-006 | Add API route and integration tests beyond the importer suite | Current automated coverage is concentrated on `types_importer.py` | Sprint carry-over |

## P3 — Platform Maturity and Delivery

| ID | Task | Why it matters | References |
|----|------|----------------|------------|
| P3-001 | Ship a dashboard for server intelligence and operations | Provides the primary operator-facing surface for analytics and mirror visibility | Platform vision |
| P3-002 | Rename `sentinel_spr019` to a stable package name | Current package name is sprint-coupled and brittle | AUDIT-011 |
| P3-003 | Wire existing Pydantic models into route `response_model` declarations | Restores typed OpenAPI output and removes model dead-weight | Existing models |
| P3-004 | Add configurable CORS middleware | Required before any browser-based UI can call the API | AUDIT-012 |
| P3-005 | Add rate limiting for read and write endpoints | Reduces abuse and complements future authentication | SEC-007 |
| P3-006 | Add schema migration tooling | Database changes are still manual and platform expansion will increase schema churn | Existing schema |
| P3-007 | Improve health checks and operational readiness metadata | Current health endpoint does not verify backing services or ingestion readiness | Security audit follow-up |

## Future Ideas

- PostgreSQL backend option for larger deployments
- Real-time log streaming
- Discord notifications
- Map visualization
