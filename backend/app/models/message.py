
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    String,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    ForeignKeyConstraint,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Message(Base):
    __tablename__ = "messages"

    __table_args__ = (
        UniqueConstraint(
            "id",
            "workspace_id",
            name="uq_message_id_workspace",
        ),
        UniqueConstraint(
            "channel_account_id",
            "external_message_id",
            name="uq_message_channel_external_id",
        ),
        CheckConstraint(
            "direction IN ('INBOUND', 'OUTBOUND')",
            name="ck_message_direction",
        ),
        CheckConstraint(
            "sender_type IN ('CUSTOMER', 'AI', 'OPERATOR', 'SYSTEM')",
            name="ck_message_sender_type",
        ),
        CheckConstraint(
            "message_type IN ('TEXT', 'IMAGE', 'VIDEO', 'AUDIO', "
            "'DOCUMENT', 'STICKER', 'OTHER')",
            name="ck_message_type",
        ),
        CheckConstraint(
            "status IN ('RECEIVED', 'PENDING', 'SENT', 'FAILED')",
            name="ck_message_status",
        ),
        ForeignKeyConstraint(
            ["conversation_id", "workspace_id", "channel_account_id"],
            [
                "conversations.id",
                "conversations.workspace_id",
                "conversations.channel_account_id",
            ],
            name="fk_message_conversation_workspace_channel",
            ondelete="RESTRICT",
        ),

        ForeignKeyConstraint(
            ["channel_account_id", "workspace_id"],
            ["channel_accounts.id", "channel_accounts.workspace_id"],
            name="fk_message_channel_workspace",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_messages_conversation_created",
            "conversation_id",
            "created_at",
        ),
        Index(
            "ix_messages_workspace_created",
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
        ForeignKey("workspace.id", ondelete="RESTRICT"),
        nullable=False,
    )

    conversation_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    channel_account_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    external_message_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    direction: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    sender_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    message_type: Mapped[str] = mapped_column(
        String(30),
        default="TEXT",
        server_default="TEXT",
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )