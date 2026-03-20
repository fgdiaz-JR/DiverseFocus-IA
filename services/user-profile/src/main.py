"""
User Profile service for DiverseFocus-IA.

Manages user accounts, preferences, and task history using SQLite via SQLAlchemy async.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from sqlalchemy import Column, DateTime, Integer, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data/users.db"

    class Config:
        env_file = ".env"


settings = Settings()

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

app = FastAPI(
    title="DiverseFocus-IA User Profile Service",
    description="User profile and task history management",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# ORM Models
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(128), unique=True, index=True, nullable=False)
    username = Column(String(128), nullable=False)
    email = Column(String(256), nullable=True)
    preferences_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(128), index=True, nullable=False)
    task_type = Column(String(64), nullable=False)
    content = Column(Text, nullable=False)
    result = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Startup: create tables
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def on_startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified.")


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class UserProfileResponse(BaseModel):
    user_id: str
    username: str
    email: str | None
    preferences: dict[str, Any]
    created_at: str


class UpdateProfileRequest(BaseModel):
    username: str | None = None
    email: str | None = None
    preferences: dict[str, Any] | None = None


class CreateTaskRequest(BaseModel):
    user_id: str
    task_type: str
    content: str
    result: str | None = None


class TaskResponse(BaseModel):
    id: int
    user_id: str
    task_type: str
    content: str
    result: str | None
    created_at: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user_to_response(user: UserModel) -> UserProfileResponse:
    prefs: dict[str, Any] = {}
    try:
        prefs = json.loads(user.preferences_json or "{}")
    except json.JSONDecodeError:
        pass
    return UserProfileResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        preferences=prefs,
        created_at=user.created_at.isoformat() if user.created_at else "",
    )


def _task_to_response(task: TaskModel) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        task_type=task.task_type,
        content=task.content,
        result=task.result,
        created_at=task.created_at.isoformat() if task.created_at else "",
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": "user-profile"}


@app.get("/profile/{user_id}", response_model=UserProfileResponse, tags=["Profile"])
async def get_profile(user_id: str) -> UserProfileResponse:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.user_id == user_id)
        )
        user = result.scalar_one_or_none()

    if user is None:
        # Auto-create a profile on first access
        new_user = UserModel(
            user_id=user_id,
            username=user_id,
            preferences_json="{}",
        )
        async with AsyncSessionLocal() as session:
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
        return _user_to_response(new_user)

    return _user_to_response(user)


@app.put("/profile/{user_id}", response_model=UserProfileResponse, tags=["Profile"])
async def update_profile(user_id: str, body: UpdateProfileRequest) -> UserProfileResponse:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            user = UserModel(
                user_id=user_id,
                username=body.username or user_id,
                preferences_json="{}",
            )
            session.add(user)

        if body.username is not None:
            user.username = body.username
        if body.email is not None:
            user.email = body.email
        if body.preferences is not None:
            existing: dict[str, Any] = {}
            try:
                existing = json.loads(user.preferences_json or "{}")
            except json.JSONDecodeError:
                pass
            existing.update(body.preferences)
            user.preferences_json = json.dumps(existing)

        await session.commit()
        await session.refresh(user)
        return _user_to_response(user)


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["Tasks"])
async def create_task(body: CreateTaskRequest) -> TaskResponse:
    task = TaskModel(
        user_id=body.user_id,
        task_type=body.task_type,
        content=body.content,
        result=body.result,
    )
    async with AsyncSessionLocal() as session:
        session.add(task)
        await session.commit()
        await session.refresh(task)
    return _task_to_response(task)


@app.get("/tasks/{user_id}", response_model=list[TaskResponse], tags=["Tasks"])
async def get_tasks(user_id: str, limit: int = 50) -> list[TaskResponse]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(TaskModel)
            .where(TaskModel.user_id == user_id)
            .order_by(TaskModel.created_at.desc())
            .limit(limit)
        )
        tasks = result.scalars().all()
    return [_task_to_response(t) for t in tasks]
