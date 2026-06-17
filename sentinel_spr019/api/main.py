from fastapi import FastAPI
from sentinel_spr019.api.routes.economy_items import router as items_router
from sentinel_spr019.api.routes.economy_events import router as events_router

app = FastAPI(title="DayZ Sentinel")

app.include_router(items_router)
app.include_router(events_router)

@app.get("/api/v1/health")
def health():
    return {"status":"ok"}
