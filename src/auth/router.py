from fastapi import APIRouter, Depends, HTTPException

from src.auth.base_config import current_user
from src.auth.models import User

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.get("/")
async def get_user(user: User = Depends(current_user)):
    try:
        return {
            "status": "200",
            "data": user,
            "details": None
        }
    except Exception:
        # Передать ошибку разработчикам
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": None
        })
