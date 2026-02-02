"""Add SalaryCoachData model for persisting salary coach data

Revision ID: b0c0daa1c46d
Revises: 6d85c85819e7
Create Date: 2026-01-16 09:29:31.739042

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b0c0daa1c46d"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade():
    # Create salary_coach_data table
    op.create_table(
        "salary_coach_data",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.String(length=255), nullable=True),
        sa.Column("region", sa.String(length=255), nullable=True),
        sa.Column("experience_years", sa.Integer(), nullable=True),
        sa.Column("target_salary", sa.Integer(), nullable=True),
        sa.Column("current_salary", sa.Integer(), nullable=True),
        sa.Column("industry", sa.String(length=255), nullable=True),
        sa.Column("research_json", sa.Text(), nullable=True),
        sa.Column("strategy_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("salary_coach_data", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_salary_coach_data_user_id"), ["user_id"], unique=True)


def downgrade():
    with op.batch_alter_table("salary_coach_data", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_salary_coach_data_user_id"))

    op.drop_table("salary_coach_data")
