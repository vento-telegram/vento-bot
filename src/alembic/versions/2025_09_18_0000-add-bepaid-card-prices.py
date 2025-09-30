"""add bepaid card prices (RUB) from yookassa

Revision ID: 202509180000
Revises: 202509170000
Create Date: 2025-09-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import datetime


# revision identifiers, used by Alembic.
revision: str = '202509180000'
down_revision: Union[str, None] = '202509170000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed bePaid card prices in RUB from existing YooKassa bundle prices."""
    conn = op.get_bind()

    # Map: tokens -> (yookassa key -> bepay keys)
    bundles = [700, 1600, 4500, 11000, 28000]

    for tokens in bundles:
        yookassa_key = f"{tokens}_bundle_price"
        # Read existing yookassa price in RUB
        res = conn.execute(sa.text("SELECT value FROM settings WHERE key = :key"), {"key": yookassa_key})
        row = res.first()
        if not row:
            continue
        try:
            rub_price = int(str(row[0]))
        except Exception:
            # Skip if invalid
            continue

        # bePaid expects minor units (kopecks) and currency
        bepay_price_key = f"{tokens}_card_price_minor"
        bepay_curr_key = f"{tokens}_card_currency"

        # Insert price_minor if not exists
        exists_price = conn.execute(sa.text("SELECT 1 FROM settings WHERE key = :key"), {"key": bepay_price_key}).first()
        if not exists_price:
            conn.execute(sa.text(
                """
                INSERT INTO settings (key, value, created_at, updated_at)
                VALUES (:key, :value, :created_at, :updated_at)
                """
            ), {
                'key': bepay_price_key,
                'value': str(rub_price * 100),
                'created_at': datetime.datetime.utcnow(),
                'updated_at': datetime.datetime.utcnow(),
            })

        # Insert currency RUB if not exists
        exists_curr = conn.execute(sa.text("SELECT 1 FROM settings WHERE key = :key"), {"key": bepay_curr_key}).first()
        if not exists_curr:
            conn.execute(sa.text(
                """
                INSERT INTO settings (key, value, created_at, updated_at)
                VALUES (:key, :value, :created_at, :updated_at)
                """
            ), {
                'key': bepay_curr_key,
                'value': 'RUB',
                'created_at': datetime.datetime.utcnow(),
                'updated_at': datetime.datetime.utcnow(),
            })


def downgrade() -> None:
    """Remove seeded bePaid card prices and currencies."""
    conn = op.get_bind()
    bundles = [700, 1600, 4500, 11000, 28000]

    for tokens in bundles:
        bepay_price_key = f"{tokens}_card_price_minor"
        bepay_curr_key = f"{tokens}_card_currency"
        conn.execute(sa.text("DELETE FROM settings WHERE key = :key"), {"key": bepay_price_key})
        conn.execute(sa.text("DELETE FROM settings WHERE key = :key"), {"key": bepay_curr_key})
