import uuid
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from jose import jwt
from app.database import Base, get_db
from app.main import app
from app.config import settings

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def make_token(role: str = "User", user_id: str = None) -> tuple[str, str]:
    uid = user_id or str(uuid.uuid4())
    payload = {
        "sub": uid,
        "username": f"user_{uid[:8]}",
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256"), uid


def make_character_data(owner_id: str, name: str = "Hero", health: int = 100,
                         strength: int = 10, agility: int = 5,
                         intelligence: int = 8, faith: int = 3) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "health": health,
        "mana": 50,
        "base_strength": strength,
        "base_agility": agility,
        "base_intelligence": intelligence,
        "base_faith": faith,
        "created_by": owner_id,
        "char_class": {"id": str(uuid.uuid4()), "name": "Warrior"},
        "items": [],
        "effective_stats": {
            "strength": strength,
            "agility": agility,
            "intelligence": intelligence,
            "faith": faith,
        },
    }


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
    mock_char_client = AsyncMock()
    mock_char_client.gift_item = AsyncMock()
    mock_char_client.pick_random_item = AsyncMock(return_value=None)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    import app.routers.combat as combat_router_module
    original_client = combat_router_module.character_client
    combat_router_module.character_client = mock_char_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac, mock_char_client, db_session

    app.dependency_overrides.clear()
    combat_router_module.character_client = original_client
