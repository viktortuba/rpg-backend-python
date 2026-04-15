from pydantic import BaseModel
from typing import Optional


class ClassCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ClassRead(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}
