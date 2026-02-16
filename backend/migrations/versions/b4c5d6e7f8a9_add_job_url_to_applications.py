"""add job_url to applications

Revision ID: b4c5d6e7f8a9
Revises: a2b3c4d5e6f7
Create Date: 2026-02-16 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b4c5d6e7f8a9"
down_revision = "a2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("applications", schema=None) as batch_op:
        batch_op.add_column(sa.Column("job_url", sa.String(500), nullable=True))


def downgrade():
    with op.batch_alter_table("applications", schema=None) as batch_op:
        batch_op.drop_column("job_url")
