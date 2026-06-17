from fastapi import APIRouter, HTTPException, Query

from sentinel_spr019.api.repositories.economy_events_repository import EconomyEventsRepository

router = APIRouter()
repo = EconomyEventsRepository()


@router.get("/api/v1/economy/events")
def get_events(
    limit: int = Query(default=100, le=500),
    active_only: bool = Query(default=False)
):
    """Return economy events, optionally filtered to active=1 only."""
    return repo.get_events(limit=limit, active_only=active_only)


@router.get("/api/v1/economy/events/{event_name}")
def get_event(event_name: str):
    """Return a single event by name."""
    event = repo.get_event_by_name(event_name)
    if not event:
        raise HTTPException(status_code=404, detail=f"Event '{event_name}' not found")
    return event
