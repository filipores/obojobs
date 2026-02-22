"""add is_admin to users

Revision ID: b3a8fb73e1b5
Revises: 1274ed14b8db
Create Date: 2026-02-09 22:26:02.516951

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b3a8fb73e1b5"
down_revision = "1274ed14b8db"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("0")))


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("is_admin")
