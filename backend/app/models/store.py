from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class StoreProfile(Base):
    __tablename__ = "store_profiles"

    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            name="uq_store_profile_workspace",
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

    contact_phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    contact_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    working_hours: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    shipping_policy: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    warranty_policy: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    return_policy: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    general_info: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )


class StoreApiConnection(Base):
    __tablename__ = "store_api_connections"

    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            name="uq_store_api_connection_workspace",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'CONNECTED', 'DISCONNECTED', 'ERROR')",
            name="ck_store_api_connection_status",
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

    base_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    credentials_encrypted: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
        server_default="PENDING",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
    )

    last_connected_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    last_error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    last_error_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
