from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.auth import PermissionOut, RoleOut, UserOut


class UserCreateRequest(BaseModel):
    username: str
    password: str
    is_active: bool = True
    is_superuser: bool = False
    role_ids: list[int] = []


class UserUpdateRequest(BaseModel):
    password: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    role_ids: list[int] | None = None


class RoleCreateRequest(BaseModel):
    name: str
    description: str = ""
    permission_ids: list[int] = []


class RoleUpdateRequest(BaseModel):
    description: str | None = None
    permission_ids: list[int] | None = None


class UserListResponse(BaseModel):
    items: list[UserOut]
    total: int


class RoleListResponse(BaseModel):
    items: list[RoleOut]
    total: int


class PermissionListResponse(BaseModel):
    items: list[PermissionOut]
    total: int
