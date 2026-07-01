import os
from functools import lru_cache

from fastapi import Header, HTTPException, status
from pydantic import BaseModel


class SecuritySettings(BaseModel):
    write_api_key: str | None = None


@lru_cache(maxsize=1)
def get_security_settings() -> SecuritySettings:
    return SecuritySettings(write_api_key=os.getenv("SENTINEL_WRITE_API_KEY"))


def require_write_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    settings = get_security_settings()
    if not settings.write_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Write operations are disabled because SENTINEL_WRITE_API_KEY is not configured",
        )

    if x_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )

    if x_api_key != settings.write_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
