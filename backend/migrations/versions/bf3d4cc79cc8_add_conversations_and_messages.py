
"""add conversations and messages

Revision ID: bf3d4cc79cc8
Revises: b50a78e3c5da
Create Date: 2026-11-23 14:51:38.938614
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "bf3d4cc79cc8"
down_revision: Union[str, Sequence[str], None] = "b50a78e3c5da"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.BigInteger(), nullable=False),
        sa.Column("customer_identity_id", sa.BigInteger(), nullable=False),
        sa.Column("channel_account_id", sa.BigInteger(), nullable=False),
        sa.Column("assigned_user_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default="OPEN",
            nullable=False,
        ),
        sa.Column(
            "is_ai_enabled",
            sa.Boolean(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('OPEN', 'PENDING', 'CLOSED')",
            name="ck_conversation_status",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["channel_account_id", "workspace_id"],
            ["channel_accounts.id", "channel_accounts.workspace_id"],
            name="fk_conversation_channel_workspace",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["customer_identity_id", "workspace_id"],
            ["customer_identities.id", "customer_identities.workspace_id"],
            name="fk_conversation_identity_workspace",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspace.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "customer_identity_id",
            "channel_account_id",
            name="uq_conversation_customer_channel_account",
        ),
        sa.UniqueConstraint(
            "id",
            "workspace_id",
            "channel_account_id",
            name="uq_conversation_id_workspace_channel",
        ),
        sa.UniqueConstraint(
            "id",
            "workspace_id",
            name="uq_conversation_id_workspace",
        ),
    )

    op.create_index(
        "ix_conversations_workspace_last_message",
        "conversations",
        ["workspace_id", "last_message_at"],
        unique=False,
    )
    op.create_index(
        "ix_conversations_workspace_status",
        "conversations",
        ["workspace_id", "status"],
        unique=False,
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.BigInteger(), nullable=False),
        sa.Column("conversation_id", sa.BigInteger(), nullable=False),
        sa.Column("channel_account_id", sa.BigInteger(), nullable=False),
        sa.Column("external_message_id", sa.String(length=255), nullable=True),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column("sender_type", sa.String(length=30), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column(
            "message_type",
            sa.String(length=30),
            server_default="TEXT",
            nullable=False,
        ),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "direction IN ('INBOUND', 'OUTBOUND')",
            name="ck_message_direction",
        ),
        sa.CheckConstraint(
            "message_type IN ('TEXT', 'IMAGE', 'VIDEO', 'AUDIO', "
            "'DOCUMENT', 'STICKER', 'OTHER')",
            name="ck_message_type",
        ),
        sa.CheckConstraint(
            "sender_type IN ('CUSTOMER', 'AI', 'OPERATOR', 'SYSTEM')",
            name="ck_message_sender_type",
        ),
        sa.CheckConstraint(
            "status IN ('RECEIVED', 'PENDING', 'SENT', 'FAILED')",
            name="ck_message_status",
        ),
        sa.ForeignKeyConstraint(
            ["channel_account_id", "workspace_id"],
            ["channel_accounts.id", "channel_accounts.workspace_id"],
            name="fk_message_channel_workspace",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id", "workspace_id", "channel_account_id"],
            [
                "conversations.id",
                "conversations.workspace_id",
                "conversations.channel_account_id",
            ],
            name="fk_message_conversation_workspace_channel",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspace.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "channel_account_id",
            "external_message_id",
            name="uq_message_channel_external_id",
        ),
    )

    op.create_index(
        "ix_messages_conversation_created",
        "messages",
        ["conversation_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_messages_workspace_created",
        "messages",
        ["workspace_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("messages")

    op.drop_index(
        "ix_conversations_workspace_status",
        table_name="conversations",
    )
    op.drop_index(
        "ix_conversations_workspace_last_message",
        table_name="conversations",
    )

    op.drop_table("conversations")
