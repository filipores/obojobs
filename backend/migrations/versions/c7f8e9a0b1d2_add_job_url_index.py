"""Add index on job_url column for job_recommendations

Revision ID: c7f8e9a0b1d2
Revises: aac89f56b4ec
Create Date: 2026-01-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7f8e9a0b1d2'
down_revision = 'aac89f56b4ec'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('job_recommendations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_job_recommendations_job_url'), ['job_url'], unique=False)


def downgrade():
    with op.batch_alter_table('job_recommendations', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_job_recommendations_job_url'))
