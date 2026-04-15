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
        "classes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
    )
    op.create_table(
        "items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("base_name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("bonus_strength", sa.Integer, nullable=False, server_default="0"),
        sa.Column("bonus_agility", sa.Integer, nullable=False, server_default="0"),
        sa.Column("bonus_intelligence", sa.Integer, nullable=False, server_default="0"),
        sa.Column("bonus_faith", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_table(
        "characters",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("health", sa.Integer, nullable=False),
        sa.Column("mana", sa.Integer, nullable=False),
        sa.Column("base_strength", sa.Integer, nullable=False, server_default="0"),
        sa.Column("base_agility", sa.Integer, nullable=False, server_default="0"),
        sa.Column("base_intelligence", sa.Integer, nullable=False, server_default="0"),
        sa.Column("base_faith", sa.Integer, nullable=False, server_default="0"),
        sa.Column("class_id", sa.String(36), sa.ForeignKey("classes.id"), nullable=False),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "character_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("character_id", sa.String(36), sa.ForeignKey("characters.id"), nullable=False),
        sa.Column("item_id", sa.String(36), sa.ForeignKey("items.id"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("character_items")
    op.drop_table("characters")
    op.drop_table("items")
    op.drop_table("classes")
