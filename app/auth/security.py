import jwt
from pydantic import BaseModel, ValidationError
import argon2
from app.config import get_config

config = get_config()
pw = argon2.PasswordHasher()


def encode_token(payload: BaseModel) -> str:
    return jwt.encode(  # pyright: ignore[reportUnknownMemberType]
        payload.model_dump(mode="json"), config.JWT_SECRET, algorithm="HS256"
    )


def validate_token[T: BaseModel](
    token: str | None, schema: type[T], *, verify_exp: bool = True
) -> T | None:
    """Returns the payload or None if the token is not valid or has expire."""
    if token is None:
        return None
    try:
        payload = jwt.decode(  # pyright: ignore[reportUnknownMemberType]
            token,
            config.JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": verify_exp},
        )
        return schema.model_validate(payload)
    except (jwt.InvalidTokenError, ValidationError):
        return None


def hash_password(password: str) -> bytes:
    return pw.hash(password).encode()


def verify_password(password: str, hashed_password: bytes) -> bool:
    return pw.verify(password, hashed_password)
