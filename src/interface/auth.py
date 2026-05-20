from __future__ import annotations

import os
import base64
import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials

from .config import settings

logger = logging.getLogger("cmplx.gateway.auth")

basic_scheme = HTTPBasic(auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


async def verify_auth(
    request: Request,
    basic: Optional[HTTPBasicCredentials] = Depends(basic_scheme),
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> str:
    if settings.auth_disabled:
        return "anonymous"

    api_key_header = request.headers.get("X-API-Key", "")
    api_key_query = request.query_params.get("api_key", "")

    if api_key_header and settings.api_key and api_key_header == settings.api_key:
        return "api-user"
    if api_key_query and settings.api_key and api_key_query == settings.api_key:
        return "api-user"

    if basic and basic.username == settings.opencode_username and basic.password == settings.opencode_password:
        return basic.username

    if bearer and settings.api_key and bearer.credentials == settings.api_key:
        return "bearer-user"

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Provide Basic auth, X-API-Key header, api_key query param, or Bearer token.",
        headers={"WWW-Authenticate": "Basic"},
    )
