from pydantic import BaseModel, model_validator
from typing import Optional


STAT_SUFFIXES = {
    "bonus_strength": "of Strength",
    "bonus_agility": "of Agility",
    "bonus_intelligence": "of Intelligence",
    "bonus_faith": "of Faith",
}


class ItemCreate(BaseModel):
    base_name: str
    description: Optional[str] = None
    bonus_strength: int = 0
    bonus_agility: int = 0
    bonus_intelligence: int = 0
    bonus_faith: int = 0


class ItemRead(BaseModel):
    id: str
    name: str  # computed
    description: Optional[str] = None
    bonus_strength: int
    bonus_agility: int
    bonus_intelligence: int
    bonus_faith: int

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def compute_name(cls, data):
        # data may be an ORM object or a dict
        if hasattr(data, "__dict__"):
            bonuses = {
                "bonus_strength": data.bonus_strength,
                "bonus_agility": data.bonus_agility,
                "bonus_intelligence": data.bonus_intelligence,
                "bonus_faith": data.bonus_faith,
            }
            base = data.base_name
        else:
            bonuses = {
                "bonus_strength": data.get("bonus_strength", 0),
                "bonus_agility": data.get("bonus_agility", 0),
                "bonus_intelligence": data.get("bonus_intelligence", 0),
                "bonus_faith": data.get("bonus_faith", 0),
            }
            base = data.get("base_name", data.get("name", ""))

        max_stat = max(bonuses, key=lambda k: bonuses[k]) if any(v > 0 for v in bonuses.values()) else None
        suffix = f" {STAT_SUFFIXES[max_stat]}" if max_stat else ""

        if isinstance(data, dict):
            data["name"] = base + suffix
        else:
            # Return a dict for further validation
            return {
                "id": data.id,
                "name": base + suffix,
                "description": data.description,
                "bonus_strength": data.bonus_strength,
                "bonus_agility": data.bonus_agility,
                "bonus_intelligence": data.bonus_intelligence,
                "bonus_faith": data.bonus_faith,
            }
        return data


class GrantItemRequest(BaseModel):
    character_id: str
    item_id: str


class GiftItemRequest(BaseModel):
    from_character_id: str
    to_character_id: str
    item_id: str
