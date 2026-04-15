import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete
from fastapi import HTTPException, status
from app.models.item import Item
from app.models.character import Character, character_items
from app.schemas.item import ItemCreate, ItemRead, GrantItemRequest, GiftItemRequest

logger = logging.getLogger(__name__)


async def _invalidate(redis, *character_ids: str):
    for cid in character_ids:
        await redis.delete(f"character:{cid}")
        logger.debug("Cache invalidated for character:%s", cid)


async def list_items(db: AsyncSession) -> list[ItemRead]:
    result = await db.execute(select(Item))
    return [ItemRead.model_validate(item) for item in result.scalars().all()]


async def get_item(item_id: str, db: AsyncSession) -> ItemRead:
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return ItemRead.model_validate(item)


async def create_item(data: ItemCreate, db: AsyncSession) -> ItemRead:
    item = Item(
        base_name=data.base_name,
        description=data.description,
        bonus_strength=data.bonus_strength,
        bonus_agility=data.bonus_agility,
        bonus_intelligence=data.bonus_intelligence,
        bonus_faith=data.bonus_faith,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return ItemRead.model_validate(item)


async def grant_item(data: GrantItemRequest, db: AsyncSession, redis) -> dict:
    # Verify character and item exist
    char_result = await db.execute(select(Character).where(Character.id == data.character_id))
    if not char_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    item_result = await db.execute(select(Item).where(Item.id == data.item_id))
    if not item_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    import uuid
    await db.execute(
        insert(character_items).values(
            id=str(uuid.uuid4()),
            character_id=data.character_id,
            item_id=data.item_id,
        )
    )
    await db.commit()
    await _invalidate(redis, data.character_id)
    return {"detail": "Item granted"}


async def gift_item(data: GiftItemRequest, db: AsyncSession, redis) -> dict:
    # Verify both characters exist
    for cid in (data.from_character_id, data.to_character_id):
        result = await db.execute(select(Character).where(Character.id == cid))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Character {cid} not found")

    # Verify item exists
    item_result = await db.execute(select(Item).where(Item.id == data.item_id))
    if not item_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    # Find one character_items row linking from_character to item
    ci_result = await db.execute(
        select(character_items.c.id)
        .where(character_items.c.character_id == data.from_character_id)
        .where(character_items.c.item_id == data.item_id)
        .limit(1)
    )
    row = ci_result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not in source character's inventory")

    # Remove from source, add to destination
    await db.execute(delete(character_items).where(character_items.c.id == row.id))

    import uuid
    await db.execute(
        insert(character_items).values(
            id=str(uuid.uuid4()),
            character_id=data.to_character_id,
            item_id=data.item_id,
        )
    )
    await db.commit()
    await _invalidate(redis, data.from_character_id, data.to_character_id)
    return {"detail": "Item transferred"}
