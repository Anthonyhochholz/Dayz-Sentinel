from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Liveness probe payload."""

    status: str = Field(examples=["ok"])


class PaginationMeta(BaseModel):
    """Fields every paginated envelope carries."""

    total: int = Field(description="Total number of rows matching the query, ignoring pagination")
    limit: int = Field(description="Maximum number of rows returned in this response")
    offset: int = Field(description="Number of rows skipped before this page")
