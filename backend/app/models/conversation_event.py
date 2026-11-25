
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    String,
    DateTime,
    ForeignKeyConstraint,
    ForeignKey,
    CheckConstraint,
    Index,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ConversationEvent(Base):
    __tablename__ = "conversation_events"

    __table_args__ = (
        ForeignKeyConstraint(
            ["conversation_id", "workspace_id"],
            [
                "conversations.id",
                "conversations.workspace_id",
            ],
            name="fk_conversation_event_workspace",
            ondelete="RESTRICT",
        ),

        CheckConstraint(
            "event_type IN ("
            "'CONVERSATION_CREATED', "
            "'AI_ENABLED', "
            "'AI_DISABLED', "
            "'HANDOFF_REQUESTED', "
            "'ASSIGNED_TO_OPERATOR', "
            "'OPERATOR_REPLIED', "
            "'RETURNED_TO_AI', "
            "'CONVERSATION_CLOSED', "
            "'CONVERSATION_REOPENED'"
            ")",
            name="ck_conversation_event_type",
        ),

        CheckConstraint(
            "actor_type IN ("
            "'SYSTEM', 'AI', 'OPERATOR', 'ADMIN', 'CUSTOMER'"
            ")",
            name="ck_conversation_event_actor_type",
        ),

        Index(
            "ix_conversation_events_conversation_created",
            "conversation_id",
            "created_at",
        ),

        Index(
            "ix_conversation_events_workspace_created",
            "workspace_id",
            "created_at",
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

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    actor_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    actor_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    details: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )