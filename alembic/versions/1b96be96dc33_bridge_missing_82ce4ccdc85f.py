"""bridge-missing-82ce4ccdc85f

Revision ID: 1b96be96dc33
Revises: 09a887bcf10b
Create Date: 2025-10-28 17:36:31.132600

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82ce4ccdc85f'
down_revision: Union[str, Sequence[str], None] = '09a887bcf10b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
