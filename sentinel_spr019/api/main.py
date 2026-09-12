from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from sentinel_spr019.api.cors import configure_cors
from sentinel_spr019.api.models.common import HealthResponse
from sentinel_spr019.api.routes.economy_events import router as events_router
from sentinel_spr019.api.routes.economy_items import router as items_router
from sentinel_spr019.api.routes.import_tracking import router as import_tracking_router

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def create_app() -> FastAPI:
    """Build the FastAPI application.

    Configuration is read while the app is built, so tests can construct an
    app under a different environment instead of depending on import order.
    """
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

    application = FastAPI(
        title="DayZ Sentinel",
        description="REST API and import pipeline for DayZ economy and ADM log data.",
    )

    configure_cors(application)

    application.include_router(items_router)
    application.include_router(events_router)
    application.include_router(import_tracking_router)

    @application.get("/api/v1/health", response_model=HealthResponse, tags=["health"])
    def health():
        """Liveness probe."""
        return {"status": "ok"}

    return application


# The ASGI entry point referenced by the Dockerfile, docker-compose and README:
# `uvicorn sentinel_spr019.api.main:app`.
app = create_app()
