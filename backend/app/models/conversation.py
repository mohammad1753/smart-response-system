
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    CheckConstraint,
    func,
    ForeignKeyConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    __table_args__ = (
    

    UniqueConstraint(
        "id",
        "workspace_id",
        name="uq_conversation_id_workspace",
    ),

    UniqueConstraint(
        "id",
        "workspace_id",
        "channel_account_id",
        name="uq_conversation_id_workspace_channel",
    ),

    ForeignKeyConstraint(
        ["customer_identity_id", "workspace_id"],
        ["customer_identities.id", "customer_identities.workspace_id"],
        name="fk_conversation_identity_workspace",
        ondelete="RESTRICT",
    ),

    ForeignKeyConstraint(
        ["channel_account_id", "workspace_id"],
        ["channel_accounts.id", "channel_accounts.workspace_id"],
        name="fk_conversation_channel_workspace",
        ondelete="RESTRICT",
    ),

    CheckConstraint(
        "status IN ('AI_ACTIVE', 'HUMAN_REQUIRED', 'HUMAN_ACTIVE', 'CLOSED')",
        name="ck_conversation_status",
    ),

    Index(
        "ix_conversations_workspace_status",
        "workspace_id",
        "status",
    ),

    Index(
        "ix_conversations_workspace_last_message",
        "workspace_id",
        "last_message_at",
    ),

    Index(
        "ix_conversations_workspace_created",
        "workspace_id",
        "created_at",
    ),
    Index(
        "ix_conversations_workspace_channel_created",
        "workspace_id",
        "channel_account_id",
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

    customer_identity_id: Mapped[int] = mapped_column(
        BigInteger,
        
        nullable=False,
    )

    channel_account_id: Mapped[int] = mapped_column(
        BigInteger,
        
        nullable=False,
    )

    assigned_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="AI_ACTIVE",
        server_default="AI_ACTIVE",
        nullable=False,
    )

    handoff_reason: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    handed_off_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime,
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