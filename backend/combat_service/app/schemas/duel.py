from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ChallengeRequest(BaseModel):
    challenger_id: str
    defender_id: str


class ActionResponse(BaseModel):
    duel_id: str
    action_type: str
    value: int
    message: str


class DuelRead(BaseModel):
    id: str
    challenger_id: str
    defender_id: str
    status: str
    winner_id: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
