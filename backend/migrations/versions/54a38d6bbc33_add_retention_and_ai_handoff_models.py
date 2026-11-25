
"""add retention and ai handoff models

Revision ID: 54a38d6bbc33
Revises: bf3d4cc79cc8
Create Date: 2026-11-24 11:52:36.821193
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "54a38d6bbc33"
down_revision: Union[str, Sequence[str], None] = "bf3d4cc79cc8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def inspector():
    return sa.inspect(op.get_bind())


def table_exists(table_name):
    return inspector().has_table(table_name)


def column_exists(table_name, column_name):
    if not table_exists(table_name):
        return False

    return column_name in {
        col["name"]
        for col in inspector().get_columns(table_name)
    }


def index_exists(table_name, index_name):
    if not table_exists(table_name):
        return False

    return index_name in {
        idx["name"]
        for idx in inspector().get_indexes(table_name)
    }


def unique_constraint_exists(table_name, constraint_name):
    if not table_exists(table_name):
        return False

    return constraint_name in {
        constraint["name"]
        for constraint in inspector().get_unique_constraints(table_name)
        if constraint["name"] is not None
    }


def unique_or_index_exists(table_name, name):
    return (
        unique_constraint_exists(table_name, name)
        or index_exists(table_name, name)
    )


def create_index_if_missing(name, table, columns, unique=False):
    if not index_exists(table, name):
        op.create_index(
            name,
            table,
            columns,
            unique=unique,
        )


# ---------------------------------------------------------
# Upgrade
# ---------------------------------------------------------

def upgrade() -> None:

    # =====================================================
    # 1. AI SETTINGS
    # =====================================================

    if not table_exists("ai_settings"):

        op.create_table(
            "ai_settings",

            sa.Column(
                "id",
                sa.BigInteger(),
                autoincrement=True,
                nullable=False,
            ),

            sa.Column(
                "workspace_id",
                sa.BigInteger(),
                nullable=False,
            ),

            sa.Column(
                "channel_account_id",
                sa.BigInteger(),
                nullable=True,
            ),

            sa.Column(
                "is_default",
                sa.Boolean(),
                server_default=sa.text("0"),
                nullable=False,
            ),

            # Normal column, NOT generated column.
            sa.Column(
                "default_workspace_id",
                sa.BigInteger(),
                nullable=True,
            ),

            sa.Column("is_enabled", sa.Boolean(), nullable=True),
            sa.Column("provider", sa.String(50), nullable=True),
            sa.Column("model_name", sa.String(100), nullable=True),
            sa.Column("system_prompt", sa.Text(), nullable=True),
            sa.Column("confidence_threshold", sa.Float(), nullable=True),
            sa.Column("fallback_to_human", sa.Boolean(), nullable=True),
            sa.Column("max_response_tokens", sa.Integer(), nullable=True),

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
                """
                (
                    is_default = 1
                    AND channel_account_id IS NULL
                )
                OR
                (
                    is_default = 0
                    AND channel_account_id IS NOT NULL
                )
                """,
                name="ck_ai_setting_default_account",
            ),

            sa.CheckConstraint(
                """
                confidence_threshold IS NULL
                OR (
                    confidence_threshold >= 0
                    AND confidence_threshold <= 1
                )
                """,
                name="ck_ai_setting_confidence",
            ),

            sa.CheckConstraint(
                """
                max_response_tokens IS NULL
                OR max_response_tokens > 0
                """,
                name="ck_ai_setting_max_tokens",
            ),

            sa.CheckConstraint(
                """
                (
                    is_default = 1
                    AND default_workspace_id = workspace_id
                )
                OR
                (
                    is_default = 0
                    AND default_workspace_id IS NULL
                )
                """,
                name="ck_ai_setting_default_workspace",
            ),

            sa.ForeignKeyConstraint(
                ["channel_account_id", "workspace_id"],
                [
                    "channel_accounts.id",
                    "channel_accounts.workspace_id",
                ],
                name="fk_ai_setting_channel_workspace",
                ondelete="CASCADE",
            ),

            sa.ForeignKeyConstraint(
                ["workspace_id"],
                ["workspace.id"],
                ondelete="CASCADE",
            ),

            sa.PrimaryKeyConstraint("id"),

            sa.UniqueConstraint(
                "default_workspace_id",
                name="uq_ai_setting_default_workspace",
            ),

            sa.UniqueConstraint(
                "workspace_id",
                "channel_account_id",
                name="uq_ai_setting_workspace_channel",
            ),
        )

    create_index_if_missing(
        "ix_ai_settings_workspace",
        "ai_settings",
        ["workspace_id"],
    )

    # =====================================================
    # 2. CONVERSATION ASSIGNMENTS
    # =====================================================

    if not table_exists("conversation_assignments"):

        op.create_table(
            "conversation_assignments",

            sa.Column(
                "id",
                sa.BigInteger(),
                autoincrement=True,
                nullable=False,
            ),

            sa.Column("workspace_id", sa.BigInteger(), nullable=False),
            sa.Column("conversation_id", sa.BigInteger(), nullable=False),

            sa.Column(
                "active_conversation_id",
                sa.BigInteger(),
                sa.Computed(
                    """
                    CASE
                        WHEN unassigned_at IS NULL
                        THEN conversation_id
                        ELSE NULL
                    END
                    """,
                    persisted=True,
                ),
                nullable=True,
            ),

            sa.Column("assigned_user_id", sa.BigInteger(), nullable=False),
            sa.Column("assigned_by_user_id", sa.BigInteger(), nullable=True),
            sa.Column("assignment_type", sa.String(30), nullable=False),
            sa.Column("note", sa.Text(), nullable=True),

            sa.Column(
                "assigned_at",
                sa.DateTime(),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),

            sa.Column("unassigned_at", sa.DateTime(), nullable=True),

            sa.CheckConstraint(
                "assignment_type IN ('MANUAL', 'AUTO', 'HANDOFF')",
                name="ck_assignment_type",
            ),

            sa.CheckConstraint(
                "unassigned_at IS NULL OR unassigned_at >= assigned_at",
                name="ck_assignment_dates",
            ),

            sa.ForeignKeyConstraint(
                ["assigned_by_user_id"],
                ["users.id"],
                ondelete="SET NULL",
            ),

            sa.ForeignKeyConstraint(
                ["assigned_user_id"],
                ["users.id"],
                ondelete="RESTRICT",
            ),

            sa.ForeignKeyConstraint(
                ["conversation_id", "workspace_id"],
                ["conversations.id", "conversations.workspace_id"],
                name="fk_assignment_conversation_workspace",
                ondelete="RESTRICT",
            ),

            sa.ForeignKeyConstraint(
                ["workspace_id", "assigned_user_id"],
                ["workspace_members.workspace_id", "workspace_members.user_id"],
                name="fk_assignment_workspace_member",
                ondelete="RESTRICT",
            ),

            sa.PrimaryKeyConstraint("id"),

            sa.UniqueConstraint(
                "active_conversation_id",
                name="uq_assignment_active_conversation",
            ),
        )

    create_index_if_missing(
        "ix_assignments_conversation_assigned",
        "conversation_assignments",
        ["conversation_id", "assigned_at"],
    )

    create_index_if_missing(
        "ix_assignments_workspace_user",
        "conversation_assignments",
        ["workspace_id", "assigned_user_id"],
    )

    # =====================================================
    # 3. CONVERSATION EVENTS
    # =====================================================

    if not table_exists("conversation_events"):

        op.create_table(
            "conversation_events",

            sa.Column(
                "id",
                sa.BigInteger(),
                autoincrement=True,
                nullable=False,
            ),

            sa.Column("workspace_id", sa.BigInteger(), nullable=False),
            sa.Column("conversation_id", sa.BigInteger(), nullable=False),
            sa.Column("event_type", sa.String(50), nullable=False),
            sa.Column("actor_type", sa.String(30), nullable=False),
            sa.Column("actor_user_id", sa.BigInteger(), nullable=True),
            sa.Column("details", sa.JSON(), nullable=True),

            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),

            sa.CheckConstraint(
                """
                actor_type IN (
                    'SYSTEM',
                    'AI',
                    'OPERATOR',
                    'ADMIN',
                    'CUSTOMER'
                )
                """,
                name="ck_conversation_event_actor_type",
            ),

            sa.CheckConstraint(
                """
                event_type IN (
                    'CONVERSATION_CREATED',
                    'AI_ENABLED',
                    'AI_DISABLED',
                    'HANDOFF_REQUESTED',
                    'ASSIGNED_TO_OPERATOR',
                    'OPERATOR_REPLIED',
                    'RETURNED_TO_AI',
                    'CONVERSATION_CLOSED',
                    'CONVERSATION_REOPENED'
                )
                """,
                name="ck_conversation_event_type",
            ),

            sa.ForeignKeyConstraint(
                ["actor_user_id"],
                ["users.id"],
                ondelete="SET NULL",
            ),

            sa.ForeignKeyConstraint(
                ["conversation_id", "workspace_id"],
                ["conversations.id", "conversations.workspace_id"],
                name="fk_conversation_event_workspace",
                ondelete="RESTRICT",
            ),

            sa.PrimaryKeyConstraint("id"),
        )

    create_index_if_missing(
        "ix_conversation_events_conversation_created",
        "conversation_events",
        ["conversation_id", "created_at"],
    )

    create_index_if_missing(
        "ix_conversation_events_workspace_created",
        "conversation_events",
        ["workspace_id", "created_at"],
    )

    # =====================================================
    # 4. MESSAGE UNIQUE CONSTRAINT
    # =====================================================

    if not unique_or_index_exists(
        "messages",
        "uq_message_id_workspace",
    ):

        op.create_unique_constraint(
            "uq_message_id_workspace",
            "messages",
            ["id", "workspace_id"],
        )

    # =====================================================
    # 5. AI RUNS
    # =====================================================

    if not table_exists("ai_runs"):

        op.create_table(
            "ai_runs",

            sa.Column(
                "id",
                sa.BigInteger(),
                autoincrement=True,
                nullable=False,
            ),

            sa.Column("workspace_id", sa.BigInteger(), nullable=False),
            sa.Column("conversation_id", sa.BigInteger(), nullable=False),
            sa.Column("message_id", sa.BigInteger(), nullable=True),

            sa.Column("provider", sa.String(50), nullable=False),
            sa.Column("model_name", sa.String(100), nullable=False),

            sa.Column(
                "status",
                sa.String(30),
                server_default="PENDING",
                nullable=False,
            ),

            sa.Column("input_tokens", sa.Integer(), nullable=True),
            sa.Column("output_tokens", sa.Integer(), nullable=True),
            sa.Column("total_tokens", sa.Integer(), nullable=True),
            sa.Column("confidence_score", sa.Float(), nullable=True),
            sa.Column("latency_ms", sa.Integer(), nullable=True),
            sa.Column("error_code", sa.String(100), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),

            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),

            sa.CheckConstraint(
                """
                status IN (
                    'PENDING',
                    'PROCESSING',
                    'COMPLETED',
                    'FAILED',
                    'HANDOFF'
                )
                """,
                name="ck_ai_run_status",
            ),

            sa.CheckConstraint(
                """
                confidence_score IS NULL
                OR (
                    confidence_score >= 0
                    AND confidence_score <= 1
                )
                """,
                name="ck_ai_run_confidence",
            ),

            sa.CheckConstraint(
                "input_tokens IS NULL OR input_tokens >= 0",
                name="ck_ai_run_input_tokens",
            ),

            sa.CheckConstraint(
                "latency_ms IS NULL OR latency_ms >= 0",
                name="ck_ai_run_latency",
            ),

            sa.CheckConstraint(
                "output_tokens IS NULL OR output_tokens >= 0",
                name="ck_ai_run_output_tokens",
            ),

            sa.CheckConstraint(
                "total_tokens IS NULL OR total_tokens >= 0",
                name="ck_ai_run_total_tokens",
            ),

            sa.ForeignKeyConstraint(
                ["conversation_id", "workspace_id"],
                ["conversations.id", "conversations.workspace_id"],
                name="fk_ai_run_conversation_workspace",
                ondelete="RESTRICT",
            ),

            sa.ForeignKeyConstraint(
                ["message_id", "workspace_id"],
                ["messages.id", "messages.workspace_id"],
                name="fk_ai_run_message_workspace",
                ondelete="RESTRICT",
            ),

            sa.ForeignKeyConstraint(
                ["workspace_id"],
                ["workspace.id"],
                ondelete="RESTRICT",
            ),

            sa.PrimaryKeyConstraint("id"),
        )

    # AI runs indexes

    create_index_if_missing(
        "ix_ai_runs_conversation_created",
        "ai_runs",
        ["conversation_id", "created_at"],
    )

    create_index_if_missing(
        "ix_ai_runs_message",
        "ai_runs",
        ["message_id"],
    )

    create_index_if_missing(
        "ix_ai_runs_workspace_created",
        "ai_runs",
        ["workspace_id", "created_at"],
    )

    create_index_if_missing(
        "ix_ai_runs_workspace_status",
        "ai_runs",
        ["workspace_id", "status"],
    )

    # =====================================================
    # 6. CONVERSATION COLUMNS
    # =====================================================

    if not column_exists("conversations", "response_mode"):

        op.add_column(
            "conversations",
            sa.Column(
                "response_mode",
                sa.String(20),
                server_default="AI",
                nullable=False,
            ),
        )

    if not column_exists("conversations", "handoff_reason"):

        op.add_column(
            "conversations",
            sa.Column(
                "handoff_reason",
                sa.String(100),
                nullable=True,
            ),
        )

    if not column_exists("conversations", "handed_off_at"):

        op.add_column(
            "conversations",
            sa.Column(
                "handed_off_at",
                sa.DateTime(),
                nullable=True,
            ),
        )

    # =====================================================
    # 7. CONVERSATION INDEXES
    # =====================================================

    old_index = "uq_conversation_customer_channel_account"

    if index_exists("conversations", old_index):

        op.drop_index(
            old_index,
            table_name="conversations",
        )

    create_index_if_missing(
        "ix_conversations_workspace_mode_status",
        "conversations",
        ["workspace_id", "response_mode", "status"],
    )


# ---------------------------------------------------------
# Downgrade
# ---------------------------------------------------------

def downgrade() -> None:

    # =====================================================
    # 1. CONVERSATIONS
    # =====================================================

    if index_exists(
        "conversations",
        "ix_conversations_workspace_mode_status",
    ):
        op.drop_index(
            "ix_conversations_workspace_mode_status",
            table_name="conversations",
        )

    if table_exists("conversations"):

        if not index_exists(
            "conversations",
            "uq_conversation_customer_channel_account",
        ):
            op.create_index(
                "uq_conversation_customer_channel_account",
                "conversations",
                ["customer_identity_id", "channel_account_id"],
                unique=True,
            )

        for column in (
            "handed_off_at",
            "handoff_reason",
            "response_mode",
        ):
            if column_exists("conversations", column):
                op.drop_column("conversations", column)

    # =====================================================
    # 2. AI RUNS
    # =====================================================

    if table_exists("ai_runs"):
        op.drop_table("ai_runs")

    # =====================================================
    # 3. MESSAGES UNIQUE
    # =====================================================

    if unique_or_index_exists(
        "messages",
        "uq_message_id_workspace",
    ):
        op.drop_constraint(
            "uq_message_id_workspace",
            "messages",
            type_="unique",
        )

    # =====================================================
    # 4. CONVERSATION EVENTS
    # =====================================================

    if table_exists("conversation_events"):
        op.drop_table("conversation_events")

    # =====================================================
    # 5. CONVERSATION ASSIGNMENTS
    # =====================================================

    if table_exists("conversation_assignments"):
        op.drop_table("conversation_assignments")

    # =====================================================
    # 6. AI SETTINGS
    # =====================================================

    if table_exists("ai_settings"):
        op.drop_table("ai_settings")
