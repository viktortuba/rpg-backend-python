import uuid
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from jose import jwt
from app.database import Base, get_db
from app.main import app
from app.models.class_ import CharacterClass
from app.config import settings

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def make_token(role: str = "User", user_id: str = None) -> str:
    from datetime import datetime, timedelta, timezone
    uid = user_id or str(uuid.uuid4())
    payload = {
        "sub": uid,
        "username": f"user_{uid[:8]}",
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256"), uid


@pytest_asyncio.fixture(scope="function")
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock()
    mock_redis.delete = AsyncMock()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.state.redis = mock_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac, mock_redis, db_session

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def seeded_class(db_session: AsyncSession):
    cls = CharacterClass(name="Warrior", description="A fighter.")
    db_session.add(cls)
    await db_session.commit()
    await db_session.refresh(cls)
    return cls
