from contextlib import asynccontextmanager

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import router as auth_router
from app.board_api import router as board_router
from app.db import create_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_pool = await create_pool()
    yield
    await app.state.db_pool.close()


fastapi_app = FastAPI(title="Catan Clone API", lifespan=lifespan)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fastapi_app.include_router(auth_router)
fastapi_app.include_router(board_router)


@fastapi_app.get("/health")
async def health():
    return {"status": "ok"}


sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


@sio.event
async def connect(sid, environ):
    print(f"client connected: {sid}")


@sio.event
async def disconnect(sid):
    print(f"client disconnected: {sid}")


app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
