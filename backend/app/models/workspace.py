from sqlalchemy import(BigInteger, String, Boolean, Integer, DateTime,CheckConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from datetime import datetime

class Workspace(Base):
    __tablename__ = "workspace"
    __table_args__= (CheckConstraint("retention_days > 0", name="ck_workspaces_retention_days_positive",),)

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
        )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    slug: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    retention_days: Mapped[int] = mapped_column(
        Integer,
        default=1095,
        server_default="1095",
        nullable=False,
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
