
"""add reporting indexes

Revision ID: 8d2f6c91a4b7
Revises: c7e91a4b2f60
Create Date: 2026-11-24
"""

from typing import Sequence, Union

from alembic import op


revision: str = "8d2f6c91a4b7"
down_revision: Union[str, Sequence[str], None] = "c7e91a4b2f60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_conversations_workspace_created",
        "conversations",
        ["workspace_id", "created_at"],
        unique=False,
    )

    op.create_index(
        "ix_conversations_workspace_channel_created",
        "conversations",
        ["workspace_id", "channel_account_id", "created_at"],
        unique=False,
    )

    op.create_index(
        "ix_ai_runs_workspace_status_created",
        "ai_runs",
        ["workspace_id", "status", "created_at"],
        unique=False,
    )

    op.create_index(
        "ix_assignments_workspace_user_assigned",
        "conversation_assignments",
        ["workspace_id", "assigned_user_id", "assigned_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_assignments_workspace_user_assigned",
        table_name="conversation_assignments",
    )

    op.drop_index(
        "ix_ai_runs_workspace_status_created",
        table_name="ai_runs",
    )

    op.drop_index(
        "ix_conversations_workspace_channel_created",
        table_name="conversations",
    )

    op.drop_index(
        "ix_conversations_workspace_created",
        table_name="conversations",
    )
