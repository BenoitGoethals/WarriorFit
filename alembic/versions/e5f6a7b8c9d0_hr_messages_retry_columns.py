"""add retry / dead-letter columns to hr_messages

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-04-27 18:00:00.000000

The Broker outbox now supports exponential back-off and a dead-letter
state instead of retrying every row at a flat 5 s interval forever.
This migration adds the columns the new logic needs:

    attempt_count INTEGER       NOT NULL DEFAULT 0
    next_retry_at TIMESTAMP     NULL              -- earliest time worker may retry
    dead_letter   BOOLEAN       NOT NULL DEFAULT FALSE
    last_error    VARCHAR(500)  NULL              -- short triage string

A composite index on (dead_letter, next_retry_at) makes the broker's
"due now" query cheap.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "e5f6a7b8c9d0"
# Chained off the GDPR consent-by-service-number migration so this can be
# applied on databases that already ran the GDPR upgrade chain.
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "hr_messages",
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "hr_messages",
        sa.Column("next_retry_at", sa.TIMESTAMP(), nullable=True),
    )
    op.add_column(
        "hr_messages",
        sa.Column(
            "dead_letter",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "hr_messages",
        sa.Column("last_error", sa.String(length=500), nullable=True),
    )
    op.create_index(
        "ix_hr_messages_due",
        "hr_messages",
        ["dead_letter", "next_retry_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_hr_messages_due", table_name="hr_messages")
    op.drop_column("hr_messages", "last_error")
    op.drop_column("hr_messages", "dead_letter")
    op.drop_column("hr_messages", "next_retry_at")
    op.drop_column("hr_messages", "attempt_count")
