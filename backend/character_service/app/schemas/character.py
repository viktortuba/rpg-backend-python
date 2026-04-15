from pydantic import BaseModel
from typing import Optional
from app.schemas.item import ItemRead
from app.schemas.class_ import ClassRead


class CharacterCreate(BaseModel):
    name: str
    health: int
    mana: int
    base_strength: int = 0
    base_agility: int = 0
    base_intelligence: int = 0
    base_faith: int = 0
    class_id: str


class CharacterListRead(BaseModel):
    id: str
    name: str
    health: int
    mana: int

    model_config = {"from_attributes": True}


class EffectiveStats(BaseModel):
    strength: int
    agility: int
    intelligence: int
    faith: int


class CharacterDetailRead(BaseModel):
    id: str
    name: str
    health: int
    mana: int
    base_strength: int
    base_agility: int
    base_intelligence: int
    base_faith: int
    created_by: str
    char_class: Optional[ClassRead] = None
    items: list[ItemRead] = []
    effective_stats: EffectiveStats

    model_config = {"from_attributes": True}
