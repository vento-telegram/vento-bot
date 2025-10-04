"""add veo prices

Revision ID: 202509170000
Revises: 202509160000
Create Date: 2025-09-17 00:00:00.000000

"""
import datetime
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '202509170000'
down_revision: Union[str, None] = '202509160000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()

    # Insert default prices for Veo
    # veo_standard_price: 10, veo_improved_price: 20
    settings_to_insert = [
        ('veo_standard_price', '10'),
        ('veo_improved_price', '20'),
    ]

    for key, value in settings_to_insert:
        res = conn.execute(sa.text("SELECT 1 FROM settings WHERE key = :key"), {'key': key})
        exists = res.first() is not None
        if not exists:
            conn.execute(sa.text(
                """
                INSERT INTO settings (key, value, created_at, updated_at)
                VALUES (:key, :value, :created_at, :updated_at)
                """
            ), {
                'key': key,
                'value': value,
                'created_at': datetime.datetime.utcnow(),
                'updated_at': datetime.datetime.utcnow(),
            })


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    for key in ('veo_standard_price', 'veo_improved_price'):
        conn.execute(sa.text("DELETE FROM settings WHERE key = :key"), {'key': key})


