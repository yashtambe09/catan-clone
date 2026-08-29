import os
from datetime import datetime, timedelta, timezone

import asyncpg
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/auth", tags=["auth"])

ph = PasswordHasher()

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 7


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str


class AuthError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def decode_access_token(token: str) -> dict:
    if not token or not isinstance(token, str):
        raise AuthError("missing_token", "no auth token provided")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise AuthError("token_expired", "your session has expired, log in again")
    except jwt.InvalidTokenError:
        raise AuthError("invalid_token", "invalid auth token")

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise AuthError("invalid_token", "invalid auth token")

    username = payload.get("username")
    if not isinstance(username, str) or not username:
        raise AuthError("invalid_token", "invalid auth token")

    return {"user_id": user_id, "username": username}


async def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing or malformed Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return decode_access_token(token)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=exc.message)


def create_access_token(user_id: int, username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(body: SignupRequest, request: Request):
    pool: asyncpg.Pool = request.app.state.db_pool
    password_hash = ph.hash(body.password)
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                "INSERT INTO users (username, password_hash) VALUES ($1, $2) "
                "RETURNING id, username",
                body.username,
                password_hash,
            )
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=409, detail="Username already taken")
    token = create_access_token(row["id"], row["username"])
    return TokenResponse(access_token=token, user_id=row["id"], username=row["username"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request):
    pool: asyncpg.Pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, username, password_hash FROM users WHERE username = $1",
            body.username,
        )
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    try:
        ph.verify(row["password_hash"], body.password)
    except VerifyMismatchError:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(row["id"], row["username"])
    return TokenResponse(access_token=token, user_id=row["id"], username=row["username"])
