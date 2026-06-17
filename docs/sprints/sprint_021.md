# SPR-021 — Code Quality & P2 Fixes

**Status:** 📋 Planned  
**Start Date:** TBD  
**Target End:** TBD  
**Predecessor:** SPR-020

---

## Goal

Address all P2 (Medium) audit findings, improve overall code quality, and ensure the import pipeline is complete and reproducible.

---

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `dict_factory` defined once in `database.py` | 📋 Pending |
| 2 | `economy_repository.py` deleted | 📋 Pending |
| 3 | Unused model imports removed from repositories | 📋 Pending |
| 4 | `requests` present in `requirements.txt` | 📋 Pending |
| 5 | `types_importer.py` implemented and tested | 📋 Pending |
| 6 | `offset` supported in all `search()` methods | 📋 Pending |
| 7 | All dependencies pinned in `requirements.txt` | 📋 Pending |

---

## Tasks

### Code Quality (AUDIT-006 to AUDIT-010)

- [ ] **CQ-001** — Move `dict_factory` to `database.py`, update all imports  
  Files: `database.py`, `economy_items_repository.py:128-131`, `economy_events_repository.py:177-180`

- [ ] **CQ-002a** — Delete `economy_repository.py`

- [ ] **CQ-002b** — Remove unused model imports from repositories  
  Files: `economy_items_repository.py:2`, `economy_events_repository.py:2`

- [ ] **CQ-003** — Add `requests` to `requirements.txt`

- [ ] **CQ-004** — Implement `types_importer.py`  
  New file: `importer/economy/types_importer.py`  
  Fix reference: `scripts/test_import_run.py:4`

- [ ] **CQ-005** — Add `offset` to all `search()` methods and SQL queries  
  Files: `economy_items_repository.py:79`, `economy_events_repository.py:85`

- [ ] **CQ-006** — Pin all dependency versions  
  File: `requirements.txt`

---

## Notes

> Add implementation notes, blockers, or decisions here during the sprint.

---

*Created: 2026-06-17*
