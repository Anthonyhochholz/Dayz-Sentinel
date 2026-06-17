# GET /api/v1/economy/events

Returns all economy events from the economy_events table.

Query params:
- limit (int, default 100, max 500)
- active_only (bool, default false)

# GET /api/v1/economy/events/{event_name}
Returns a single event by name. 404 if not found.
