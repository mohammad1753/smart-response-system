
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    String,
    DateTime,
    ForeignKeyConstraint,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CustomerIdentity(Base):
    __tablename__ = "customer_identities"

    __table_args__ = (
        UniqueConstraint(
    "id",
    "workspace_id",
    name="uq_customer_identity_id_workspace",
    ),
        ForeignKeyConstraint(
            ["customer_id", "workspace_id"],
            ["customers.id", "customers.workspace_id"],
            name="fk_identity_customer_workspace",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["channel_account_id", "workspace_id"],
            ["channel_accounts.id", "channel_accounts.workspace_id"],
            name="fk_identity_channel_workspace",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "channel_account_id",
            "external_user_id",
            name="uq_channel_external_user",
        ),
        Index(
            "ix_customer_identities_customer",
            "customer_id",
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

    customer_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    channel_account_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    external_user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    display_name: Mapped[str | None] = mapped_column(
        String(150),
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