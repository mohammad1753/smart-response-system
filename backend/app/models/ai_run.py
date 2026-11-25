
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    String,
    Integer,
    Float,
    Text,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    CheckConstraint,
    Index,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AIRun(Base):
    __tablename__ = "ai_runs"

    __table_args__ = (
        ForeignKeyConstraint(
            ["conversation_id", "workspace_id"],
            [
                "conversations.id",
                "conversations.workspace_id",
            ],
            name="fk_ai_run_conversation_workspace",
            ondelete="RESTRICT",
        ),

        ForeignKeyConstraint(
            ["message_id", "workspace_id"],
            ["messages.id", "messages.workspace_id"],
            name="fk_ai_run_message_workspace",
            ondelete="RESTRICT",
        ),

        CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'COMPLETED', "
            "'FAILED', 'HANDOFF')",
            name="ck_ai_run_status",
        ),

        CheckConstraint(
            "input_tokens IS NULL OR input_tokens >= 0",
            name="ck_ai_run_input_tokens",
        ),

        CheckConstraint(
            "output_tokens IS NULL OR output_tokens >= 0",
            name="ck_ai_run_output_tokens",
        ),

        CheckConstraint(
            "total_tokens IS NULL OR total_tokens >= 0",
            name="ck_ai_run_total_tokens",
        ),

        CheckConstraint(
            "confidence_score IS NULL OR "
            "(confidence_score >= 0 AND confidence_score <= 1)",
            name="ck_ai_run_confidence",
        ),

        CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0",
            name="ck_ai_run_latency",
        ),

        Index(
            "ix_ai_runs_conversation_created",
            "conversation_id",
            "created_at",
        ),

        Index(
            "ix_ai_runs_workspace_created",
            "workspace_id",
            "created_at",
        ),

        Index(
            "ix_ai_runs_workspace_status",
            "workspace_id",
            "status",
        ),

        Index(
            "ix_ai_runs_message",
            "message_id",
        ),
        Index(
            "ix_ai_runs_workspace_status_created",
            "workspace_id",
            "status",
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
        ForeignKey("workspace.id", ondelete="RESTRICT"),
        nullable=False,
    )

    conversation_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    message_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
        server_default="PENDING",
        nullable=False,
    )

    input_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    output_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    total_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    confidence_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    error_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )