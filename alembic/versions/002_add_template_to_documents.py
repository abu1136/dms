"""Add template_id to documents table

Revision ID: 002
Revises: 001
Create Date: 2026-01-31 21:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add template_id column
    op.add_column('documents', sa.Column('template_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_documents_template_id',
        'documents',
        'document_templates',
        ['template_id'],
        ['id']
    )
    
    # Drop the template_name column if it exists
    try:
        op.drop_column('documents', 'template_name')
    except Exception:
        pass


def downgrade() -> None:
    # Drop foreign key
    try:
        op.drop_constraint('fk_documents_template_id', 'documents', type_='foreignkey')
    except Exception:
        pass
    
    # Drop template_id column
    op.drop_column('documents', 'template_id')
    
    # Re-add template_name column
    op.add_column('documents', sa.Column('template_name', sa.String(100), nullable=False, server_default='default'))
