"""Add display_name field to users

Revision ID: 6d85c85819e7
Revises: 1987447ed91e
Create Date: 2026-01-16 00:34:43.568556

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6d85c85819e7'
down_revision = '1987447ed91e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('display_name', sa.String(length=100), nullable=True))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('display_name')
