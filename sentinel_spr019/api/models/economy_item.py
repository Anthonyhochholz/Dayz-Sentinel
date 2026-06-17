from pydantic import BaseModel
from typing import Optional


class EconomyItemBase(BaseModel):
    """Base model for economy items"""
    name: str
    nominal: float
    min_value: float
    max_value: float
    restock: float
    lifetime: float


class EconomyItem(EconomyItemBase):
    """Full economy item model"""
    id: Optional[int] = None

    class Config:
        from_attributes = True


class EconomyItemResponse(BaseModel):
    """Response model for economy items"""
    name: str
    nominal: float
    min_value: float
    max_value: float
    restock: float
    lifetime: float

    class Config:
        from_attributes = True
