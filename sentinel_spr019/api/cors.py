"""CORS configuration driven by the environment.

Browser clients need an explicit allow-list. The API stays closed by default:
with `SENTINEL_CORS_ORIGINS` unset, no CORS middleware is installed at all, so
this change cannot loosen an existing deployment.
"""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

LOGGER = logging.getLogger(__name__)

ORIGINS_ENV_VAR = "SENTINEL_CORS_ORIGINS"

# Only the methods the API actually serves.
_ALLOWED_METHODS = ("GET", "POST", "OPTIONS")
# X-API-Key is required for the write endpoint; Content-Type for ordinary requests.
_ALLOWED_HEADERS = ("Content-Type", "X-API-Key")


def parse_origins(raw: str | None) -> list[str]:
    """Parse a comma-separated origin list, dropping blanks and duplicates."""
    if not raw:
        return []

    origins: list[str] = []
    for candidate in raw.split(","):
        origin = candidate.strip().rstrip("/")
        if origin and origin not in origins:
            origins.append(origin)
    return origins


def configure_cors(app: FastAPI) -> list[str]:
    """Install the CORS middleware if origins are configured; return the list used."""
    origins = parse_origins(os.getenv(ORIGINS_ENV_VAR))

    if not origins:
        LOGGER.debug("%s is not set; CORS middleware not installed", ORIGINS_ENV_VAR)
        return []

    if "*" in origins:
        # A wildcard together with credentials is rejected by browsers, and
        # silently allowing every origin is not something to infer from config.
        raise RuntimeError(
            f"{ORIGINS_ENV_VAR} must list explicit origins; "
            "'*' is not accepted. Example: "
            "SENTINEL_CORS_ORIGINS=http://localhost:5173,https://dashboard.example.com"
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=list(_ALLOWED_METHODS),
        allow_headers=list(_ALLOWED_HEADERS),
    )
    LOGGER.info("CORS enabled for origins: %s", ", ".join(origins))
    return origins
