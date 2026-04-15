import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class CharacterSnapshot(Base):
    __tablename__ = "character_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    current_health: Mapped[int] = mapped_column(Integer, nullable=False)
    mana: Mapped[int] = mapped_column(Integer, nullable=False)
    eff_strength: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    eff_agility: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    eff_intelligence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    eff_faith: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
