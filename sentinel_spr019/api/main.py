from pathlib import Path

from fastapi import FastAPI
from dotenv import load_dotenv
from sentinel_spr019.api.routes.economy_items import router as items_router
from sentinel_spr019.api.routes.economy_events import router as events_router
from sentinel_spr019.api.routes.import_tracking import router as import_tracking_router

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

app = FastAPI(title="DayZ Sentinel")

app.include_router(items_router)
app.include_router(events_router)
app.include_router(import_tracking_router)

@app.get("/api/v1/health")
def health():
    return {"status":"ok"}
