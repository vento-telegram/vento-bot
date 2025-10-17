"""Add BYN VISA/Mastercard prices and BYN→USD rate

Revision ID: 9a8b7c6d5e4f
Revises: 7f9b8c2d1e3a
Create Date: 2025-10-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a8b7c6d5e4f'
down_revision: Union[str, None] = '7f9b8c2d1e3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Exchange rate setting: BYN per 1 USD
    conn.execute(
        sa.text(
            """
            INSERT INTO settings (key, value)
            VALUES (:key, :value)
            ON CONFLICT (key) DO NOTHING
            """
        ),
        {"key": "byn-usd", "value": "2.97"},
    )

    # BYN prices for VISA/Mastercard bundles
    byn_prices = {
        "300_byn_bundle_price": "10",
        "1100_byn_bundle_price": "35",
        "2400_byn_bundle_price": "75",
        "3800_byn_bundle_price": "110",
        "7000_byn_bundle_price": "185",
    }

    for key, value in byn_prices.items():
        conn.execute(
            sa.text(
                """
                INSERT INTO settings (key, value)
                VALUES (:key, :value)
                ON CONFLICT (key) DO NOTHING
                """
            ),
            {"key": key, "value": value},
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM settings WHERE key = :key"), {"key": "byn-usd"})
    for key in [
        "300_byn_bundle_price",
        "1100_byn_bundle_price",
        "2400_byn_bundle_price",
        "3800_byn_bundle_price",
        "7000_byn_bundle_price",
    ]:
        conn.execute(sa.text("DELETE FROM settings WHERE key = :key"), {"key": key})

