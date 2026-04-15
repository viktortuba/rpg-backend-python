from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user, require_game_master, TokenData
from app.schemas.character import CharacterCreate, CharacterListRead, CharacterDetailRead
from app.schemas.class_ import ClassRead
from app.models.class_ import CharacterClass
from app.services import character_service

router = APIRouter(prefix="/api")


@router.get("/classes", response_model=list[ClassRead])
async def list_classes(
    _: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CharacterClass))
    return [ClassRead.model_validate(c) for c in result.scalars().all()]


@router.get("/character", response_model=list[CharacterListRead])
async def list_characters(
    _: TokenData = Depends(require_game_master),
    db: AsyncSession = Depends(get_db),
):
    return await character_service.list_characters(db)


@router.post("/character", response_model=CharacterDetailRead, status_code=201)
async def create_character(
    data: CharacterCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await character_service.create_character(data, current_user.user_id, db)


@router.get("/character/{character_id}", response_model=CharacterDetailRead)
async def get_character(
    character_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    detail = await character_service.get_character_detail(character_id, db, request.app.state.redis)

    if current_user.role != "GameMaster" and detail.created_by != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return detail
