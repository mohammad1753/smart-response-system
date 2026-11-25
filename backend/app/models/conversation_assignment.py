
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    String,
    Text,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    CheckConstraint,
    Index,
    Computed,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ConversationAssignment(Base):
    __tablename__ = "conversation_assignments"

    __table_args__ = (
        ForeignKeyConstraint(
            ["conversation_id", "workspace_id"],
            [
                "conversations.id",
                "conversations.workspace_id",
            ],
            name="fk_assignment_conversation_workspace",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["workspace_id", "assigned_user_id"],
            [
                "workspace_members.workspace_id",
                "workspace_members.user_id",
            ],
            name="fk_assignment_workspace_member",
            ondelete="RESTRICT",
        ),

        UniqueConstraint(
            "active_conversation_id",
            name="uq_assignment_active_conversation",
        ),

        CheckConstraint(
            "assignment_type IN ('MANUAL', 'AUTO', 'HANDOFF')",
            name="ck_assignment_type",
        ),

        CheckConstraint(
            "unassigned_at IS NULL OR unassigned_at >= assigned_at",
            name="ck_assignment_dates",
        ),

        Index(
            "ix_assignments_conversation_assigned",
            "conversation_id",
            "assigned_at",
        ),

        Index(
            "ix_assignments_workspace_user",
            "workspace_id",
            "assigned_user_id",
        ),
        Index(
            "ix_assignments_workspace_user_assigned",
            "workspace_id",
            "assigned_user_id",
            "assigned_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    workspace_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    conversation_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    active_conversation_id: Mapped[int | None] = mapped_column(
        BigInteger,
        Computed(
            """
            CASE
                WHEN unassigned_at IS NULL THEN conversation_id
                ELSE NULL
            END
            """,
            persisted=True,
        ),
        nullable=True,
    )

    assigned_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    assigned_by_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    assignment_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    unassigned_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )