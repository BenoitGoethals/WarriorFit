"""add user_consents table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-24 00:00:00.000000

GDPR Art. 7: track explicit consent for terms of service, privacy policy,
and Art. 9 health-data processing. Append-only; withdrawals set
`withdrawn_at`.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP

from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_consents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("consent_type", sa.String(length=64), nullable=False),
        sa.Column("version", sa.String(length=16), nullable=False),
        sa.Column(
            "consent_given_at",
            TIMESTAMP(),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.Column("withdrawn_at", TIMESTAMP(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "consent_type", "version", name="uq_user_consent_type_version"
        ),
    )
    op.create_index("ix_user_consents_user_id", "user_consents", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_consents_user_id", table_name="user_consents")
    op.drop_table("user_consents")
