from pydantic import BaseModel


class AccessTokenPayload(BaseModel):
    exp: int
