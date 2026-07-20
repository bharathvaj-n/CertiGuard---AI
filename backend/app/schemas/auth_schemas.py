from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenUser(BaseModel):
    username: str
    is_admin: bool

class Token(BaseModel):
    access_token: str
    token_type: str
    user: TokenUser
