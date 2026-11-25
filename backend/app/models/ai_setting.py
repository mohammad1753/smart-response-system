
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    String,
    Boolean,
    DateTime,
    Text,
    Integer,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    UniqueConstraint,
    CheckConstraint,
    Index,
    func,
    text,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AISetting(Base):
    __tablename__ = "ai_settings"

    __table_args__ = (
        ForeignKeyConstraint(
            ["channel_account_id", "workspace_id"],
            [
                "channel_accounts.id",
                "channel_accounts.workspace_id",
            ],
            name="fk_ai_setting_channel_workspace",
            ondelete="CASCADE",
        ),

        UniqueConstraint(
            "default_workspace_id",
            name="uq_ai_setting_default_workspace",
        ),

        UniqueConstraint(
            "workspace_id",
            "channel_account_id",
            name="uq_ai_setting_workspace_channel",
        ),

        CheckConstraint(
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

        CheckConstraint(
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

        CheckConstraint(
            """
            confidence_threshold IS NULL
            OR (
                confidence_threshold >= 0
                AND confidence_threshold <= 1
            )
            """,
            name="ck_ai_setting_confidence",
        ),

        CheckConstraint(
            """
            max_response_tokens IS NULL
            OR max_response_tokens > 0
            """,
            name="ck_ai_setting_max_tokens",
        ),

        CheckConstraint(
            "tone IS NULL OR tone IN ('FORMAL', 'FRIENDLY', 'NEUTRAL')",
            name="ck_ai_setting_tone",
        ),

        CheckConstraint(
            "response_length IS NULL OR "
            "response_length IN ('SHORT', 'MEDIUM', 'LONG')",
            name="ck_ai_setting_response_length",
        ),

        CheckConstraint(
            "unknown_answer_behavior IS NULL OR unknown_answer_behavior IN "
            "('ASK_FOLLOW_UP', 'HANDOFF', 'ADMIT_UNKNOWN')",
            name="ck_ai_setting_unknown_behavior",
        ),

        Index(
            "ix_ai_settings_workspace",
            "workspace_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    workspace_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("workspace.id", ondelete="CASCADE"),
        nullable=False,
    )

    channel_account_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )

    # معمولی است؛ دیگر Generated Column نیست.
    default_workspace_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    is_enabled: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    provider: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    model_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    system_prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    confidence_threshold: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    fallback_to_human: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    max_response_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    tone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    response_length: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    unknown_answer_behavior: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    handoff_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    welcome_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    response_scope: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


@event.listens_for(AISetting, "before_insert")
@event.listens_for(AISetting, "before_update")
def update_default_workspace_id(mapper, connection, target):
    if target.is_default:
        target.default_workspace_id = target.workspace_id
    else:
        target.default_workspace_id = None
