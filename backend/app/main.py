import asyncio
import logging
from contextlib import asynccontextmanager
from functools import wraps

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from socketio.exceptions import ConnectionRefusedError

from app.auth import AuthError, decode_access_token
from app.auth import router as auth_router
from app.db import create_pool
from app.game.placement import GameError
from app.rooms import Room, RoomError, RoomManager
from app.stats import router as stats_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_pool = await create_pool()
    yield
    await app.state.db_pool.close()


fastapi_app = FastAPI(title="Catan Clone API", lifespan=lifespan)

fastapi_app.add_middleware(
    CORSMiddleware,
    # Matches http://localhost:5173 and http://<any LAN IPv4>:5173 so friends'
    # devices can reach this over LAN, not just the host machine itself, plus
    # the real deployed frontend origin.
    allow_origin_regex=r"http://(localhost|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):5173|https://catan\.mightycaptions\.in",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fastapi_app.include_router(auth_router)
fastapi_app.include_router(stats_router)


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


async def broadcast(room: Room, event: str):
    for p in room.players:
        if p.connected:
            await sio.emit(event, room.to_dict(viewer=p.name), to=p.sid)


async def persist_finished_game(room: Room):
    game = room.game
    try:
        scored = sorted(
            ((p, game.true_victory_points(p.name)) for p in room.players),
            key=lambda t: -t[1],
        )
        placements = []
        last_score, last_place = None, 0
        for i, (_, score) in enumerate(scored, start=1):
            if score != last_score:
                last_place, last_score = i, score
            placements.append(last_place)

        winner = next(p for p in room.players if p.name == game.winner)

        async with fastapi_app.state.db_pool.acquire() as conn:
            async with conn.transaction():
                game_id = await conn.fetchval(
                    "INSERT INTO games (started_at, ended_at, winner_id, player_count, board_size) "
                    "VALUES ($1, now(), $2, $3, $4) RETURNING id",
                    room.started_at,
                    winner.user_id,
                    len(room.players),
                    room.board.size.value,
                )
                await conn.executemany(
                    "INSERT INTO game_players (game_id, user_id, final_score, placement) "
                    "VALUES ($1, $2, $3, $4)",
                    [
                        (game_id, p.user_id, score, placement)
                        for (p, score), placement in zip(scored, placements)
                    ],
                )
    except Exception:
        logging.exception("failed to persist finished game %s", room.code)


def _maybe_persist(room: Room):
    if room.game is not None and room.game.winner is not None and not room.persisted:
        room.persisted = True
        asyncio.create_task(persist_finished_game(room))


@sio.event
async def connect(sid, environ, auth):
    try:
        identity = decode_access_token((auth or {}).get("token"))
    except AuthError as exc:
        raise ConnectionRefusedError(exc.message)
    room_manager.register_identity(sid, identity["user_id"], identity["username"])


@sio.event
async def disconnect(sid):
    room = room_manager.remove_player(sid)
    if room is not None:
        await broadcast(room, "room_updated")


@sio.event
@room_handler
async def create_room(sid, data):
    room = room_manager.create_room(sid, data.get("player_count"))
    await sio.enter_room(sid, room.code)
    return {"room": room.to_dict(viewer=room_manager.name_for_sid(sid))}


@sio.event
@room_handler
async def join_room(sid, data):
    room = room_manager.join_room(sid, data.get("code"))
    await sio.enter_room(sid, room.code)
    await broadcast(room, "room_updated")
    return {"room": room.to_dict(viewer=room_manager.name_for_sid(sid))}


@sio.event
@room_handler
async def start_game(sid, data):
    room = room_manager.start_game(sid)
    await broadcast(room, "game_started")
    return {"room": room.to_dict(viewer=room_manager.name_for_sid(sid))}


@sio.event
@room_handler
async def game_action(sid, data):
    room = room_manager.game_action(sid, data.get("action"), data.get("payload"))
    await broadcast(room, "game_updated")
    _maybe_persist(room)
    return {"room": room.to_dict(viewer=room_manager.name_for_sid(sid))}


app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
