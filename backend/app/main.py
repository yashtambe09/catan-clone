from contextlib import asynccontextmanager
from functools import wraps

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import router as auth_router
from app.db import create_pool
from app.game.placement import GameError
from app.rooms import RoomError, RoomManager


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


@fastapi_app.get("/health")
async def health():
    return {"status": "ok"}


sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
room_manager = RoomManager()


def room_handler(fn):
    @wraps(fn)
    async def wrapper(sid, *args, **kwargs):
        try:
            return await fn(sid, *args, **kwargs)
        except (RoomError, GameError) as exc:
            return {"error": exc.code, "message": exc.message}
        except Exception:
            return {"error": "server_error", "message": "something went wrong"}

    return wrapper


@sio.event
async def connect(sid, environ):
    print(f"client connected: {sid}")


@sio.event
async def disconnect(sid):
    print(f"client disconnected: {sid}")
    room = room_manager.remove_player(sid)
    if room is not None:
        await sio.emit("room_updated", room.to_dict(), room=room.code)


@sio.event
@room_handler
async def create_room(sid, data):
    room = room_manager.create_room(sid, data.get("name"), data.get("player_count"))
    await sio.enter_room(sid, room.code)
    return {"room": room.to_dict()}


@sio.event
@room_handler
async def join_room(sid, data):
    room = room_manager.join_room(sid, data.get("code"), data.get("name"))
    await sio.enter_room(sid, room.code)
    await sio.emit("room_updated", room.to_dict(), room=room.code)
    return {"room": room.to_dict()}


@sio.event
@room_handler
async def start_game(sid, data):
    room = room_manager.start_game(sid)
    await sio.emit("game_started", room.to_dict(), room=room.code)
    return {"room": room.to_dict()}


@sio.event
@room_handler
async def game_action(sid, data):
    room = room_manager.game_action(sid, data.get("action"), data.get("payload"))
    await sio.emit("game_updated", room.to_dict(), room=room.code)
    return {"room": room.to_dict()}


app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
