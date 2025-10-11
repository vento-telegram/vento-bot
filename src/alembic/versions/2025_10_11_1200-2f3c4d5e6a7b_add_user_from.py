"""Add user.from referrer column

Revision ID: 2f3c4d5e6a7b
Revises: bdc51e473229
Create Date: 2025-10-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f3c4d5e6a7b'
down_revision: Union[str, None] = 'bdc51e473229'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add nullable referrer column named "from" (reserved keyword handled by Alembic/SQLAlchemy quoting)
    op.add_column('user', sa.Column('from', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('user', 'from')

