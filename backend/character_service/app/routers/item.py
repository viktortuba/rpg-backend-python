from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user, require_game_master, TokenData
from app.schemas.item import ItemCreate, ItemRead, GrantItemRequest, GiftItemRequest
from app.services import item_service

router = APIRouter(prefix="/api")


@router.get("/items", response_model=list[ItemRead])
async def list_items(
    _: TokenData = Depends(require_game_master),
    db: AsyncSession = Depends(get_db),
):
    return await item_service.list_items(db)


@router.post("/items", response_model=ItemRead, status_code=201)
async def create_item(
    data: ItemCreate,
    _: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await item_service.create_item(data, db)


@router.get("/items/{item_id}", response_model=ItemRead)
async def get_item(
    item_id: str,
    _: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await item_service.get_item(item_id, db)


@router.post("/items/grant")
async def grant_item(
    data: GrantItemRequest,
    request: Request,
    _: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await item_service.grant_item(data, db, request.app.state.redis)


@router.post("/items/gift")
async def gift_item(
    data: GiftItemRequest,
    request: Request,
    _: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await item_service.gift_item(data, db, request.app.state.redis)
