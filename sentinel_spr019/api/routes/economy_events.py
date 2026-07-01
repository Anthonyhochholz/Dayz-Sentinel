import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sentinel_spr019.api.repositories.economy_events_repository import EconomyEventsRepository
from sentinel_spr019.api.security import require_write_api_key

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/economy", tags=["economy-events"])


@router.get("/events", response_model=dict)
async def get_events(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    active_only: bool = Query(False),
    search: Optional[str] = Query(None)
):
    """
    Get all economy events with pagination and optional filters.

    - **limit**: Number of events to return (1-1000, default 100)
    - **offset**: Number of events to skip (default 0)
    - **active_only**: Filter for active events only (default false)
    - **search**: Optional search query to filter events by name

    Returns paginated list of events with total count.
    """
    try:
        if search:
            events, total = EconomyEventsRepository.search(search, limit, offset, active_only)
            return {
                "data": events,
                "total": total,
                "limit": limit,
                "offset": offset,
                "active_only": active_only,
                "search": search
            }
        else:
            events, total = EconomyEventsRepository.get_all(limit, offset, active_only)
            return {
                "data": events,
                "total": total,
                "limit": limit,
                "offset": offset,
                "active_only": active_only
            }
    except Exception as e:
        LOGGER.exception("Error in get_events")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/events/{event_name}", response_model=dict)
async def get_event(event_name: str):
    """
    Get a specific economy event by name.

    - **event_name**: The name of the event to retrieve

    Returns event details or 404 if not found.
    """
    try:
        event = EconomyEventsRepository.get_by_name(event_name)
        if not event:
            raise HTTPException(
                status_code=404,
                detail=f"Event '{event_name}' not found"
            )
        return event
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.exception("Error in get_event: %s", event_name)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/events/{event_name}/toggle-active", response_model=dict)
async def toggle_event_active(event_name: str, _auth: None = Depends(require_write_api_key)):
    """
    Toggle the active status of an economy event.

    - **event_name**: The name of the event to toggle

    Returns the new active status.
    """
    try:
        new_status = EconomyEventsRepository.toggle_active(event_name)
        return {
            "event_name": event_name,
            "active": new_status,
            "message": f"Event set to {'active' if new_status else 'inactive'}"
        }
    except Exception as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        LOGGER.exception("Error in toggle_event_active: %s", event_name)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/events/stats/count", response_model=dict)
async def get_events_count(active_only: bool = Query(False)):
    """
    Get total count of economy events.

    - **active_only**: Count only active events (default false)

    Returns the total number of events in the database.
    """
    try:
        count = EconomyEventsRepository.get_count(active_only)
        return {
            "total": count,
            "active_only": active_only
        }
    except Exception as e:
        LOGGER.exception("Error in get_events_count")
        raise HTTPException(status_code=500, detail="Internal server error")
