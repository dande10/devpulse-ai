import secrets

from fastapi import Header, HTTPException

from app.core.config import settings


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    """Dependency for every /api/admin/* route.

    Fails closed: if ADMIN_TOKEN isn't configured, every admin request is
    rejected rather than silently allowed through.
    """
    if not settings.admin_token or not x_admin_token or not secrets.compare_digest(x_admin_token, settings.admin_token):
        raise HTTPException(status_code=401, detail="Missing or invalid admin token")
