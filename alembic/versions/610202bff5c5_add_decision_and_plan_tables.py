"""add_decision_and_plan_tables

Revision ID: 610202bff5c5
Revises: b10db4e3de18
Create Date: 2025-06-19 00:06:20.959604

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '610202bff5c5'
down_revision: Union[str, None] = 'b10db4e3de18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('decisions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('context_md', sa.Text(), nullable=True),
        sa.Column('decision_md', sa.Text(), nullable=True),
        sa.Column('consequences_md', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('PROPOSED', 'ACCEPTED', 'REJECTED', 'SUPERSEDED', name='decisionstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_decisions_id'), 'decisions', ['id'], unique=False)

    op.create_table('task_priorities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'task_id', name='_project_task_uc'),
        sa.UniqueConstraint('task_id')
    )
    op.create_index(op.f('ix_task_priorities_id'), 'task_priorities', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_task_priorities_id'), table_name='task_priorities')
    op.drop_table('task_priorities')
    op.drop_index(op.f('ix_decisions_id'), table_name='decisions')
    op.drop_table('decisions')
    sa.Enum(name='decisionstatus').drop(op.get_bind(), checkfirst=False)
