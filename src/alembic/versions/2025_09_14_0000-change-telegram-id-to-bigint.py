"""change telegram_id to bigint

Revision ID: 202509140000
Revises: a4d36866b792
Create Date: 2025-09-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '202509140000'
down_revision: Union[str, None] = 'a4d36866b792'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # PostgreSQL specific alter to BIGINT
    op.alter_column('user', 'telegram_id',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Revert back to INTEGER
    op.alter_column('user', 'telegram_id',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=False)
