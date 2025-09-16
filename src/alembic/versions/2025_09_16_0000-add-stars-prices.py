"""add stars prices

Revision ID: 202509160000
Revises: 202509150000
Create Date: 2025-09-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import datetime


# revision identifiers, used by Alembic.
revision: str = '202509160000'
down_revision: Union[str, None] = '202509150000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    
    # Star prices for token bundles
    star_prices = [
        ('700_stars_price', '99'),
        ('1600_stars_price', '219'),
        ('4500_stars_price', '599'),
        ('11000_stars_price', '1399'),
        ('28000_stars_price', '2799'),
    ]
    
    for key, value in star_prices:
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
    star_price_keys = [
        '700_stars_price',
        '1600_stars_price', 
        '4500_stars_price',
        '11000_stars_price',
        '28000_stars_price',
    ]
    
    for key in star_price_keys:
        conn.execute(sa.text("DELETE FROM settings WHERE key = :key"), {'key': key})
