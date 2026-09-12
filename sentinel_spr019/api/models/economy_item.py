from pydantic import BaseModel, ConfigDict, Field

from sentinel_spr019.api.models.common import PaginationMeta


class EconomyItem(BaseModel):
    """A single row of `economy_items`.

    Every numeric column is nullable in the schema, because `types.xml` is not
    required to declare them, so the model keeps them optional rather than
    failing response validation on a sparse row.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str
    nominal: int | None = None
    min_value: int | None = None
    max_value: int | None = None
    restock: int | None = None
    lifetime: int | None = None


class EconomyItemListResponse(PaginationMeta):
    """Paginated `economy_items` collection."""

    data: list[EconomyItem]
    search: str | None = Field(
        default=None,
        description="Echo of the applied search filter; null when no filter was applied",
    )


class EconomyItemCountResponse(BaseModel):
    """Row count for `economy_items`."""

    total: int
