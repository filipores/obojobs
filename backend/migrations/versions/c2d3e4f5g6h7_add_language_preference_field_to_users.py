"""Add language_preference field to users

Revision ID: c2d3e4f5g6h7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2d3e4f5g6h7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('language_preference', sa.String(length=10), nullable=False, server_default='en'))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('language_preference')
