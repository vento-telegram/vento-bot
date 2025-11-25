"""Add nano banana pro and sora prices

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-11-25 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # Add new pricing settings
    new_settings = [
        ("nano_banana_pro_price", "100"),
        ("sora2_video_price", "150"),
        ("sora2_pro_video_price", "300"),
    ]
    
    for key, value in new_settings:
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
    keys = ["nano_banana_pro_price", "sora2_video_price", "sora2_pro_video_price"]
    for key in keys:
        conn.execute(sa.text("DELETE FROM settings WHERE key = :key"), {"key": key})

