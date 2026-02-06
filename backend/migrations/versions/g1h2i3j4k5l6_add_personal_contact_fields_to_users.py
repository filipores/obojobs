"""Add personal contact fields to users

Revision ID: g1h2i3j4k5l6
Revises: b1c2d3e4f5a6
Create Date: 2026-02-06 14:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "g1h2i3j4k5l6"
down_revision = "f0a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("phone", sa.String(50), nullable=True))
        batch_op.add_column(sa.Column("address", sa.String(255), nullable=True))
        batch_op.add_column(sa.Column("city", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("postal_code", sa.String(20), nullable=True))
        batch_op.add_column(sa.Column("website", sa.String(255), nullable=True))


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("website")
        batch_op.drop_column("postal_code")
        batch_op.drop_column("city")
        batch_op.drop_column("address")
        batch_op.drop_column("phone")
