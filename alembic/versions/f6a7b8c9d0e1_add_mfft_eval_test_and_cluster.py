"""add MFFT Eval test table and ServiceMen.cluster column

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-15 09:00:00.000000

Adds the new MFFT Eval polymorphic subtype (`mfft_eval_tests`) and the
`cluster` column on `service_men` used by the calculator to pick the
scoring scale.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CLUSTER_ENUM_NAME = "cluster"
CLUSTER_VALUES = ("COMBAT", "ENABLER", "OPS_SP", "TER_SP", "NON_DEP")


def upgrade() -> None:
    cluster_enum = sa.Enum(*CLUSTER_VALUES, name=CLUSTER_ENUM_NAME)
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

    # Extend the existing typefitnesstest enum with the new MFFT_EVAL value
    # so TestSession rows of this type can be inserted.
    op.execute("ALTER TYPE typefitnesstest ADD VALUE IF NOT EXISTS 'MFFT_EVAL'")

    op.create_table(
        "mfft_eval_tests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pull_ups", sa.Integer(), nullable=False),
        sa.Column("burpees_step_over", sa.Integer(), nullable=False),
        sa.Column("farmer_walk_m", sa.Integer(), nullable=False),
        sa.Column("push_ups_release", sa.Integer(), nullable=False),
        sa.Column("casualty_drag_m", sa.Integer(), nullable=False),
        sa.Column("sandbag_carry_m", sa.Integer(), nullable=False),
        sa.Column("combat_run_seconds", sa.Integer(), nullable=False),
        sa.Column("combat_swim_seconds", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["id"], ["fitness_tests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("mfft_eval_tests")
    op.drop_column("service_men", "cluster")
    cluster_enum = sa.Enum(*CLUSTER_VALUES, name=CLUSTER_ENUM_NAME)
    cluster_enum.drop(op.get_bind(), checkfirst=True)
