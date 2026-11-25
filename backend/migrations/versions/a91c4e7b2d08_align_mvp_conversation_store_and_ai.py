"""align mvp conversation store and ai

Revision ID: a91c4e7b2d08
Revises: 3113ca25127d
Create Date: 2026-11-24

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a91c4e7b2d08"
down_revision: Union[str, Sequence[str], None] = "3113ca25127d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(
        "ix_conversations_workspace_mode_status",
        table_name="conversations",
    )
    op.drop_constraint(
        "ck_conversation_response_mode",
        "conversations",
        type_="check",
    )
    op.drop_constraint(
        "ck_conversation_status",
        "conversations",
        type_="check",
    )

    op.execute(
        sa.text(
            """
            UPDATE conversations
            SET status = CASE
                WHEN status = 'CLOSED' THEN 'CLOSED'
                WHEN response_mode = 'HUMAN'
                    AND assigned_user_id IS NOT NULL THEN 'HUMAN_ACTIVE'
                WHEN response_mode = 'HUMAN' THEN 'HUMAN_REQUIRED'
                ELSE 'AI_ACTIVE'
            END
            """
        )
    )

    op.alter_column(
        "conversations",
        "status",
        existing_type=sa.String(length=30),
        existing_nullable=False,
        server_default="AI_ACTIVE",
    )
    op.drop_column("conversations", "is_ai_enabled")
    op.drop_column("conversations", "response_mode")
    op.create_check_constraint(
        "ck_conversation_status",
        "conversations",
        "status IN ('AI_ACTIVE', 'HUMAN_REQUIRED', 'HUMAN_ACTIVE', 'CLOSED')",
    )

    op.add_column(
        "ai_settings",
        sa.Column("tone", sa.String(length=30), nullable=True),
    )
    op.add_column(
        "ai_settings",
        sa.Column("response_length", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "ai_settings",
        sa.Column(
            "unknown_answer_behavior",
            sa.String(length=30),
            nullable=True,
        ),
    )
    op.add_column(
        "ai_settings",
        sa.Column("handoff_message", sa.Text(), nullable=True),
    )
    op.add_column(
        "ai_settings",
        sa.Column("welcome_message", sa.Text(), nullable=True),
    )
    op.add_column(
        "ai_settings",
        sa.Column("response_scope", sa.Text(), nullable=True),
    )
    op.create_check_constraint(
        "ck_ai_setting_tone",
        "ai_settings",
        "tone IS NULL OR tone IN ('FORMAL', 'FRIENDLY', 'NEUTRAL')",
    )
    op.create_check_constraint(
        "ck_ai_setting_response_length",
        "ai_settings",
        "response_length IS NULL OR "
        "response_length IN ('SHORT', 'MEDIUM', 'LONG')",
    )
    op.create_check_constraint(
        "ck_ai_setting_unknown_behavior",
        "ai_settings",
        "unknown_answer_behavior IS NULL OR unknown_answer_behavior IN "
        "('ASK_FOLLOW_UP', 'HANDOFF', 'ADMIT_UNKNOWN')",
    )

    op.create_table(
        "store_profiles",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.BigInteger(), nullable=False),
        sa.Column("contact_phone", sa.String(length=30), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("working_hours", sa.Text(), nullable=True),
        sa.Column("shipping_policy", sa.Text(), nullable=True),
        sa.Column("warranty_policy", sa.Text(), nullable=True),
        sa.Column("return_policy", sa.Text(), nullable=True),
        sa.Column("general_info", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspace.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", name="uq_store_profile_workspace"),
    )

    op.create_table(
        "store_api_connections",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.BigInteger(), nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=False),
        sa.Column("credentials_encrypted", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column("last_connected_at", sa.DateTime(), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("last_error_at", sa.DateTime(), nullable=True),
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
            "status IN ('PENDING', 'CONNECTED', 'DISCONNECTED', 'ERROR')",
            name="ck_store_api_connection_status",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspace.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            name="uq_store_api_connection_workspace",
        ),
    )


def downgrade() -> None:
    op.drop_table("store_api_connections")
    op.drop_table("store_profiles")

    op.drop_constraint(
        "ck_ai_setting_unknown_behavior",
        "ai_settings",
        type_="check",
    )
    op.drop_constraint(
        "ck_ai_setting_response_length",
        "ai_settings",
        type_="check",
    )
    op.drop_constraint(
        "ck_ai_setting_tone",
        "ai_settings",
        type_="check",
    )
    op.drop_column("ai_settings", "response_scope")
    op.drop_column("ai_settings", "welcome_message")
    op.drop_column("ai_settings", "handoff_message")
    op.drop_column("ai_settings", "unknown_answer_behavior")
    op.drop_column("ai_settings", "response_length")
    op.drop_column("ai_settings", "tone")

    op.drop_constraint(
        "ck_conversation_status",
        "conversations",
        type_="check",
    )
    op.add_column(
        "conversations",
        sa.Column(
            "response_mode",
            sa.String(length=20),
            server_default="AI",
            nullable=False,
        ),
    )
    op.add_column(
        "conversations",
        sa.Column(
            "is_ai_enabled",
            sa.Boolean(),
            server_default=sa.text("1"),
            nullable=False,
        ),
    )
    op.execute(
        sa.text(
            """
            UPDATE conversations
            SET
                response_mode = CASE
                    WHEN status IN ('HUMAN_REQUIRED', 'HUMAN_ACTIVE') THEN 'HUMAN'
                    ELSE 'AI'
                END,
                is_ai_enabled = CASE
                    WHEN status = 'AI_ACTIVE' THEN 1
                    ELSE 0
                END,
                status = CASE
                    WHEN status = 'CLOSED' THEN 'CLOSED'
                    WHEN status = 'HUMAN_REQUIRED' THEN 'PENDING'
                    ELSE 'OPEN'
                END
            """
        )
    )
    op.alter_column(
        "conversations",
        "status",
        existing_type=sa.String(length=30),
        existing_nullable=False,
        server_default="OPEN",
    )
    op.create_check_constraint(
        "ck_conversation_status",
        "conversations",
        "status IN ('OPEN', 'PENDING', 'CLOSED')",
    )
    op.create_check_constraint(
        "ck_conversation_response_mode",
        "conversations",
        "response_mode IN ('AI', 'HUMAN')",
    )
    op.create_index(
        "ix_conversations_workspace_mode_status",
        "conversations",
        ["workspace_id", "response_mode", "status"],
        unique=False,
    )
