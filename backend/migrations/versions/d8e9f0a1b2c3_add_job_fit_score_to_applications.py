"""Add job_fit_score field to applications

Revision ID: d8e9f0a1b2c3
Revises: c7f8e9a0b1d2
Create Date: 2026-02-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd8e9f0a1b2c3'
down_revision = 'c7f8e9a0b1d2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('job_fit_score', sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.drop_column('job_fit_score')
