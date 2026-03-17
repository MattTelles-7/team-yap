from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import sqlite3

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from .config import Settings, load_settings
from .db import get_connection, init_db
from .security import hash_token, issue_token, verify_password


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def utc_iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=256)


class UserResponse(BaseModel):
    id: int
    username: str
    display_name: str
    is_admin: bool


class LoginResponse(BaseModel):
    token: str
    user: UserResponse


class MessageResponse(BaseModel):
    id: int
    body: str
    created_at: str
    author_username: str
    author_display_name: str


class CreateMessageRequest(BaseModel):
    body: str = Field(min_length=1, max_length=1000)


@dataclass
class CurrentUser:
    id: int
    username: str
    display_name: str
    is_admin: bool
    token_hash: str


def row_to_user(row: sqlite3.Row) -> UserResponse:
    return UserResponse(
        id=row["id"],
        username=row["username"],
        display_name=row["display_name"],
        is_admin=bool(row["is_admin"]),
    )


def row_to_message(row: sqlite3.Row) -> MessageResponse:
    return MessageResponse(
        id=row["id"],
        body=row["body"],
        created_at=row["created_at"],
        author_username=row["author_username"],
        author_display_name=row["author_display_name"],
    )


def get_settings() -> Settings:
    return load_settings()


def get_db(settings: Settings = Depends(get_settings)):
    connection = get_connection(settings)
    try:
        yield connection
    finally:
        connection.close()


security = HTTPBearer(auto_error=False)


def delete_expired_sessions(connection: sqlite3.Connection) -> None:
    connection.execute("DELETE FROM sessions WHERE expires_at <= ?", (utc_iso(now_utc()),))
    connection.commit()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    connection: sqlite3.Connection = Depends(get_db),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )

    delete_expired_sessions(connection)
    row = connection.execute(
        """
        SELECT
          users.id,
          users.username,
          users.display_name,
          users.is_admin,
          sessions.token_hash
        FROM sessions
        JOIN users ON users.id = sessions.user_id
        WHERE sessions.token_hash = ?
        """,
        (hash_token(credentials.credentials),),
    ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session is invalid or has expired.",
        )

    return CurrentUser(
        id=row["id"],
        username=row["username"],
        display_name=row["display_name"],
        is_admin=bool(row["is_admin"]),
        token_hash=row["token_hash"],
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db(load_settings())
    yield


app = FastAPI(title="Team Yap Server", lifespan=lifespan)

if load_settings().allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(load_settings().allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )


@app.get("/healthz")
def healthz(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    with get_connection(settings) as connection:
        connection.execute("SELECT 1;").fetchone()
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    connection: sqlite3.Connection = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    username = payload.username.strip()
    row = connection.execute(
        """
        SELECT id, username, display_name, password_hash, is_admin
        FROM users
        WHERE username = ?
        """,
        (username,),
    ).fetchone()

    if row is None or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    delete_expired_sessions(connection)
    token = issue_token()
    expires_at = now_utc() + timedelta(hours=settings.session_ttl_hours)
    connection.execute(
        """
        INSERT INTO sessions (token_hash, user_id, created_at, expires_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            hash_token(token),
            row["id"],
            utc_iso(now_utc()),
            utc_iso(expires_at),
        ),
    )
    connection.commit()

    return LoginResponse(token=token, user=row_to_user(row))


@app.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    user: CurrentUser = Depends(get_current_user),
    connection: sqlite3.Connection = Depends(get_db),
) -> None:
    connection.execute("DELETE FROM sessions WHERE token_hash = ?", (user.token_hash,))
    connection.commit()


@app.get("/api/auth/me", response_model=UserResponse)
def me(user: CurrentUser = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        is_admin=user.is_admin,
    )


@app.get("/api/messages", response_model=list[MessageResponse])
def list_messages(
    _: CurrentUser = Depends(get_current_user),
    connection: sqlite3.Connection = Depends(get_db),
) -> list[MessageResponse]:
    rows = connection.execute(
        """
        SELECT
          messages.id,
          messages.body,
          messages.created_at,
          users.username AS author_username,
          users.display_name AS author_display_name
        FROM messages
        JOIN users ON users.id = messages.user_id
        ORDER BY messages.created_at DESC
        LIMIT 100
        """
    ).fetchall()
    return [row_to_message(row) for row in rows]


@app.post("/api/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(
    payload: CreateMessageRequest,
    user: CurrentUser = Depends(get_current_user),
    connection: sqlite3.Connection = Depends(get_db),
) -> MessageResponse:
    body = payload.body.strip()
    if not body:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Messages cannot be empty.",
        )

    created_at = utc_iso(now_utc())
    cursor = connection.execute(
        """
        INSERT INTO messages (user_id, body, created_at)
        VALUES (?, ?, ?)
        """,
        (user.id, body, created_at),
    )
    connection.commit()

    row = connection.execute(
        """
        SELECT
          messages.id,
          messages.body,
          messages.created_at,
          users.username AS author_username,
          users.display_name AS author_display_name
        FROM messages
        JOIN users ON users.id = messages.user_id
        WHERE messages.id = ?
        """,
        (cursor.lastrowid,),
    ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The message was stored but could not be loaded back.",
        )

    return row_to_message(row)
