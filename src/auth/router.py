from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.base_config import current_user
from src.auth.models import User, user
from src.database import get_async_session

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.get("/get-current-user")
async def get_user(c_user: User = Depends(current_user)):
    try:
        return {
            "status": "200",
            "data": c_user,
            "details": None
        }
    except Exception:
        # Передать ошибку разработчикам
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": None
        })


@router.get("/get-all-users")
async def get_users(session: AsyncSession = Depends(get_async_session)):
    try:
        query = select(user)
        result = await session.execute(query)
        users = result.mappings().all()
        users.sort(key=lambda x: x.points, reverse=True)
        return {
            "status": "200",
            "data": users,
            "details": None
        }
    except Exception:
        # Передать ошибку разработчикам
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": None
        })


@router.get("/get-rating-user")
async def get_rate(c_user: User = Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    try:
        list_of_users = (await get_users(session))["data"]
        position = next(index for index, item in enumerate(list_of_users) if item['id'] == c_user.id)
        return {
            "status": "200",
            "data": position+1,
            "details": None
        }
    except Exception:
        # Передать ошибку разработчикам
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": None
        })
