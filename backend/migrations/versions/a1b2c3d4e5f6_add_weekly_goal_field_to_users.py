"""Add weekly_goal field to users

Revision ID: a1b2c3d4e5f6
Revises: 6d85c85819e7
Create Date: 2026-01-20 22:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '6d85c85819e7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('weekly_goal', sa.Integer(), nullable=False, server_default='5'))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('weekly_goal')
