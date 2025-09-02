"""add_notification_flags

Revision ID: ce3d6fddf9dd
Revises: 001
Create Date: 2025-09-02 12:12:51.254276

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce3d6fddf9dd'
down_revision: Union[str, Sequence[str], None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Добавляем поля для отслеживания отправленных уведомлений о таймере
    op.add_column('users', sa.Column('notification_6_hours_sent', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('notification_1_hour_sent', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('notification_10_minutes_sent', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем поля для отслеживания отправленных уведомлений о таймере
    op.drop_column('users', 'notification_6_hours_sent')
    op.drop_column('users', 'notification_1_hour_sent')
    op.drop_column('users', 'notification_10_minutes_sent')
