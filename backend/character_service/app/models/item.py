import uuid
from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    base_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    bonus_strength: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bonus_agility: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bonus_intelligence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bonus_faith: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
