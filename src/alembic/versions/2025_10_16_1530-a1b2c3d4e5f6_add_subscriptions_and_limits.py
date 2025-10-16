"""Add subscriptions table and daily limits for subs

Revision ID: a1b2c3d4e5f6
Revises: 9a8b7c6d5e4f
Create Date: 2025-10-16 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9a8b7c6d5e4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'subscription',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('till', sa.DateTime(), nullable=False),
        sa.Column('requests_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('mini_requests_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    conn = op.get_bind()
    for key in ("sub_gpt_daily_limit", "sub_gpt_mini_daily_limit"):
        conn.execute(
            sa.text(
                """
                INSERT INTO settings (key, value)
                VALUES (:key, '0')
                ON CONFLICT (key) DO NOTHING
                """
            ),
            {"key": key},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for key in ("sub_gpt_daily_limit", "sub_gpt_mini_daily_limit"):
        conn.execute(sa.text("DELETE FROM settings WHERE key = :key"), {"key": key})
    op.drop_table('subscription')

