"""cascade service_men.user_id on user delete

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-24 00:10:00.000000

GDPR Art. 17 (right to erasure): deleting a User must not leave orphaned
ServiceMen rows containing PII. Replace the existing FK with ON DELETE
CASCADE.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


FK_NAME = "service_men_user_id_fkey"


def upgrade() -> None:
    op.drop_constraint(FK_NAME, "service_men", type_="foreignkey")
    op.create_foreign_key(
        FK_NAME,
        source_table="service_men",
        referent_table="users",
        local_cols=["user_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(FK_NAME, "service_men", type_="foreignkey")
    op.create_foreign_key(
        FK_NAME,
        source_table="service_men",
        referent_table="users",
        local_cols=["user_id"],
        remote_cols=["id"],
    )
