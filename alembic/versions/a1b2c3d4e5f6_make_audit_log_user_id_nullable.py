"""make audit_logs.user_id nullable

Revision ID: a1b2c3d4e5f6
Revises: 1263e3d648be
Create Date: 2026-03-18 00:00:00.000000

Allows audit_log entries for unauthenticated events (e.g. failed login attempts)
where no user_id is available.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "1263e3d648be"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "audit_logs",
        "user_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    # Remove rows with NULL user_id before restoring NOT NULL constraint
    op.execute("DELETE FROM audit_logs WHERE user_id IS NULL")
    op.alter_column(
        "audit_logs",
        "user_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
