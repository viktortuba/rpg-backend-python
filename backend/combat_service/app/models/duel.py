import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Duel(Base):
    __tablename__ = "duels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    challenger_id: Mapped[str] = mapped_column(String(36), ForeignKey("character_snapshots.id"), nullable=False)
    defender_id: Mapped[str] = mapped_column(String(36), ForeignKey("character_snapshots.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    winner_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("character_snapshots.id"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    challenger: Mapped["CharacterSnapshot"] = relationship("CharacterSnapshot", foreign_keys=[challenger_id])  # noqa: F821
    defender: Mapped["CharacterSnapshot"] = relationship("CharacterSnapshot", foreign_keys=[defender_id])  # noqa: F821
    winner: Mapped["CharacterSnapshot | None"] = relationship("CharacterSnapshot", foreign_keys=[winner_id])  # noqa: F821
    actions: Mapped[list["DuelAction"]] = relationship("DuelAction", back_populates="duel", lazy="selectin")  # noqa: F821


class DuelAction(Base):
    __tablename__ = "duel_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    duel_id: Mapped[str] = mapped_column(String(36), ForeignKey("duels.id"), nullable=False)
    character_id: Mapped[str] = mapped_column(String(36), ForeignKey("character_snapshots.id"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(10), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    value: Mapped[int] = mapped_column(Integer, nullable=False)

    duel: Mapped["Duel"] = relationship("Duel", back_populates="actions")
