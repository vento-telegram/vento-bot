"""Add notify_new_users_admins setting (default disabled)

Revision ID: 3a1b2c3d4e5f
Revises: 2f3c4d5e6a7b
Create Date: 2025-10-11 14:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a1b2c3d4e5f'
down_revision: Union[str, None] = '2f3c4d5e6a7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    # Default disabled: '0'
    conn.execute(
        sa.text(
            """
            INSERT INTO settings (key, value)
            VALUES (:key, :value)
            ON CONFLICT (key) DO NOTHING
            """
        ),
        {"key": "notify_new_users_admins", "value": "0"},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM settings WHERE key = :key"), {"key": "notify_new_users_admins"})

