"""add nano banana price

Revision ID: 202509140100
Revises: 202509140000
Create Date: 2025-09-14 01:00:00.000000

"""
import datetime
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '202509140100'
down_revision: Union[str, None] = '202509140000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    res = conn.execute(sa.text("SELECT 1 FROM settings WHERE key = 'nano_banana_price'"))
    exists = res.first() is not None
    if not exists:
        conn.execute(sa.text(
            """
            INSERT INTO settings (key, value, created_at, updated_at)
            VALUES (:key, :value, :created_at, :updated_at)
            """
        ), {
            'key': 'nano_banana_price',
            'value': '50',
            'created_at': datetime.datetime.utcnow(),
            'updated_at': datetime.datetime.utcnow(),
        })


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM settings WHERE key = 'nano_banana_price'"))
