import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.models.character import Character
from app.models.class_ import CharacterClass
from app.schemas.character import CharacterCreate, CharacterDetailRead, CharacterListRead, EffectiveStats
from app.schemas.item import ItemRead
from app.config import settings

logger = logging.getLogger(__name__)


def _build_detail(character: Character) -> CharacterDetailRead:
    items = [ItemRead.model_validate(item) for item in character.items]
    eff = EffectiveStats(
        strength=character.base_strength + sum(i.bonus_strength for i in character.items),
        agility=character.base_agility + sum(i.bonus_agility for i in character.items),
        intelligence=character.base_intelligence + sum(i.bonus_intelligence for i in character.items),
        faith=character.base_faith + sum(i.bonus_faith for i in character.items),
    )
    return CharacterDetailRead(
        id=character.id,
        name=character.name,
        health=character.health,
        mana=character.mana,
        base_strength=character.base_strength,
        base_agility=character.base_agility,
        base_intelligence=character.base_intelligence,
        base_faith=character.base_faith,
        created_by=character.created_by,
        char_class=character.char_class,
        items=items,
        effective_stats=eff,
    )


async def list_characters(db: AsyncSession) -> list[CharacterListRead]:
    result = await db.execute(select(Character))
    characters = result.scalars().all()
    return [CharacterListRead.model_validate(c) for c in characters]


async def get_character_detail(
    character_id: str,
    db: AsyncSession,
    redis,
) -> CharacterDetailRead:
    cache_key = f"character:{character_id}"
    cached = await redis.get(cache_key)
    if cached:
        logger.debug("Cache hit for %s", cache_key)
        return CharacterDetailRead.model_validate_json(cached)

    result = await db.execute(
        select(Character)
        .where(Character.id == character_id)
        .options(selectinload(Character.char_class), selectinload(Character.items))
    )
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    detail = _build_detail(character)
    await redis.set(cache_key, detail.model_dump_json(), ex=settings.CACHE_TTL)
    logger.debug("Cache set for %s", cache_key)
    return detail


async def create_character(
    data: CharacterCreate,
    created_by: str,
    db: AsyncSession,
) -> CharacterDetailRead:
    # Validate class exists
    result = await db.execute(select(CharacterClass).where(CharacterClass.id == data.class_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    # Validate unique name
    result = await db.execute(select(Character).where(Character.name == data.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Character name already taken")

    character = Character(
        name=data.name,
        health=data.health,
        mana=data.mana,
        base_strength=data.base_strength,
        base_agility=data.base_agility,
        base_intelligence=data.base_intelligence,
        base_faith=data.base_faith,
        class_id=data.class_id,
        created_by=created_by,
    )
    db.add(character)
    await db.commit()

    result = await db.execute(
        select(Character)
        .where(Character.id == character.id)
        .options(selectinload(Character.char_class), selectinload(Character.items))
    )
    character = result.scalar_one()
    return _build_detail(character)
