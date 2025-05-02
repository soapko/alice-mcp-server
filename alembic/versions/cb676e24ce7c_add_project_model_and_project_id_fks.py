"""Add Project model and project_id FKs

Revision ID: cb676e24ce7c
Revises: 
Create Date: 2025-05-02 13:41:50.585924

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cb676e24ce7c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the projects table
    op.create_table('projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)
    
    # Add project_id columns (initially nullable for data migration)
    op.add_column('epics', sa.Column('project_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_epics_project_id', 'epics', 'projects', ['project_id'], ['id'])
    
    op.add_column('tasks', sa.Column('project_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_tasks_project_id', 'tasks', 'projects', ['project_id'], ['id'])
    
    # Create "default" project
    default_project = """
    INSERT INTO projects (name) VALUES ('default');
    """
    op.execute(default_project)
    
    # Update existing tasks and epics to point to the default project
    op.execute("""
    UPDATE epics 
    SET project_id = (SELECT id FROM projects WHERE name = 'default')
    WHERE project_id IS NULL;
    """)
    
    op.execute("""
    UPDATE tasks 
    SET project_id = (SELECT id FROM projects WHERE name = 'default')
    WHERE project_id IS NULL;
    """)
    
    # Make project_id non-nullable now that all records have a value
    op.alter_column('epics', 'project_id', nullable=False)
    op.alter_column('tasks', 'project_id', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Make columns nullable again for removal
    op.alter_column('epics', 'project_id', nullable=True)
    op.alter_column('tasks', 'project_id', nullable=True)
    
    # Drop foreign keys and columns
    op.drop_constraint('fk_tasks_project_id', 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'project_id')
    
    op.drop_constraint('fk_epics_project_id', 'epics', type_='foreignkey')
    op.drop_column('epics', 'project_id')
    
    # Drop the projects table last
    op.drop_index(op.f('ix_projects_id'), table_name='projects')
    op.drop_table('projects')
