from fastapi import APIRouter, Depends, HTTPException
from fastapi_cache.decorator import cache
from sqlalchemy import select, insert, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.base_config import current_user
from src.auth.models import User
from src.database import get_async_session
from src.tasks.models import tasks
from src.tasks.schemas import TaskCreate

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)


# @router.get("/")
# async def get_tasks(user: User = Depends(current_user), session: AsyncSession = Depends(get_async_session)):
#     try:
#         query = select(tasks).where(tasks.c.user_id == user.id)
#         result = await session.execute(query)
#         return {
#             "status": "200",
#             "data": result.mappings().all(),
#             "details": None
#         }
#     except Exception:
#         # Передать ошибку разработчикам
#         raise HTTPException(status_code=500, detail={
#             "status": "error",
#             "data": None,
#             "details": None
#         })


@router.get("/")
async def get_tasks(user: User = Depends(current_user), tasks_title: str = "all", session: AsyncSession = Depends(get_async_session)):
    tasks_title = tasks_title.lower()
    print(tasks_title)
    # try:

    @cache(expire=30)
    async def get_all_task(id):
        query = (select(tasks).
                 where(tasks.c.user_id == id))
        result = await session.execute(query)
        my_tasks = result.mappings().all()
        return my_tasks

    my_tasks = await get_all_task(user.id)
    test = [dict(row) for row in my_tasks]
    res = [d for d in test if d["title"] == tasks_title] if tasks_title != "all" else test
    # print(type(test[0]))
    return {
        "status": "200",
        "data": res,
        "details": None
    }
    # except Exception:
    #     # Передать ошибку разработчикам
    #     raise HTTPException(status_code=500, detail={
    #         "status": "error",
    #         "data": None,
    #         "details": None
    #     })


@router.post("/")
async def add_task(new_operation: TaskCreate, user: User = Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    try:
        stmt = (insert(tasks).
                values(**new_operation.model_dump(), user_id=user.id))
        await session.execute(stmt)
        await session.commit()
        query = select(tasks).where(tasks.c.user_id == user.id)
        result = await session.execute(query)
        return {
                    "status": "200",
                    "data": result.mappings().all(),
                    "details": None
                }
    except Exception:
        # Передать ошибку разработчикам
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": None
        })


@router.post("/{task_id}/edit")
async def edit_task(task_id: int, new_operation: TaskCreate, user: User = Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    try:
        query = update(tasks).\
                where((tasks.c.user_id == user.id) & (tasks.c.id == task_id)).\
                values(**new_operation.model_dump(), user_id=user.id)
        await session.execute(query)
        await session.commit()
        query = select(tasks).where((tasks.c.user_id == user.id) & (tasks.c.id == task_id))
        result = await session.execute(query)
        return {
            "status": "200",
            "data": result.mappings().all(),
            "details": None
        }
    except Exception:
        # Передать ошибку разработчикам
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": None
        })


@router.post("/{task_id}/delete")
async def delete_task(task_id: int, user: User = Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    try:
        stmt = (delete(tasks).
                where((tasks.c.id == task_id) & (tasks.c.user_id == user.id)))
        await session.execute(stmt)
        await session.commit()
        query2 = (select(tasks).
                  where(tasks.c.user_id == user.id))
        result = await session.execute(query2)
        return {
            "status": "200",
            "data": result.mappings().all(),
            "detail": None
        }
    except Exception:
        # Передать ошибку разработчикам
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": None
        })


@router.post("/{task_id}/complete")
async def complete_task(task_id: int, user: User = Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    try:
        stmt = update(tasks). \
                where((tasks.c.user_id == user.id) & (tasks.c.id == task_id)). \
                values(title="completed")
        await session.execute(stmt)
        await session.commit()
        query2 = (select(tasks).
                  where(tasks.c.user_id == user.id))
        result = await session.execute(query2)
        return {
            "status": "200",
            "data": result.mappings().all(),
            "detail": None
        }
    except Exception:
        # Передать ошибку разработчикам
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": None
        })


@router.post("/{task_id}/add_to_trash")
async def add_to_trash_task(task_id: int, user: User = Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    try:
        stmt = update(tasks). \
                where((tasks.c.user_id == user.id) & (tasks.c.id == task_id)). \
                values(title="deleted")
        await session.execute(stmt)
        await session.commit()
        query2 = (select(tasks).
                  where(tasks.c.user_id == user.id))
        result = await session.execute(query2)
        return {
            "status": "200",
            "data": result.mappings().all(),
            "detail": None
        }
    except Exception:
        # Передать ошибку разработчикам
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": None
        })
