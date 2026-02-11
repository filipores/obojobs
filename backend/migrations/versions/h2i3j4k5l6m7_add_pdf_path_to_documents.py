"""Add pdf_path field to documents

Revision ID: h2i3j4k5l6m7
Revises: g1h2i3j4k5l6
Create Date: 2026-02-06 16:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "h2i3j4k5l6m7"
down_revision = "g1h2i3j4k5l6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("documents", schema=None) as batch_op:
        batch_op.add_column(sa.Column("pdf_path", sa.String(length=500), nullable=True))


def downgrade():
    with op.batch_alter_table("documents", schema=None) as batch_op:
        batch_op.drop_column("pdf_path")
