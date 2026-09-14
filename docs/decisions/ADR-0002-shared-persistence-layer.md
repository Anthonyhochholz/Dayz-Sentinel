# ADR-0002 · Shared Persistence Layer

**Date:** 2026-09-12
**Status:** ✅ Accepted
**Supersedes in part:** ADR-002 (Repository Pattern for Data Access)

## Context

`importer/import_pipeline.py` imported `ImportTrackingRepository` from
`api/repositories/`, so the importer layer depended on the API layer purely to
reach shared database code. This was tracked as ARCH-001 and P1-001.

Two further problems shared the same root cause:

- `PRAGMA foreign_keys = ON` appears in both schema files, but the pragma is
  per-connection. It applied only to the connection that executed the schema
  script, so `events_importer.py` and `adm_importer.py` — which each called
  `sqlite3.connect()` directly — wrote without referential integrity enforced,
  while `types_importer.py` and the tracking repository happened to set it.
- The default database path was defined twice: in `api/database.py` and again
  in `import_pipeline.py`.

## Decision

Introduce `sentinel_spr019/persistence/` as a layer that depends on neither the
API nor the importer layer, and have both depend on it.

- `persistence/connection.py` holds the database bootstrap, the default path,
  `dict_factory`, and `connect()`.
- `connect()` is the only sanctioned way to open a SQLite connection and
  applies `PRAGMA foreign_keys = ON`.
- `persistence/import_tracking_repository.py` holds the import-tracking access
  used by both layers.
- Domain repositories that only the API uses (`economy_items`,
  `economy_events`) stay in `api/repositories/`, per ADR-002.

## Alternatives Considered

| Option | Reason Not Chosen |
|--------|-------------------|
| Keep the cross-layer import | Leaves the API layer as an implicit dependency of every importer run |
| Duplicate the tracking repository in the importer | Two copies of the same schema and SQL to keep in sync |
| Dependency injection of a repository interface | More indirection than a single-process SQLite app needs |
| Set the pragma in each importer | The omission that caused the bug would simply recur |

## Consequences

✅ The importer layer runs without importing any API code
✅ Referential integrity is enforced on every connection, not incidentally
✅ One definition of the default database path
✅ Two guard tests fail if the boundary is crossed again or an importer calls
   `sqlite3.connect()` directly (`tests/test_persistence_and_layering.py`)
⚠️ `api/database.py` is gone; imports move to
   `sentinel_spr019.persistence.connection`
⚠️ Enforced foreign keys mean a future importer that inserts rows out of
   dependency order now fails instead of writing orphans — intended, but it
   changes how such a bug surfaces
