import hmac
import time
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException

from app.config import settings

TTL = 7 * 86400


def make_token(password: str) -> str:
    s = settings()
    if not s.app_password:
        raise HTTPException(503, "APP_PASSWORD non défini dans .env")
    if not hmac.compare_digest(password, s.app_password):
        raise HTTPException(401, "Mot de passe incorrect")
    return jwt.encode({"exp": int(time.time()) + TTL}, s.secret_key, algorithm="HS256")


def require_auth(authorization: Annotated[str | None, Header()] = None) -> None:
    s = settings()
    if not s.auth_enabled:
        return
    token = (authorization or "").removeprefix("Bearer ")
    try:
        jwt.decode(token, s.secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(401, "Non authentifié") from e


Auth = Depends(require_auth)
