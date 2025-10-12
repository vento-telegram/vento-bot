"""Update specific settings values

Revision ID: 7f9b8c2d1e3a
Revises: 3a1b2c3d4e5f
Create Date: 2025-10-12 14:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f9b8c2d1e3a'
down_revision: Union[str, None] = '3a1b2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            UPDATE settings
            SET value = '350'
            WHERE id = 5;
        """)
    )
    conn.execute(
        sa.text("""
            UPDATE settings
            SET value = '1760'
            WHERE id = 20;
        """)
    )
    conn.execute(
        sa.text("""
            UPDATE settings
            SET value = '880'
            WHERE id = 19;
        """)
    )
    conn.execute(
        sa.text("""
            UPDATE settings
            SET value = '880'
            WHERE id = 31;
        """)
    )


def downgrade() -> None:
    pass
