# ADR-0001 · Economy Items Schema

**Date:** 2026-06-17
**Status:** ✅ Accepted

---

## Problem

The `economy_items` table exists in two forms across the project:

1. **`sentinel_v1_schema.sql`** — the original schema file defines columns  
   `item_name TEXT`, `quantmin INTEGER`, `quantmax INTEGER`, `cost INTEGER`

2. **Live `sentinel.db`** — the deployed database (and all API code) uses  
   `name TEXT`, `min_value INTEGER`, `max_value INTEGER`  
   (no `cost` column)

A new `types_importer.py` must write to this table. The importer must decide which column naming convention to target.

---

## Options

### Option A — Follow the Schema File (`item_name`, `quantmin`, `quantmax`)

- Advantage: consistent with the checked-in `.sql` file
- Disadvantage: breaks all existing API queries (`economy_items_repository.py` uses `name`, `min_value`, `max_value`); the live database already diverged; no migration was ever created

### Option B — Follow the Live DB and API (`name`, `min_value`, `max_value`)  ✅ Chosen

- Advantage: consistent with the running application; all repository queries work unchanged
- Advantage: the schema file (`sentinel_v1_schema.sql`) already defines these columns as of its current committed state (the schema file was updated to match the deployed DB before this ADR)
- Disadvantage: none — both artefacts now agree

### Option C — Support both via migration

- Advantage: backward compatibility with any stale DB instances
- Disadvantage: added complexity; unnecessary for a single-node deployment where the DB is managed directly; the importer already performs schema introspection and can rename legacy columns automatically

---

## Chosen Solution

**Option B: use `name`, `min_value`, `max_value`** as the canonical column set.

`types_importer.py` targets these columns and includes defensive migration logic
(`_ensure_items_table`) to rename legacy columns (`item_name → name`,
`quantmin → min_value`, `quantmax → max_value`) when found in an older DB.

---

## Rationale

- The live `sentinel.db` and every API repository already use `name` / `min_value` / `max_value`.
- Maintaining a second naming convention solely because an old schema file used different names would introduce an unnecessary source of confusion.
- The `sentinel_v1_schema.sql` file already reflects the correct column names, eliminating the discrepancy noted in ARCHITECTURE.md §4.
- The defensive migration path in `_ensure_items_table` means no manual DB migration is needed for instances that were created from the old schema.

---

## Consequences

✅ `types_importer.py` and all API repositories use the same column names  
✅ Schema file and live DB are now consistent  
✅ No schema migration required for fresh installs  
⚠️ Existing DBs with the old column names (`item_name`, `quantmin`, `quantmax`)
   will be migrated in-place on first `import_types()` run — this is intentional

---

*Decision by: Copilot Coding Agent · SPR-021*
