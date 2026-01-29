"""Separate free and premium tests

Revision ID: 002_separate_tests
Revises: ce3d6fddf9dd
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_separate_tests'
down_revision = 'ce3d6fddf9dd'
branch_labels = None
depends_on = None


def upgrade():
    # Добавляем новое поле test_version в таблицу questions
    op.add_column('questions', sa.Column('test_version', sa.String(20), server_default='free'))
    
    # Добавляем новые поля в таблицу users для раздельного отслеживания тестов
    op.add_column('users', sa.Column('free_test_completed', sa.Boolean(), server_default='0'))
    op.add_column('users', sa.Column('premium_test_completed', sa.Boolean(), server_default='0'))
    op.add_column('users', sa.Column('current_free_question_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('current_premium_question_id', sa.Integer(), nullable=True))
    
    # Помечаем все существующие вопросы как "premium" (для обратной совместимости)
    op.execute("UPDATE questions SET test_version = 'premium' WHERE test_version = 'free'")
    
    # Копируем данные из старых полей в новые для существующих пользователей
    op.execute("""
        UPDATE users 
        SET free_test_completed = test_completed,
            current_free_question_id = current_question_id
        WHERE test_completed = 1 AND is_paid = 0
    """)
    
    op.execute("""
        UPDATE users 
        SET premium_test_completed = test_completed,
            current_premium_question_id = current_question_id
        WHERE test_completed = 1 AND is_paid = 1
    """)


def downgrade():
    # Удаляем добавленные колонки
    op.drop_column('users', 'current_premium_question_id')
    op.drop_column('users', 'current_free_question_id')
    op.drop_column('users', 'premium_test_completed')
    op.drop_column('users', 'free_test_completed')
    op.drop_column('questions', 'test_version')
