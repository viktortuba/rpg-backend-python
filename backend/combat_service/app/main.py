import logging
from contextlib import asynccontextmanager
from alembic.config import Config
from alembic import command
from fastapi import FastAPI
from app.routers.combat import router as combat_router
from app.services.character_client import character_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def run_migrations():
    logger.info("Running database migrations...")
    alembic_cfg = Config("/app/alembic.ini")
    command.upgrade(alembic_cfg, "head")
    logger.info("Migrations complete.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    yield
    await character_client.aclose()


app = FastAPI(title="Combat Service", lifespan=lifespan)
app.include_router(combat_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "combat"}
