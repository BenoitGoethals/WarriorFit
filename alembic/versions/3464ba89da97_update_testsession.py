"""update testsession

Revision ID: 3464ba89da97
Revises: 5725be57b291
Create Date: 2025-11-03 19:49:55.173195

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3464ba89da97'
down_revision: Union[str, Sequence[str], None] = '5725be57b291'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
   ...


def downgrade() -> None:
  ...