from dataclasses import dataclass
from typing import Optional


@dataclass
class EconomyEvent:
    id: int
    event_name: str
    nominal: Optional[int]
    min_count: Optional[int]
    max_count: Optional[int]
    lifetime: Optional[int]
    restock: Optional[int]
    saferadius: Optional[float]
    distanceradius: Optional[float]
    cleanupradius: Optional[float]
    position_mode: Optional[str]
    limit_mode: Optional[str]
    active: Optional[int]
