# SPR-020 — Integration Testing & Security Fixes

**Status:** ⚠️ Archived with carry-over  
**Started:** 2026-06-17  
**Outcome:** Partial delivery; remaining work moved to `docs/ROADMAP.md`

---

## Goal

Improve production readiness through security fixes, testing, and README corrections.

## Delivered During This Sprint

- README endpoint examples were corrected.
- Generic HTTP 500 responses replaced most `detail=str(e)` behavior.
- SQL query construction for economy events was hardened.
- Docker Compose port mapping now reads `${API_PORT:-8000}`.
- `scripts/test_api.py` exists as an integration smoke-test runner.

## Not Delivered / Carried Forward

- Authentication for the toggle-active write endpoint.
- End-to-end `.env` loading inside the Python application.
- A true database connection context manager.
- Route-level automated tests for the API.
- Final cleanup of the toggle-active 404 response path.

## Notes

This sprint should be treated as a partial hardening pass rather than a completed security sprint.
