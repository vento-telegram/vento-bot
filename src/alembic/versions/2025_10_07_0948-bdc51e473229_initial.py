"""Initial

Revision ID: bdc51e473229
Revises: 202509170000
Create Date: 2025-10-07 09:48:56.984165

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import datetime


# revision identifiers, used by Alembic.
revision: str = 'bdc51e473229'
down_revision: Union[str, None] = '202509170000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('balance', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_admin', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_blocked', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id'),
    )

    op.create_table(
        'settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.String(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key'),
    )

    conn = op.get_bind()
    now = datetime.datetime.utcnow()

    default_settings = [
        ('gpt_price', '47'),
        ('gpt_mini_price', '10'),
        ('gpt_image_price', '127'),
        ('daily_bonus', '50'),
        ('start_bonus', '150'),
        ('700_bundle_price', '199'),
        ('1600_bundle_price', '399'),
        ('4500_bundle_price', '990'),
        ('11000_bundle_price', '2290'),
        ('28000_bundle_price', '4990'),
        ('nano_banana_price', '50'),
        ('suno_music_price', '180'),
        ('700_stars_price', '99'),
        ('1600_stars_price', '219'),
        ('4500_stars_price', '599'),
        ('11000_stars_price', '1399'),
        ('28000_stars_price', '2799'),
        ('veo_standard_price', '10'),
        ('veo_improved_price', '20'),
    ]

    for key, value in default_settings:
        conn.execute(sa.text(
            """
            INSERT INTO settings (key, value, created_at, updated_at)
            VALUES (:key, :value, :created_at, :updated_at)
            """
        ), {'key': key, 'value': value, 'created_at': now, 'updated_at': now})

    op.create_table(
        'tokens_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('delta', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(), nullable=False),
        sa.Column('meta', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('tokens_history')
    op.drop_table('settings')
    op.drop_table('user')
