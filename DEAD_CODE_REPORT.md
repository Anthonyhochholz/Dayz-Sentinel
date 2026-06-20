# Dead Code Report — DayZ Sentinel

**Date:** 2026-06-20  
**Auditor:** Copilot Architecture Audit  
**Method:** Static analysis of all import graphs and runtime usage

---

## Summary

| Deletion Safety | Count |
|-----------------|-------|
| SAFE TO DELETE | 5 |
| VERIFY FIRST | 4 |
| DO NOT DELETE | 2 |

---

## Unused Files

### DC-001 · `docs/copilot-audits/types_importer_implementation_report.md`

| Field | Detail |
|-------|--------|
| **Type** | Documentation file |
| **Reason unused** | Documents the design process for `types_importer.py`, which is now implemented and shipped in v0.4.0. The design document served its purpose and has been superseded by the implementation itself. |
| **Deletion safety** | **SAFE TO DELETE** — All decisions are captured in `ADR-0001-economy-items-schema.md`. No code references this file. |

---

### DC-002 · `docs/copilot-audits/types_importer_final_implementation.md`

| Field | Detail |
|-------|--------|
| **Type** | Documentation file |
| **Reason unused** | Documents the final implementation of `types_importer.py`. Superseded by the actual implementation file `sentinel_spr019/importer/economy/types_importer.py`. |
| **Deletion safety** | **SAFE TO DELETE** — The implementation is the authoritative source. |

---

### DC-003 · `docs/copilot-audits/current_state_report.md`

| Field | Detail |
|-------|--------|
| **Type** | Documentation file |
| **Reason unused** | Point-in-time snapshot of project state from 2026-06-17. Superseded by `PROJECT_STATUS.md` and `docs/PROJECT_MEMORY.md` which are actively maintained. |
| **Deletion safety** | **SAFE TO DELETE** — Current state is documented in live, maintained files. |

---

## Unused Classes

### DC-004 · `EconomyItemBase` — `sentinel_spr019/api/models/economy_item.py:5`

| Field | Detail |
|-------|--------|
| **Type** | Pydantic model class |
| **Reason unused** | No production code imports this class. Routes use `response_model=dict`. Repositories return raw `dict`. The class is only subclassed by `EconomyItem` and `EconomyItemResponse`, which are themselves unused. |
| **Deletion safety** | **VERIFY FIRST** — Before deleting, confirm no external code (future plugins, scripts) imports from `sentinel_spr019.api.models`. Then proceed with deletion or, preferably, wire into routes. |

---

### DC-005 · `EconomyItem` — `sentinel_spr019/api/models/economy_item.py:15`

| Field | Detail |
|-------|--------|
| **Type** | Pydantic model class |
| **Reason unused** | Subclass of `EconomyItemBase` with an optional `id` field. Never used by any repository, route, or test. The `Config: from_attributes = True` setting (for ORM mode) is irrelevant since no ORM is used. |
| **Deletion safety** | **VERIFY FIRST** — Same caveat as DC-004. |

---

### DC-006 · `EconomyItemResponse` — `sentinel_spr019/api/models/economy_item.py:23`

| Field | Detail |
|-------|--------|
| **Type** | Pydantic model class |
| **Reason unused** | Duplicates all fields of `EconomyItemBase` without inheriting from it. Never used by any route as `response_model`. Dead code that also contains a DRY violation. |
| **Deletion safety** | **VERIFY FIRST** — Same caveat as DC-004. Preferred action: make this the `response_model` for `GET /items` endpoints instead of deleting. |

---

### DC-007 · `EconomyEventBase` — `sentinel_spr019/api/models/economy_event.py:5`

| Field | Detail |
|-------|--------|
| **Type** | Pydantic model class |
| **Reason unused** | No production code imports this class. All 12 fields are dead. |
| **Deletion safety** | **VERIFY FIRST** — Confirm nothing external imports it. Preferred action: wire into routes. |

---

### DC-008 · `EconomyEvent` — `sentinel_spr019/api/models/economy_event.py:21`

| Field | Detail |
|-------|--------|
| **Type** | Pydantic model class |
| **Reason unused** | Subclass of `EconomyEventBase` with optional `id`. Never instantiated or used anywhere. |
| **Deletion safety** | **VERIFY FIRST** |

---

### DC-009 · `EconomyEventResponse` — `sentinel_spr019/api/models/economy_event.py:29`

| Field | Detail |
|-------|--------|
| **Type** | Pydantic model class |
| **Reason unused** | Duplicates all 12 fields of `EconomyEventBase` without inheriting. Never used as `response_model`. Dead code + DRY violation. |
| **Deletion safety** | **VERIFY FIRST** — Preferred action: wire into routes. |

---

## Unused Functions

### DC-010 · `EconomyItemsRepository.get_count()` — `economy_items_repository.py:111`

| Field | Detail |
|-------|--------|
| **Type** | Repository static method |
| **Reason unused** | Called only by `GET /api/v1/economy/items/stats/count` — which IS a live endpoint. |
| **Deletion safety** | **DO NOT DELETE** — Actively used. Listed here for completeness. |

