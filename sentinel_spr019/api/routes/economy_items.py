
from fastapi import APIRouter
from sentinel_spr019.api.repositories.economy_repository import EconomyRepository

router = APIRouter()
repo = EconomyRepository()

@router.get("/api/v1/economy/items")
def get_items():
    return repo.get_items()
