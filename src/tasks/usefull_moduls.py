import json
import time
from datetime import datetime, date
from redis import asyncio as aioredis
from sqlalchemy import select, update

from src.auth.models import user
from src.tasks.models import tasks

r = aioredis.from_url("redis://localhost", encoding="utf8", decode_responses=True)


def datetime_serializer(obj):
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError("Type not serializable")


def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Функция {func.__name__} выполнилась за {execution_time:.4f} секунд")
        return result
    return wrapper


async def get_all_task(user, session):
    # caching part
    key = str(user.id) + "_get_all_task"
    cached_result = await r.get(key)
    if cached_result:
        ret = json.loads(cached_result)

        for i in ret:
            i['do_before'] = datetime.strptime(i['do_before'], "%Y-%m-%d").date()
        return ret

    # func
    query = (select(tasks).
             where(tasks.c.user_id == user.id))
    result = await session.execute(query)
    my_tasks = result.mappings().all()

    list_of_dicts = [dict(row) for row in my_tasks]
    for i in list_of_dicts:
        i['do_before'] = i['do_before'].date()
    serialized_data = json.dumps(list_of_dicts, default=datetime_serializer)

    # check expired task
    today = date.today()

    for task in list_of_dicts:
        if today > task['do_before'] and not task['title'] == "expired":
            await set_expired_task(task, user, session)

    await r.setex(key, 300, serialized_data)
    return list_of_dicts


async def get_task_by_id(user_id, task_id, session):
    query = (select(tasks).
             where((tasks.c.user_id == user_id) & (tasks.c.id == task_id)))
    result = await session.execute(query)
    my_tasks = result.mappings().all()
    return my_tasks[0]


def choose_needed_tasks_from_all(all_tasks, tasks_title):
    res = []
    for task in all_tasks:
        if tasks_title != "all":
            if task["title"] == tasks_title:
                res.append(task)
        else:
            if task["title"] != "deleted" and task["title"] != "expired":
                res.append(task)
    res.sort(key=lambda x: x['created_at'])
    return res


def choose_relevant_tasks_from_all(all_tasks):
    rel = []

    tod = date.today()

    for task in all_tasks:
        do_before = tod < task['do_before'] and not task['on_this_day']
        do_in_this_day = tod == task['do_before'] and task['on_this_day']
        deleted = task["title"] == "deleted"
        expired = task["title"] == "expired"
        if (do_before or do_in_this_day) and not (deleted or expired):
            rel.append(task)
    rel.sort(key=lambda x: x['created_at'])
    return rel


async def set_expired_task(task, c_user, session):
    task['title'] = "expired"
    query = update(tasks). \
        where((tasks.c.user_id == task['user_id']) & (tasks.c.id == task['id'])). \
        values(title="expired")
    await session.execute(query)
    await session.commit()

    if c_user.points-5 > 0:
        stmt = update(user). \
            where(user.c.id == c_user.id). \
            values(points=c_user.points-5)
    else:
        stmt = update(user). \
            where(user.c.id == c_user.id). \
            values(points=0)
    await session.execute(stmt)
    await session.commit()

    await r.delete(str(c_user.id) + "_get_all_task")


async def add_points(c_user, task, session):
    key = str(c_user.id) + "_points"
    cashed_points = await r.get(key)
    if cashed_points:
        if int(cashed_points) < 100:
            if task["on_this_day"]:
                plus = 10
                temp = int(cashed_points) + plus
                if temp > 100:
                    temp = 100
                await r.setex(key, 86400, temp)
                await change_points_in_db(c_user, plus, session)
                return
            else:
                a = (task["do_before"].date() - task["created_at"].date()).days
                b = (date.today() - task["created_at"].date()).days
                plus = 5 + 5 * (1 - b / a)

                temp = int(cashed_points) + plus
                if temp > 100:
                    temp = 100
                await r.setex(key, 86400, temp)
                await change_points_in_db(c_user, plus, session)
                return
    if task["on_this_day"]:
        plus = 10
        temp = plus
        await r.setex(key, 86400, temp)
        await change_points_in_db(c_user, plus, session)
        return
    else:
        a = (task["do_before"].date() - task["created_at"].date()).days
        b = (date.today() - task["created_at"].date()).days
        plus = 5 + 5 * (1 - b / a)

        temp = plus
        await r.setex(key, 86400, temp)
        await change_points_in_db(c_user, plus, session)
        return


async def change_points_in_db(c_user, plus, session):
    points = c_user.points + plus
    stmt = update(user). \
        where(user.c.id == c_user.id). \
        values(points=points)
    await session.execute(stmt)
    await session.commit()
