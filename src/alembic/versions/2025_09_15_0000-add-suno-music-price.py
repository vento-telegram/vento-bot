"""add suno music price

Revision ID: 202509150000
Revises: 202509140100
Create Date: 2025-09-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import datetime


# revision identifiers, used by Alembic.
revision: str = '202509150000'
down_revision: Union[str, None] = '202509140100'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    res = conn.execute(sa.text("SELECT 1 FROM settings WHERE key = 'suno_music_price'"))
    exists = res.first() is not None
    if not exists:
        conn.execute(sa.text(
            """
            INSERT INTO settings (key, value, created_at, updated_at)
            VALUES (:key, :value, :created_at, :updated_at)
            """
        ), {
            'key': 'suno_music_price',
            'value': '180',
            'created_at': datetime.datetime.utcnow(),
            'updated_at': datetime.datetime.utcnow(),
        })


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM settings WHERE key = 'suno_music_price'"))


