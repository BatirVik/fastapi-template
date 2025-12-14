from typing import Annotated
from fastapi import Depends, HTTPException

from app.auth.schemas import AccessTokenPayload
from app.auth.security import validate_token


def get_me_or_none() -> AccessTokenPayload | None:
    token = None
    me = validate_token(token, AccessTokenPayload)
    return me


def get_me():
    me = get_me_or_none()
    if me is None:
        raise HTTPException(401, "Not authenticated", {"WWW-Authenticate": "Bearer"})
    return me


Me = Annotated[AccessTokenPayload, Depends(get_me)]
