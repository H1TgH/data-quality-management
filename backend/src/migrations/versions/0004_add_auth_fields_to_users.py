"""add name and password fields to users

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004"
down_revision: Union[str, Sequence[str], None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("name", sa.String(), nullable=True))
    op.add_column("users", sa.Column("password", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "password")
    op.drop_column("users", "name")
