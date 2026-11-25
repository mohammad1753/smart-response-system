
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Index,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ChannelAccount(Base):
    __tablename__ = "channel_accounts"

    __table_args__ = (
    UniqueConstraint(
        "id",
        "workspace_id",
        name="uq_channel_account_id_workspace",
    ),
    UniqueConstraint(
        "workspace_id",
        "channel_id",
        "external_account_id",
        name="uq_channel_account_external_id",
    ),
    CheckConstraint(
        "status IN ('PENDING', 'CONNECTED', 'DISCONNECTED', 'ERROR')",
        name="ck_channel_account_status",
    ),
    Index(
        "ix_channel_accounts_workspace_status",
        "workspace_id",
        "status",
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
        index=True,
    )

    channel_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("channels.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    account_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    external_account_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    credentials_encrypted: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
        server_default="PENDING",
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("1"),
        nullable=False,
    )

    last_connected_at: Mapped[datetime | None] = mapped_column(
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
    