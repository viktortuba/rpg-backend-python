import logging
from contextlib import asynccontextmanager
from alembic.config import Config
from alembic import command
from sqlalchemy import select, text
from fastapi import FastAPI
from app.routers.character import router as character_router
from app.routers.item import router as item_router
from app.cache import create_redis_client
from app.database import async_session_factory
from app.models.class_ import CharacterClass

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_CLASSES = [
    {"name": "Warrior", "description": "A mighty fighter skilled in melee combat."},
    {"name": "Rogue", "description": "A swift and cunning trickster."},
    {"name": "Mage", "description": "A wielder of arcane power."},
    {"name": "Cleric", "description": "A devoted healer blessed by the gods."},
]


def run_migrations():
    logger.info("Running database migrations...")
    alembic_cfg = Config("/app/alembic.ini")
    command.upgrade(alembic_cfg, "head")
    logger.info("Migrations complete.")


async def seed_classes():
    async with async_session_factory() as db:
        result = await db.execute(select(CharacterClass).limit(1))
        if result.scalar_one_or_none():
            return
        for cls_data in DEFAULT_CLASSES:
            db.add(CharacterClass(**cls_data))
        await db.commit()
        logger.info("Seeded default character classes.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    await seed_classes()
    redis = create_redis_client()
    app.state.redis = redis
    logger.info("Redis connected.")
    yield
    await redis.aclose()
    logger.info("Redis disconnected.")


app = FastAPI(title="Character Service", lifespan=lifespan)
app.include_router(character_router)
app.include_router(item_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "character"}
