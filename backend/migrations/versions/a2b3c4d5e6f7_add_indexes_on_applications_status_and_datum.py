"""add indexes on applications status and datum

Revision ID: a2b3c4d5e6f7
Revises: b3a8fb73e1b5
Create Date: 2026-02-16 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a2b3c4d5e6f7"
down_revision = "b3a8fb73e1b5"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("applications", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_applications_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_applications_datum"), ["datum"], unique=False)


def downgrade():
    with op.batch_alter_table("applications", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_applications_datum"))
        batch_op.drop_index(batch_op.f("ix_applications_status"))
