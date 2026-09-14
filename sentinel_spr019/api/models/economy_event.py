from pydantic import BaseModel, ConfigDict, Field

from sentinel_spr019.api.models.common import PaginationMeta


class EconomyEvent(BaseModel):
    """A single row of `economy_events`.

    `active` is stored as an INTEGER flag and is exposed as a boolean so that
    the read endpoints agree with the toggle endpoint, which has always
    returned a real boolean.
    """

    model_config = ConfigDict(from_attributes=True)

    event_name: str
    nominal: int | None = None
    min_count: int | None = None
    max_count: int | None = None
    lifetime: int | None = None
    restock: int | None = None
    saferadius: float | None = None
    distanceradius: float | None = None
    cleanupradius: float | None = None
    position_mode: str | None = None
    limit_mode: str | None = None
    active: bool | None = None


class EconomyEventListResponse(PaginationMeta):
    """Paginated `economy_events` collection."""

    data: list[EconomyEvent]
    active_only: bool = Field(description="Echo of the applied active-only filter")
    search: str | None = Field(
        default=None,
        description="Echo of the applied search filter; null when no filter was applied",
    )


class EconomyEventCountResponse(BaseModel):
    """Row count for `economy_events`."""

    total: int
    active_only: bool


class EconomyEventToggleResponse(BaseModel):
    """Result of flipping an event's active flag."""

    event_name: str
    active: bool
    message: str
