from fastapi import Header, HTTPException

from .config import settings


def verify_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    x_user_id: str | None = Header(default=None, alias="X-User-ID"),
) -> str:
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include header: X-API-Key",
        )

    if x_api_key != settings.agent_api_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key",
        )

    return x_user_id or "default-user"
