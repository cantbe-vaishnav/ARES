from pydantic import BaseModel, Field
from typing import Literal


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    role: Literal["admin", "user"] = "user"


class RoleUpdate(BaseModel):
    role: Literal["admin", "user"]


class ChatCreate(BaseModel):
    title: str = "New Chat"


class ChatRename(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    selected_file_ids: list[int] = []
