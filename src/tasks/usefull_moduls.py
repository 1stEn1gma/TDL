import datetime
import json
import time
from datetime import datetime, date
from redis import asyncio as aioredis
from sqlalchemy import select

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


async def get_all_task(id, session):
    key = str(id) + "get_all_task"
    cached_result = await r.get(key)
    if cached_result:
        ret = json.loads(cached_result)

        for i in ret:
            i['do_before'] = datetime.strptime(i['do_before'], "%Y-%m-%d").date()
        return ret

    query = (select(tasks).
             where(tasks.c.user_id == id))
    result = await session.execute(query)
    my_tasks = result.mappings().all()

    list_of_dicts = [dict(row) for row in my_tasks]
    for i in list_of_dicts:
        i['do_before'] = i['do_before'].date()
    serialized_data = json.dumps(list_of_dicts, default=datetime_serializer)

    await r.setex(key, 300, serialized_data)
    return list_of_dicts
