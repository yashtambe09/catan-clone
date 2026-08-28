import socketio
from fastapi import FastAPI

fastapi_app = FastAPI(title="Catan Clone API")


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
