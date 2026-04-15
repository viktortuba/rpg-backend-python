import logging
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user, TokenData
from app.schemas.duel import ChallengeRequest, ActionResponse, DuelRead
from app.services import combat_service
from app.services.character_client import character_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


def _extract_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")


@router.post("/challenge", response_model=DuelRead, status_code=201)
async def challenge(
    data: ChallengeRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    token = _extract_token(request)
    try:
        challenger_data = await character_client.get_character(data.challenger_id, token)
        defender_data = await character_client.get_character(data.defender_id, token)
    except Exception as exc:
        logger.error("Failed to fetch character data: %s", exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Could not fetch character data")

    return await combat_service.create_challenge(
        data, challenger_data, defender_data, current_user.user_id, db
    )


@router.post("/{duel_id}/attack", response_model=ActionResponse)
async def attack(
    duel_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    token = _extract_token(request)
    return await combat_service.perform_action(duel_id, "attack", current_user.user_id, db, character_client, token)


@router.post("/{duel_id}/cast", response_model=ActionResponse)
async def cast(
    duel_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    token = _extract_token(request)
    return await combat_service.perform_action(duel_id, "cast", current_user.user_id, db, character_client, token)


@router.post("/{duel_id}/heal", response_model=ActionResponse)
async def heal(
    duel_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    token = _extract_token(request)
    return await combat_service.perform_action(duel_id, "heal", current_user.user_id, db, character_client, token)


@router.get("/{duel_id}", response_model=DuelRead)
async def get_duel(
    duel_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await combat_service.get_duel(duel_id, db)
