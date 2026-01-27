"""Add PDF template fields to templates

Revision ID: aac89f56b4ec
Revises: b0c0daa1c46d
Create Date: 2026-01-26 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aac89f56b4ec'
down_revision = 'b0c0daa1c46d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('templates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_pdf_template', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('pdf_path', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('variable_positions', sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table('templates', schema=None) as batch_op:
        batch_op.drop_column('variable_positions')
        batch_op.drop_column('pdf_path')
        batch_op.drop_column('is_pdf_template')
