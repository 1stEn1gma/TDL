import time

import uvicorn

from fastapi import FastAPI, Depends
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.templating import Jinja2Templates

from src.auth.schemas import UserRead, UserCreate
from src.auth.base_config import fastapi_users, auth_backend, current_user
from src.auth.models import User
from src.tasks.router import router as router_tasks
from src.auth.router import router as get_user

from redis import asyncio as aioredis

app = FastAPI(
    title="TDL"
)
templates = Jinja2Templates(directory="static")


origins = [
    "http://26.132.166.28",
    "http://26.132.166.28:443",
    "http://26.132.166.28:5173",
    "http://26.132.166.28:3000",
    "http://26.132.166.28:3001",
    "http://localhost:8080",
    "http://26.81.52.203:8000",
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    'http://26.81.52.203:3000'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE", "PATCH", "PUT"],
    allow_headers=["Content-Type", "Set-Cookie", "Access-Control-Allow-Headers", "Access-Control-Allow-Origin",
                   "Authorization"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    # print(response.status_code)
    return response


app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)


app.include_router(get_user)


@app.get("/protected-route")
def protected_route(user: User = Depends(current_user)):
    return f"Hello, {user.username}"


@app.get("/unprotected-route")
def unprotected_route():
    return f"Hello, anonym"


app.include_router(router_tasks)


@app.on_event("startup")
async def startup_event():
    print("Server: Hello world!")


@app.on_event("shutdown")
async def startup_event():
    print("Server: Goodbye world!")


if __name__ == "__main__":
    uvicorn.run(app, host="26.81.52.203", port=8000, log_level="info")
