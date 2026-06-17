# types_importer Implementation Report

**Date:** 2026-06-17  
**Sprint:** SPR-021  
**Author:** Copilot Coding Agent

---

## Summary

This report documents the investigation, decisions, and deliverables produced
while implementing the `types_importer.py` economy items import pipeline for
DayZ Sentinel.

---

## 1. Changed Files

| File | Change Type | Description |
|------|-------------|-------------|
| `sentinel_spr019/importer/economy/types_importer.py` | **Verified / Already Implemented** | Full implementation was already present; verified correctness against schema and API |
| `sentinel_spr019/scripts/test_import_run.py` | **Verified** | Import path `sentinel_spr019.importer.economy.types_importer` confirmed correct; no change required |
| `tests/test_types_importer.py` | **Created** | 21 pytest unit tests covering all importer functionality |
| `docs/decisions/ADR-0001-economy-items-schema.md` | **Created** | Architecture Decision Record for canonical `economy_items` schema |
| `docs/ARCHITECTURE.md` | **Updated** | Import flow diagram, layer breakdown, removed "NOT IMPLEMENTED" annotation |
| `docs/PROJECT_MEMORY.md` | **Updated** | Component status, AUDIT-009 marked resolved, sprint updated to SPR-021 |
| `docs/ROADMAP.md` | **Updated** | P2-004 and P2-007 marked ✅ complete; completed section updated |
| `docs/CHANGELOG.md` | **Updated** | Added [0.4.0] release entry for SPR-021 |

---

## 2. Architecture Decisions

### ADR-0001: Canonical economy_items Schema

**Decision:** Use `name`, `min_value`, `max_value` as the canonical column names.

**Rationale:** The live `sentinel.db` and all API repositories already use these
names. The original schema file (`sentinel_v1_schema.sql`) contained a diverged
naming convention (`item_name`, `quantmin`, `quantmax`) that was never applied
to the deployed database. Targeting the column names already in production
eliminates an inconsistency without requiring a DB migration.

The importer includes defensive migration logic (`_ensure_items_table`) that
automatically renames legacy columns when it encounters them, covering any DB
instances created from the old schema file.

Full decision: `docs/decisions/ADR-0001-economy-items-schema.md`

### Duplicate Strategy: Upsert (Update Existing)

When `import_types()` is called again with the same (or updated) `types.xml`,
existing items are **updated** rather than skipped. This ensures the DB always
reflects the current state of the XML file.

- Economy items: `UPDATE … WHERE name = ?`
- Flags: `DELETE + INSERT` per item (full replacement)
- Relations (categories, usages, values, tags): `DELETE + INSERT` per item (full replacement)

This strategy is safe because `types.xml` is the authoritative source.

### Transaction Integrity

The entire import is wrapped in a single transaction:

```python
try:
    _ensure_schema(cur)
    for item in ...:
        _upsert_item(...)
        _sync_flags(...)
        _sync_relations(...)
    conn.commit()
except Exception:
    conn.rollback()
    raise
finally:
    conn.close()
```

If any row fails (e.g., constraint violation, unexpected column), the whole
import is rolled back — no partial imports can enter the DB.

### SQL Injection Prevention

All dynamic table and column references in `_replace_relations` pass through
`_validate_identifier()`, which checks against a fixed allowlist before
interpolating into SQL. This prevents any user-controlled value from reaching
the SQL query as an identifier.

---

## 3. Implementation Verification

### Schema Verification (pre-implementation)

| Artefact | `economy_items` columns |
|----------|------------------------|
| `sentinel_v1_schema.sql` | `id`, `name`, `nominal`, `lifetime`, `restock`, `min_value`, `max_value` |
| API repositories (`economy_items_repository.py`) | `name`, `nominal`, `min_value`, `max_value`, `restock`, `lifetime` |
| API model (`economy_item.py`) | `name`, `nominal`, `min_value`, `max_value`, `restock`, `lifetime` |
| Live `sentinel.db` | Consistent with API (1,917 rows) |

All four artefacts agree on the canonical column set → ADR-0001 Option B confirmed.

### Import Scope Verification

`types_importer.py` populates the following tables:

