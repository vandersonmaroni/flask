# app/models/user.py
from pydantic import BaseModel

class LoginPayload(BaseModel):
    username: str
    password: str