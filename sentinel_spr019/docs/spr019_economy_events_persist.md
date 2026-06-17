# SPR-019: economy_events in SQLite persistieren und API vorbereiten

## Status
COMPLETE

## Executed
2026-06-16

## What was done

### 1. Database Migration
- Created `economy_events` table per `sentinel_v1_schema.sql` definition
- Table added to existing `sentinel.db` (which already contained 1917 `economy_items` rows)

### 2. Import
- Source: `_3/dayzps_missions/dayzOffline.chernarusplus/db/events.xml`
- Fixed `events_importer.py` — original only captured `name/nominal/min/max`
- Corrected importer now captures all 12 fields:
  `event_name, nominal, min_count, max_count, lifetime, restock,
   saferadius, distanceradius, cleanupradius, position_mode, limit_mode, active`
- Column name fixes: `name→event_name`, `min_value→min_count`, `max_value→max_count`

### 3. Validation
- Rows inserted: **58**
- Rows skipped:  0
- Active events: 50
- Inactive events: 8

### 4. API
- New: `GET /api/v1/economy/events?limit=100&active_only=false`
- New: `GET /api/v1/economy/events/{event_name}`
- Files added:
  - `api/models/economy_event.py`
  - `api/repositories/economy_events_repository.py`
  - `api/routes/economy_events.py`

## Next
SPR-020: Wire economy_events route into FastAPI app and run integration test.
