"""Add title field to ats_analyses

Revision ID: 1987447ed91e
Revises: 4119d07912f4
Create Date: 2026-01-16 00:31:35.383374

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1987447ed91e'
down_revision = '4119d07912f4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ats_analyses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('title', sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table('ats_analyses', schema=None) as batch_op:
        batch_op.drop_column('title')
