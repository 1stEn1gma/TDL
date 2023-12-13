from typing import Optional, Annotated

from fastapi import Query
from fastapi_users import schemas


class UserRead(schemas.BaseUser[int]):
    id: int
    # email: str
    email: Annotated[str, Query(min_length=5,
                                pattern="[\w\.-]+@[\w\.-]+(\.[\w]+)+")]
    username: str
    points: float
    role_id: int
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False

    class Config:
        from_attributes = True  # orm_mode = True


class UserCreate(schemas.BaseUserCreate):
    username: str
    email: Annotated[str, Query(min_length=5,
                                pattern="[\w\.-]+@[\w\.-]+(\.[\w]+)+")]
    password: str
    role_id: int
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False
