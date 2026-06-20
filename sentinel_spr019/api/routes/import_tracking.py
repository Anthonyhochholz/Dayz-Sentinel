from fastapi import APIRouter, HTTPException, Query

from sentinel_spr019.api.repositories.import_tracking_repository import ImportTrackingRepository


router = APIRouter(prefix="/api/v1/import-tracking", tags=["import-tracking"])


@router.get("/scans", response_model=dict)
async def get_scans(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    try:
        scans = ImportTrackingRepository.list_scans(limit=limit, offset=offset)
        return {"data": scans, "limit": limit, "offset": offset}
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/scans/{scan_id}", response_model=dict)
async def get_scan(scan_id: int):
    try:
        scan = ImportTrackingRepository.get_scan(scan_id=scan_id)
        if not scan:
            raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found")
        return scan
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/scans/{scan_id}/files", response_model=dict)
async def get_scan_files(
    scan_id: int,
    limit: int = Query(200, ge=1, le=5000),
    offset: int = Query(0, ge=0),
):
    try:
        files = ImportTrackingRepository.list_scan_files(scan_id=scan_id, limit=limit, offset=offset)
        return {"data": files, "scan_id": scan_id, "limit": limit, "offset": offset}
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/runs", response_model=dict)
async def get_runs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    try:
        runs = ImportTrackingRepository.list_runs(limit=limit, offset=offset)
        return {"data": runs, "limit": limit, "offset": offset}
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")
