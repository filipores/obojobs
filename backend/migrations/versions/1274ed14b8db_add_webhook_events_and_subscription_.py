"""add webhook events and subscription fields

Revision ID: 1274ed14b8db
Revises: h2i3j4k5l6m7
Create Date: 2026-02-09 20:46:34.335975

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1274ed14b8db"
down_revision = "h2i3j4k5l6m7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "webhook_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stripe_event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("webhook_events", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_webhook_events_stripe_event_id"), ["stripe_event_id"], unique=True)

    with op.batch_alter_table("subscriptions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.text("0"))
        )
        batch_op.add_column(sa.Column("canceled_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("trial_end", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("subscriptions", schema=None) as batch_op:
        batch_op.drop_column("trial_end")
        batch_op.drop_column("canceled_at")
        batch_op.drop_column("cancel_at_period_end")

    with op.batch_alter_table("webhook_events", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_webhook_events_stripe_event_id"))

    op.drop_table("webhook_events")
