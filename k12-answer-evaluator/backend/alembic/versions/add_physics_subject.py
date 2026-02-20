"""add physics to subject enum

Revision ID: add_physics_subject
Revises: 
Create Date: 2026-02-19
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_physics_subject'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # PostgreSQL requires ALTER TYPE to add enum values
    op.execute("ALTER TYPE subject ADD VALUE IF NOT EXISTS 'physics'")


def downgrade():
    # PostgreSQL does not support removing enum values natively.
    # To fully revert: recreate the enum without 'physics'.
    # For safety we just leave the value in place on downgrade.
    pass
