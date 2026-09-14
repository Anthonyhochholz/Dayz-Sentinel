import logging

from fastapi import APIRouter, HTTPException, Query
from starlette.concurrency import run_in_threadpool

from sentinel_spr019.api.models.import_tracking import (
    ImportRunListResponse,
    MirrorScan,
    MirrorScanFileListResponse,
    MirrorScanListResponse,
)
from sentinel_spr019.persistence.import_tracking_repository import ImportTrackingRepository

LOGGER = logging.getLogger(__name__)


router = APIRouter(prefix="/api/v1/import-tracking", tags=["import-tracking"])


@router.get("/scans", response_model=MirrorScanListResponse)
async def get_scans(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    try:
        scans = await run_in_threadpool(ImportTrackingRepository.list_scans, limit, offset)
        return {"data": scans, "limit": limit, "offset": offset}
    except Exception:
        LOGGER.exception("Error in get_scans")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/scans/{scan_id}", response_model=MirrorScan)
async def get_scan(scan_id: int):
    try:
        scan = await run_in_threadpool(ImportTrackingRepository.get_scan, scan_id)
        if not scan:
            raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found")
        return scan
    except HTTPException:
        raise
    except Exception:
        LOGGER.exception("Error in get_scan: %s", scan_id)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/scans/{scan_id}/files", response_model=MirrorScanFileListResponse)
async def get_scan_files(
    scan_id: int,
    limit: int = Query(200, ge=1, le=5000),
    offset: int = Query(0, ge=0),
):
    try:
        files = await run_in_threadpool(ImportTrackingRepository.list_scan_files, scan_id, limit, offset)
        return {"data": files, "scan_id": scan_id, "limit": limit, "offset": offset}
    except Exception:
        LOGGER.exception("Error in get_scan_files: %s", scan_id)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/runs", response_model=ImportRunListResponse)
async def get_runs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    try:
        runs = await run_in_threadpool(ImportTrackingRepository.list_runs, limit, offset)
        return {"data": runs, "limit": limit, "offset": offset}
    except Exception:
        LOGGER.exception("Error in get_runs")
        raise HTTPException(status_code=500, detail="Internal server error")
