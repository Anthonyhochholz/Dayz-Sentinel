from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from sentinel_spr019.api.models.economy_item import EconomyItemResponse
from sentinel_spr019.api.repositories.economy_items_repository import EconomyItemsRepository

router = APIRouter(prefix="/api/v1/economy", tags=["economy-items"])


@router.get("/items", response_model=dict)
async def get_items(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None)
):
    """
    Get all economy items with pagination and optional search
    
    - **limit**: Number of items to return (1-1000, default 50)
    - **offset**: Number of items to skip (default 0)
    - **search**: Optional search query to filter items by name
    
    Returns paginated list of items with total count
    """
    try:
        if search:
            items = EconomyItemsRepository.search(search, limit)
            return {
                "data": items,
                "total": len(items),
                "limit": limit,
                "offset": offset,
                "search": search
            }
        else:
            items, total = EconomyItemsRepository.get_all(limit, offset)
            return {
                "data": items,
                "total": total,
                "limit": limit,
                "offset": offset
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/items/{item_name}", response_model=dict)
async def get_item(item_name: str):
    """
    Get a specific economy item by name
    
    - **item_name**: The name of the item to retrieve
    
    Returns item details or 404 if not found
    """
    try:
        item = EconomyItemsRepository.get_by_name(item_name)
        if not item:
            raise HTTPException(
                status_code=404,
                detail=f"Item '{item_name}' not found"
            )
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/items/stats/count", response_model=dict)
async def get_items_count():
    """
    Get total count of economy items
    
    Returns the total number of items in the database
    """
    try:
        count = EconomyItemsRepository.get_count()
        return {"total": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
