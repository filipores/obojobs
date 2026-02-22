"""add credits_remaining to users

Revision ID: 175d87d8f730
Revises: 77dfe5317514
Create Date: 2026-02-21 00:31:21.459891

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "175d87d8f730"
down_revision = "77dfe5317514"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("credits_remaining", sa.Integer(), nullable=False, server_default=sa.text("10")))


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("credits_remaining")
