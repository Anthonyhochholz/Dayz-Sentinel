from pydantic import BaseModel
from typing import Optional


class EconomyEventBase(BaseModel):
    """Base model for economy events"""
    event_name: str
    nominal: float
    min_count: int
    max_count: int
    lifetime: int
    restock: int
    saferadius: float
    distanceradius: float
    cleanupradius: float
    position_mode: str
    limit_mode: str
    active: bool


class EconomyEvent(EconomyEventBase):
    """Full economy event model"""
    id: Optional[int] = None

    class Config:
        from_attributes = True


class EconomyEventResponse(BaseModel):
    """Response model for economy events"""
    event_name: str
    nominal: float
    min_count: int
    max_count: int
    lifetime: int
    restock: int
    saferadius: float
    distanceradius: float
    cleanupradius: float
    position_mode: str
    limit_mode: str
    active: bool

    class Config:
        from_attributes = True
