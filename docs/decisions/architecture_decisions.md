# Architecture Decision Records — DayZ Sentinel

---

## ADR-001 · Use SQLite as Primary Database

**Date:** 2026-06  
**Status:** ✅ Accepted

### Context

DayZ Sentinel needs to persist ~2,000 economy items, ~60 events, and future player/log data. The deployment target is a single self-hosted machine (CasaOS, Docker).

### Decision

Use SQLite as the only database engine, stored as a file on the host and volume-mounted into the container.

### Alternatives Considered

| Option | Reason Not Chosen |
|--------|-------------------|
| PostgreSQL | Requires separate container; overhead not justified for single-node |
| MySQL / MariaDB | Same overhead concern |
| In-memory store (Redis) | No persistence |

### Consequences

✅ Zero infra overhead — no separate DB container  
✅ Backup = copy single `.db` file  
✅ Volume mount in `docker-compose.yml` ensures persistence  
⚠️ Not suitable for high-concurrency writes (SQLite serializes writes)  
⚠️ No built-in user authentication at DB level  

---

## ADR-002 · Use Repository Pattern for Data Access

**Date:** 2026-06  
**Status:** ✅ Accepted

### Context

Routes need access to database data. Several options exist for structuring this access.

### Decision

Implement a Repository layer (`api/repositories/`) with static methods per domain object. Routes call repositories; repositories call `database.py`.

### Alternatives Considered

| Option | Reason Not Chosen |
|--------|-------------------|
| Direct DB calls in routes | Mixes concerns; makes testing harder |
| ORM (SQLAlchemy) | Additional dependency; team unfamiliar at sprint start |
| Active Record pattern | Not idiomatic for FastAPI + plain SQLite |

### Consequences

✅ Clear separation: routes handle HTTP, repositories handle SQL  
✅ Repositories can be tested in isolation with a test DB  
⚠️ Currently returns `dict` instead of typed models — weakens type safety  
⚠️ `dict_factory` duplicated (to be fixed in SPR-021)  

---

## ADR-003 · Sprint-Numbered Python Package Name

**Date:** 2026-06  
**Status:** ⚠️ Deprecated (superseded by pending ADR)

### Context

During early development, the package was named `sentinel_spr019` to track which sprint introduced the current implementation.

### Decision

Name the top-level Python package after the current sprint number.

### Consequences

⚠️ Breaks all imports, Docker config, and volume paths on every sprint rename  
⚠️ Sprint number in package name is unusual and confusing for new contributors  
⚠️ Violates Python packaging conventions  

### Superseding Decision (Planned — SPR-022)

Rename `sentinel_spr019` → `sentinel`. See ROADMAP.md P2-006.

---

## ADR-004 · FastAPI as Web Framework

**Date:** 2026-06  
**Status:** ✅ Accepted

### Context

Need a Python HTTP framework for the REST API.

### Decision

Use FastAPI with uvicorn as the ASGI server.

### Alternatives Considered

| Option | Reason Not Chosen |
|--------|-------------------|
| Flask | No async support; manual OpenAPI docs |
| Django REST Framework | Too heavyweight for a focused API |
| Starlette (raw) | FastAPI is built on Starlette with better DX |

### Consequences

✅ Automatic OpenAPI/Swagger UI at `/docs`  
✅ Pydantic validation built in  
✅ Async-ready for future performance needs  
✅ `Query()` helpers make parameter validation concise  
⚠️ `response_model=dict` currently defeats OpenAPI schema generation  

---

## ADR Template

Use this template for new decisions:

```markdown
## ADR-XXX · [Title]

**Date:** YYYY-MM  
**Status:** 📋 Proposed | ✅ Accepted | ❌ Rejected | ⚠️ Deprecated

### Context

[What is the problem or situation requiring a decision?]

### Decision

[What was decided?]

### Alternatives Considered

| Option | Reason Not Chosen |
|--------|-------------------|
| ... | ... |

### Consequences

[Positive and negative outcomes of the decision.]
```

---

*Last updated: 2026-06-17*
