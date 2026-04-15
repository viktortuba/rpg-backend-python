import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

# M2M join table with its own PK to allow multiple copies of the same item
character_items = Table(
    "character_items",
    Base.metadata,
    Column("id", String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
    Column("character_id", String(36), ForeignKey("characters.id"), nullable=False),
    Column("item_id", String(36), ForeignKey("items.id"), nullable=False),
)


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    health: Mapped[int] = mapped_column(Integer, nullable=False)
    mana: Mapped[int] = mapped_column(Integer, nullable=False)
    base_strength: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    base_agility: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    base_intelligence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    base_faith: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    class_id: Mapped[str] = mapped_column(String(36), ForeignKey("classes.id"), nullable=False)
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    char_class: Mapped["CharacterClass"] = relationship("CharacterClass", back_populates="characters")  # noqa: F821
    items: Mapped[list] = relationship("Item", secondary=character_items, lazy="selectin")
