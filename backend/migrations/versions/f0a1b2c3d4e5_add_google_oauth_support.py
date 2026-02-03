"""Add Google OAuth support to users

Revision ID: f0a1b2c3d4e5
Revises: e9f0a1b2c3d4
Create Date: 2026-02-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f0a1b2c3d4e5'
down_revision = 'e9f0a1b2c3d4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        # Add google_id column for OAuth users
        batch_op.add_column(sa.Column('google_id', sa.String(length=255), nullable=True))
        batch_op.create_index('ix_users_google_id', ['google_id'], unique=True)
        # Make password_hash nullable for OAuth-only users
        batch_op.alter_column('password_hash',
                              existing_type=sa.String(length=255),
                              nullable=True)


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('password_hash',
                              existing_type=sa.String(length=255),
                              nullable=False)
        batch_op.drop_index('ix_users_google_id')
        batch_op.drop_column('google_id')