| Table | Populated | Method |
|-------|-----------|--------|
| `economy_items` | ✅ | Upsert per `<type name>` |
| `economy_item_flags` | ✅ | Replace per item from `<flags>` attrs |
| `economy_categories` | ✅ | INSERT OR IGNORE lookup |
| `economy_item_categories` | ✅ | Replace per item |
| `economy_usages` | ✅ | INSERT OR IGNORE lookup |
| `economy_item_usages` | ✅ | Replace per item |
| `economy_values` | ✅ | INSERT OR IGNORE lookup |
| `economy_item_values` | ✅ | Replace per item |
| `economy_tags` | ✅ | INSERT OR IGNORE lookup |
| `economy_item_tags` | ✅ | Replace per item |

---

## 4. Test Results

All 21 tests pass against the implementation.

```
tests/test_types_importer.py::TestBasicInsert::test_single_item_inserted             PASSED
tests/test_types_importer.py::TestBasicInsert::test_multiple_items_inserted           PASSED
tests/test_types_importer.py::TestBasicInsert::test_item_numeric_fields               PASSED
tests/test_types_importer.py::TestBasicInsert::test_item_without_name_is_skipped      PASSED
tests/test_types_importer.py::TestUpsertStrategy::test_reimport_updates_existing      PASSED
tests/test_types_importer.py::TestUpsertStrategy::test_idempotent_import              PASSED
tests/test_types_importer.py::TestFlags::test_flags_inserted                          PASSED
tests/test_types_importer.py::TestFlags::test_flags_updated_on_reimport               PASSED
tests/test_types_importer.py::TestFlags::test_item_without_flags_has_no_flags_row     PASSED
tests/test_types_importer.py::TestCategories::test_category_inserted                  PASSED
tests/test_types_importer.py::TestCategories::test_item_category_relation             PASSED
tests/test_types_importer.py::TestCategories::test_shared_category_deduplicated       PASSED
tests/test_types_importer.py::TestUsages::test_usage_inserted_and_linked              PASSED
tests/test_types_importer.py::TestValues::test_value_inserted_and_linked              PASSED
tests/test_types_importer.py::TestTags::test_tag_inserted_and_linked                  PASSED
tests/test_types_importer.py::TestMultipleRelations::test_multiple_usages             PASSED
tests/test_types_importer.py::TestMultipleRelations::test_relations_replaced_on_reimport PASSED
tests/test_types_importer.py::TestTransactions::test_rollback_on_error                PASSED
tests/test_types_importer.py::TestSchemaMigration::test_legacy_item_name_column_migrated PASSED
tests/test_types_importer.py::TestSchemaMigration::test_legacy_quantmin_quantmax_columns_migrated PASSED
tests/test_types_importer.py::TestLargeImport::test_hundred_items                     PASSED

21 passed in 0.39s
```

---

## 5. Open Risks

| Risk | Severity | Notes |
|------|----------|-------|
| `events_importer` uses skip-on-conflict; `types_importer` uses upsert | 🟡 Low | Inconsistency between importers. Consider aligning `events_importer` to also support upsert (ROADMAP P2-004 scope extension). |
| `economy_repository.py` is dead code | 🟡 Low | Exists but is unused. Removal tracked as ROADMAP P2-002. |
| No `pytest` coverage for API routes | 🟡 Low | The existing `scripts/test_api.py` requires a running server. `tests/test_types_importer.py` is the first standalone unit test. Route tests should follow (P2-007 extended). |
| Schema for `economy_items` columns uses `FLOAT` in ARCHITECTURE.md but `INTEGER` in schema SQL | 🔵 Info | The Pydantic model and repository accept `float`; SQLite stores as `INTEGER`. No runtime impact (SQLite is typeless), but documentation is inconsistent. |
| No `conftest.py` or `pytest.ini` | 🔵 Info | Tests currently run from repo root via `python -m pytest tests/`. Add a `pytest.ini` or `pyproject.toml` if test discovery becomes complex. |

---

## 6. Next Recommended Steps

1. **P2-001** — Centralize `dict_factory` in `database.py` (remove duplication).
2. **P2-002** — Delete `economy_repository.py` dead code.
3. **P2-003** — Add `requests` to `requirements.txt`.
4. **P2-005** — Fix ignored `offset` in `search()` methods.
5. **Add route unit tests** — extend `tests/` with repository-level tests using
   in-memory SQLite, parallel to the `types_importer` approach.
6. **Align `events_importer`** — consider adding upsert support so both importers
   are consistent.
7. **Add `conftest.py`** — define shared fixtures (e.g., `populated_db`) for future
   test expansion.

---

*Generated by: Copilot Coding Agent · 2026-06-17*
