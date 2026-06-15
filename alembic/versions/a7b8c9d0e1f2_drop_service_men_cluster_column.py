"""drop service_men.cluster column (now derived from para)

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-06-15 12:00:00.000000

Project rule: a paratrooper's MFFT cluster is always COMBAT, every other
serviceman is ENABLER. The mapping is fully derivable from ``para`` so we
drop the stored ``service_men.cluster`` column and let the ORM expose a
``@property cluster`` instead. The ``cluster`` PostgreSQL enum type goes
with it.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CLUSTER_VALUES = ("COMBAT", "ENABLER", "OPS_SP", "TER_SP", "NON_DEP")


def upgrade() -> None:
    op.drop_column("service_men", "cluster")
    op.execute("DROP TYPE IF EXISTS cluster")


def downgrade() -> None:
    cluster_enum = sa.Enum(*CLUSTER_VALUES, name="cluster")
    cluster_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "service_men",
        sa.Column(
            "cluster",
            cluster_enum,
            nullable=False,
            server_default="NON_DEP",
        ),
    )
