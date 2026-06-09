"""add hierarchy_nodes table for unit SOR structure

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-09 00:00:00.000000

Adds a self-referential adjacency-list table to represent a battalion's
Standard Organisation Reference (SOR / Structure Organique de Référence).

    hierarchy_nodes
        id                  SERIAL PK
        name                VARCHAR(120)  NOT NULL
        echelon             VARCHAR(20)   NOT NULL  -- BATTALION/COMPANY/PLATOON/SECTION/STAFF
        callsign            VARCHAR(30)   NULL
        establishment_strength  INTEGER  NULL
        role                VARCHAR(200)  NULL
        parent_id           INTEGER       NULL  FK → hierarchy_nodes.id ON DELETE CASCADE
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "hierarchy_nodes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("echelon", sa.String(length=20), nullable=False),
        sa.Column("callsign", sa.String(length=30), nullable=True),
        sa.Column("establishment_strength", sa.Integer(), nullable=True),
        sa.Column("role", sa.String(length=200), nullable=True),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["hierarchy_nodes.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hierarchy_nodes_parent_id", "hierarchy_nodes", ["parent_id"])


def downgrade() -> None:
    op.drop_index("ix_hierarchy_nodes_parent_id", table_name="hierarchy_nodes")
    op.drop_table("hierarchy_nodes")