> Note: All repository methods (`get_all`, `get_by_name`, `search`, `get_count`) and `toggle_active` are actively called by route handlers. No repository methods are dead.

---

## Unused Endpoints

No endpoints are technically unused — all 9 endpoints in the API are reachable and respond. However:

### DC-011 · Route Utility Issue: `GET /api/v1/economy/items/stats/count`

| Field | Detail |
|-------|--------|
| **Type** | API endpoint |
| **Concern** | This endpoint (`/items/stats/count`) is registered in `economy_items.py` AFTER the `GET /items/{item_name}` catch-all route. In FastAPI, `/items/stats` would match the `{item_name}` route with `item_name="stats"`. `/items/stats/count` has two path segments, so it does NOT conflict with `{item_name}`. However, any GET to `/api/v1/economy/items/stats` (one segment) returns a 404 "Item 'stats' not found" rather than a meaningful route. |
| **Deletion safety** | **DO NOT DELETE** — Functional endpoint. Register it BEFORE `{item_name}` as a defensive measure. |

---

## Unused Models

### DC-012 · `sentinel_spr019/api/models/` directory

| Field | Detail |
|-------|--------|
| **Type** | Python package (directory + 3 files) |
| **Reason unused** | Contains 6 Pydantic model classes (DC-004 through DC-009). Not one of these classes is imported by any production code. The directory exists but is architecturally disconnected. |
| **Deletion safety** | **VERIFY FIRST** — The preferred action is NOT to delete but to activate: wire the models into routes as `response_model` arguments, giving the application actual OpenAPI schema generation. Only delete if a decision is made to use a different schema approach. |

---

## Unused Repositories

No repositories are unused — both `EconomyItemsRepository` and `EconomyEventsRepository` are fully active. 

The previously identified `economy_repository.py` (dead code from the initial prototype) was deleted in SPR-021 (AUDIT-007 resolved).

---

## Unused Tables (Database)

The following tables are defined in the schema and exist in `sentinel.db` but contain zero rows and have no corresponding importer, repository, or API endpoint:

| Table | Domain | Status |
|-------|--------|--------|
| `economy_item_flags` | Economy metadata | Empty; `types_importer.py` populates it — populated after fresh import |
| `economy_event_flags` | Economy metadata | Empty; `events_importer.py` does NOT populate it |
| `economy_event_secondary` | Economy metadata | Empty; no importer |
| `economy_event_children` | Economy metadata | Empty; no importer |
| `group_prototypes` | World/Map | Empty; no importer |
| `group_categories` | World/Map | Empty; no importer |
| `group_prototype_categories` | World/Map | Empty; no importer |
| `group_usages` | World/Map | Empty; no importer |
| `group_prototype_usages` | World/Map | Empty; no importer |
| `group_tags` | World/Map | Empty; no importer |
| `group_prototype_tags` | World/Map | Empty; no importer |
| `group_points` | World/Map | Empty; no importer |
| `group_proxies` | World/Map | Empty; no importer |
| `cluster_instances` | World/Map | Empty; no importer |
| `map_objects` | World/Map | Empty; no importer |
| `territory_files` | World/Map | Empty; no importer |
| `territories` | World/Map | Empty; no importer |
| `territory_zone_types` | World/Map | Empty; no importer |
| `territory_zones` | World/Map | Empty; no importer |
| `players` | Player | Empty; no importer |
| `player_sessions` | Player | Empty; no importer |
| `player_positions` | Player | Empty; no importer |
| `player_damage_events` | Player | Empty; no importer |
| `player_actions` | Player | Empty; no importer |
| `server_sessions` | Server | Empty; no importer |
| `import_sources` | Meta | Empty; no importer |
| `import_runs` | Meta | Empty; no importer |
| `localization_errors` | Logging | Empty; no importer |
| `network_events` | Logging | Empty; no importer |
| `script_sessions` | Logging | Empty; no importer |
| `script_engine_events` | Logging | Empty; no importer |
| `script_logout_events` | Logging | Empty; no importer |
| `script_persistence_events` | Logging | Empty; no importer |
| `script_errors` | Logging | Empty; no importer |

**Deletion safety for unused tables:** **DO NOT DELETE** — These tables represent planned features documented in the ROADMAP. They are structural placeholders, not dead code. Their presence in the schema is intentional and their foreign key relationships should be preserved for when importers are built.

---

## Unused Imports (Code-Level)

The following imports exist in source files but are not used:

| File | Import | Status |
|------|--------|--------|
| `routes/economy_items.py:3` | `from typing import List` | Unused — `List` is not used in this file (only `Optional`) |
| `routes/economy_items.py:3` | `from typing import Optional` | Used — keep |
| `routes/economy_events.py:3` | `from typing import Optional` | Used — keep |

> Note: Previous issues with unused Pydantic model imports in repository files (AUDIT-008) have been resolved in SPR-021. The repositories correctly import only `logging`, `typing`, and `database`.

---

*Last updated: 2026-06-20 · Full repository audit*
