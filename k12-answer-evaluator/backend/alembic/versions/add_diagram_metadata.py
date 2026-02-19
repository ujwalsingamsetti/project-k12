"""add diagram metadata to submissions

Revision ID: add_diagram_metadata
Revises: 
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'add_diagram_metadata'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('answer_submissions', sa.Column('diagram_metadata', postgresql.JSON, nullable=True))


def downgrade():
    op.drop_column('answer_submissions', 'diagram_metadata')
