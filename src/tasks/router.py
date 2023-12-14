from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import insert, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.base_config import current_user
from src.auth.models import User
from src.database import get_async_session
from src.tasks.custom_task_error import ExpiredError
from src.tasks.models import tasks
from src.tasks.schemas import TaskCreate, ResponseForGetTasks
from redis import asyncio as aioredis

from src.tasks.usefull_moduls import get_all_task, choose_needed_tasks_from_all, choose_relevant_tasks_from_all, \
    get_task_by_id, add_points

r = aioredis.from_url("redis://localhost", encoding="utf8", decode_responses=True)

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)


@router.get("/", response_model=ResponseForGetTasks)
async def get_tasks(user: User = Depends(current_user),
                    tasks_title: str = "all",
                    session: AsyncSession = Depends(get_async_session)):
    tasks_title = tasks_title.lower()
    print(f"get by:{tasks_title}")
    try:
        all_tasks = await get_all_task(user, session)
        res = choose_needed_tasks_from_all(all_tasks, tasks_title)
        rel = choose_relevant_tasks_from_all(all_tasks)

        return {
            "status": "200",
            "data":
                {
                    "relevant": rel,
                    "current": res
                },
            "details": None
        }
    except Exception:
        # Передать ошибку разработчикам
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": None
        })


@router.post("/", response_model=ResponseForGetTasks)
async def add_task(new_operation: TaskCreate,
                   tasks_title: str = "all",
                   user: User = Depends(current_user),
                   session: AsyncSession = Depends(get_async_session)):
    try:
        tasks_title = tasks_title.lower()
        stmt = (insert(tasks).
                values(**new_operation.model_dump(), user_id=user.id))
        await session.execute(stmt)
        await session.commit()

        await r.delete(str(user.id) + "_get_all_task")
        all_tasks = await get_all_task(user, session)
        res = choose_needed_tasks_from_all(all_tasks, tasks_title)
        rel = choose_relevant_tasks_from_all(all_tasks)

        return {
            "status": "200",
            "data":
                {
                    "relevant": rel,
                    "current": res
                },
            "details": None
        }
    except Exception:
        # Передать ошибку разработчикам
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": None
        })


@router.post("/{task_id}/edit", response_model=ResponseForGetTasks)
async def edit_task(task_id: int, new_operation: TaskCreate,
                    tasks_title: str = "all",
                    user: User = Depends(current_user),
                    session: AsyncSession = Depends(get_async_session)
                    ):
    try:
        tasks_title = tasks_title.lower()
        query = (update(tasks).
                 where((tasks.c.user_id == user.id) & (tasks.c.id == task_id)).
                 values(**new_operation.model_dump(), user_id=user.id))
        await session.execute(query)
        await session.commit()

        await r.delete(str(user.id) + "_get_all_task")
        all_tasks = await get_all_task(user, session)
        res = choose_needed_tasks_from_all(all_tasks, tasks_title)
        rel = choose_relevant_tasks_from_all(all_tasks)

        return {
            "status": "200",
            "data":
                {
                    "relevant": rel,
                    "current": res
                },
            "details": None
        }
    except Exception:
        # Передать ошибку разработчикам
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": None
        })


@router.post("/{task_id}/delete", response_model=ResponseForGetTasks)
async def delete_task(task_id: int,
                      tasks_title: str = "all",
                      user: User = Depends(current_user),
                      session: AsyncSession = Depends(get_async_session)):
    try:
        tasks_title = tasks_title.lower()
        stmt = (delete(tasks).
                where((tasks.c.id == task_id) & (tasks.c.user_id == user.id)))
        await session.execute(stmt)
        await session.commit()

        await r.delete(str(user.id) + "_get_all_task")
        all_tasks = await get_all_task(user, session)
        res = choose_needed_tasks_from_all(all_tasks, tasks_title)
        rel = choose_relevant_tasks_from_all(all_tasks)

        return {
            "status": "200",
            "data":
                {
                    "relevant": rel,
                    "current": res
                },
            "details": None
        }
    except Exception:
        # Передать ошибку разработчикам
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": None
        })


@router.post("/{task_id}/complete", response_model=ResponseForGetTasks)
async def complete_task(task_id: int,
                        tasks_title: str = "all",
                        user: User = Depends(current_user),
                        session: AsyncSession = Depends(get_async_session)):
    try:
        tasks_title = tasks_title.lower()
        task = await get_task_by_id(user.id, task_id, session)
        if task["title"] == "expired":
            raise HTTPException(status_code=399, detail={"status": "399",
                                                         "data": "Expired",
                                                         "details": None
                                                         }
                                )
        stmt = (update(tasks).
                where((tasks.c.user_id == user.id) & (tasks.c.id == task_id)).
                values(title="completed"))
        await session.execute(stmt)
        await session.commit()

        # logic for points
        await add_points(user, task, session)

        await r.delete(str(user.id) + "_get_all_task")
        all_tasks = await get_all_task(user, session)
        res = choose_needed_tasks_from_all(all_tasks, tasks_title)
        rel = choose_relevant_tasks_from_all(all_tasks)

        return {
            "status": "200",
            "data":
                {
                    "relevant": rel,
                    "current": res
                },
            "details": None
        }
    except Exception:
        # Передать ошибку разработчикам
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": None
        })


@router.post("/{task_id}/add_to_trash", response_model=ResponseForGetTasks)
async def add_to_trash_task(task_id: int,
                            tasks_title: str = "all",
                            user: User = Depends(current_user),
                            session: AsyncSession = Depends(get_async_session)):
    try:
        tasks_title = tasks_title.lower()
        stmt = (update(tasks).
                where((tasks.c.user_id == user.id) & (tasks.c.id == task_id)).
                values(title="deleted"))
        await session.execute(stmt)
        await session.commit()

        await r.delete(str(user.id) + "_get_all_task")
        all_tasks = await get_all_task(user, session)
        res = choose_needed_tasks_from_all(all_tasks, tasks_title)
        rel = choose_relevant_tasks_from_all(all_tasks)

        return {
            "status": "200",
            "data":
                {
                    "relevant": rel,
                    "current": res
                },
            "details": None
        }
    except Exception:
        # Передать ошибку разработчикам
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "data": None,
            "details": None
        })
