"""initial

Revision ID: 0001
Revises:
Create Date: 2026-04-15
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "character_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("current_health", sa.Integer, nullable=False),
        sa.Column("mana", sa.Integer, nullable=False),
        sa.Column("eff_strength", sa.Integer, nullable=False, server_default="0"),
        sa.Column("eff_agility", sa.Integer, nullable=False, server_default="0"),
        sa.Column("eff_intelligence", sa.Integer, nullable=False, server_default="0"),
        sa.Column("eff_faith", sa.Integer, nullable=False, server_default="0"),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "duels",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("challenger_id", sa.String(36), sa.ForeignKey("character_snapshots.id"), nullable=False),
        sa.Column("defender_id", sa.String(36), sa.ForeignKey("character_snapshots.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("winner_id", sa.String(36), sa.ForeignKey("character_snapshots.id"), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "duel_actions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("duel_id", sa.String(36), sa.ForeignKey("duels.id"), nullable=False),
        sa.Column("character_id", sa.String(36), sa.ForeignKey("character_snapshots.id"), nullable=False),
        sa.Column("action_type", sa.String(10), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("value", sa.Integer, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("duel_actions")
    op.drop_table("duels")
    op.drop_table("character_snapshots")
