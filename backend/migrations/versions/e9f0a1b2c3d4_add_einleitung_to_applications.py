"""Add einleitung field to applications for premium reveal

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2026-02-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e9f0a1b2c3d4'
down_revision = 'd8e9f0a1b2c3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('einleitung', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.drop_column('einleitung')
