"""rekey user_consents from user_id to service_number

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-25 00:00:00.000000

Privacy / consent records are now scoped to the serviceman (by
service_number) rather than the application user. Drop the user_id
FK + unique constraint and replace with service_number column +
unique constraint.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("uq_user_consent_type_version", "user_consents", type_="unique")
    op.drop_constraint(
        "user_consents_user_id_fkey", "user_consents", type_="foreignkey"
    )
    op.drop_index("ix_user_consents_user_id", table_name="user_consents")
    op.drop_column("user_consents", "user_id")

    op.add_column(
        "user_consents",
        sa.Column("service_number", sa.String(length=50), nullable=False),
    )
    op.create_index(
        "ix_user_consents_service_number", "user_consents", ["service_number"]
    )
    op.create_unique_constraint(
        "uq_user_consent_type_version",
        "user_consents",
        ["service_number", "consent_type", "version"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_user_consent_type_version", "user_consents", type_="unique")
    op.drop_index("ix_user_consents_service_number", table_name="user_consents")
    op.drop_column("user_consents", "service_number")

    op.add_column("user_consents", sa.Column("user_id", sa.Integer(), nullable=False))
    op.create_index("ix_user_consents_user_id", "user_consents", ["user_id"])
    op.create_foreign_key(
        "user_consents_user_id_fkey",
        source_table="user_consents",
        referent_table="users",
        local_cols=["user_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_user_consent_type_version",
        "user_consents",
        ["user_id", "consent_type", "version"],
    )
