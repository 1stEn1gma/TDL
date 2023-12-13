import datetime
import json

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select, insert, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.base_config import current_user
from src.auth.models import User
from src.database import get_async_session
from src.tasks.models import tasks
from src.tasks.schemas import TaskCreate
from redis import asyncio as aioredis

from src.tasks.usefull_moduls import datetime_serializer, timing_decorator, get_all_task

r = aioredis.from_url("redis://localhost", encoding="utf8", decode_responses=True)

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)


@router.get("/")
async def get_tasks(user: User = Depends(current_user), tasks_title: str = "all", session: AsyncSession = Depends(get_async_session)):
    tasks_title = tasks_title.lower()
    print(f"get by:{tasks_title}")
    # try:

    all_tasks = await get_all_task(user.id, session)
    res = [d for d in all_tasks if d["title"] == tasks_title] if tasks_title != "all" else all_tasks
    rel = []

    tod = datetime.date.today()
    for i in all_tasks:
        if (tod < i['do_before'] and not i['on_this_day']) or (tod == i['do_before'] and i['on_this_day']):
            rel.append(i)
    return {
        "status": "200",
        "data":
            {
                "relevant": rel,
                "current": res
            },
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

        await r.delete(str(user.id) + "_get_all_task")

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

        await r.delete(str(user.id) + "_get_all_task")

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

        await r.delete(str(user.id) + "_get_all_task")

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

        await r.delete(str(user.id) + "_get_all_task")

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

        await r.delete(str(user.id) + "_get_all_task")

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

