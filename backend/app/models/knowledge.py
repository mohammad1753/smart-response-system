
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
    and_,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            name="uq_knowledge_base_workspace",
        ),
        UniqueConstraint(
            "id",
            "workspace_id",
            name="uq_knowledge_base_id_workspace",
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

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default="Default Knowledge Base",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
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

    documents: Mapped[list["KnowledgeDocument"]] = relationship(
    back_populates="knowledge_base",
    primaryjoin=lambda: and_(
        KnowledgeBase.id == KnowledgeDocument.knowledge_base_id,
        KnowledgeBase.workspace_id == KnowledgeDocument.workspace_id,
    ),
    foreign_keys=lambda: [KnowledgeDocument.knowledge_base_id],
)


class FAQCategory(Base):
    __tablename__ = "faq_categories"

    __table_args__ = (
        UniqueConstraint(
            "id",
            "workspace_id",
            name="uq_faq_category_id_workspace",
        ),
        UniqueConstraint(
            "workspace_id",
            "slug",
            name="uq_faq_category_workspace_slug",
        ),
        CheckConstraint(
            "sort_order >= 0",
            name="ck_faq_category_sort_order",
        ),
        Index(
            "ix_faq_categories_workspace_active",
            "workspace_id",
            "is_active",
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

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(180),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
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

    items: Mapped[list["FAQItem"]] = relationship(
    back_populates="category",
    primaryjoin=lambda: and_(
        FAQCategory.id == FAQItem.category_id,
        FAQCategory.workspace_id == FAQItem.workspace_id,
    ),
    foreign_keys=lambda: [FAQItem.category_id],
)


class FAQItem(Base):
    __tablename__ = "faq_items"

    __table_args__ = (
        UniqueConstraint(
            "id",
            "workspace_id",
            name="uq_faq_item_id_workspace",
        ),
        ForeignKeyConstraint(
            ["category_id", "workspace_id"],
            ["faq_categories.id", "faq_categories.workspace_id"],
            name="fk_faq_item_category_workspace",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "priority >= 0",
            name="ck_faq_item_priority",
        ),
        Index(
            "ix_faq_items_workspace_active",
            "workspace_id",
            "is_active",
        ),
        Index(
            "ix_faq_items_workspace_category",
            "workspace_id",
            "category_id",
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

    category_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    question: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
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

    category: Mapped["FAQCategory | None"] = relationship(
    back_populates="items",
    primaryjoin=lambda: and_(
        FAQItem.category_id == FAQCategory.id,
        FAQItem.workspace_id == FAQCategory.workspace_id,
    ),
    foreign_keys=lambda: [FAQItem.category_id],
)


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    __table_args__ = (
        UniqueConstraint(
            "id",
            "workspace_id",
            name="uq_knowledge_document_id_workspace",
        ),
        ForeignKeyConstraint(
            ["knowledge_base_id", "workspace_id"],
            ["knowledge_bases.id", "knowledge_bases.workspace_id"],
            name="fk_document_knowledge_base_workspace",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "source_type IN ('FILE', 'TEXT')",
            name="ck_knowledge_document_source_type",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'READY', 'FAILED', 'ARCHIVED')",
            name="ck_knowledge_document_status",
        ),
        Index(
            "ix_knowledge_documents_workspace_status",
            "workspace_id",
            "status",
        ),
        Index(
            "ix_knowledge_documents_knowledge_base",
            "knowledge_base_id",
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

    knowledge_base_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    source_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    file_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    mime_type: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    storage_key: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    content_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        server_default=text("'PENDING'"),
    )

    error_message: Mapped[str | None] = mapped_column(
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

    knowledge_base: Mapped["KnowledgeBase"] = relationship(
    back_populates="documents",
    primaryjoin=lambda: and_(
        KnowledgeDocument.knowledge_base_id == KnowledgeBase.id,
        KnowledgeDocument.workspace_id == KnowledgeBase.workspace_id,
    ),
    foreign_keys=lambda: [KnowledgeDocument.knowledge_base_id],
)

    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        back_populates="document",
        primaryjoin=lambda: and_(
            KnowledgeDocument.id == KnowledgeChunk.document_id,
            KnowledgeDocument.workspace_id == KnowledgeChunk.workspace_id,
        ),
        foreign_keys=lambda: [KnowledgeChunk.document_id],
    )


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    __table_args__ = (
        UniqueConstraint(
            "id",
            "workspace_id",
            name="uq_knowledge_chunk_id_workspace",
        ),
        ForeignKeyConstraint(
            ["document_id", "workspace_id"],
            ["knowledge_documents.id", "knowledge_documents.workspace_id"],
            name="fk_knowledge_chunk_document_workspace",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_knowledge_chunk_document_index",
        ),
        CheckConstraint(
            "chunk_index >= 0",
            name="ck_knowledge_chunk_index",
        ),
        CheckConstraint(
            "token_count IS NULL OR token_count >= 0",
            name="ck_knowledge_chunk_token_count",
        ),
        Index(
            "ix_knowledge_chunks_workspace_document",
            "workspace_id",
            "document_id",
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

    document_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    token_count: Mapped[int | None] = mapped_column(
        Integer,
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

    document: Mapped["KnowledgeDocument"] = relationship(
    back_populates="chunks",
    primaryjoin=lambda: and_(
        KnowledgeChunk.document_id == KnowledgeDocument.id,
        KnowledgeChunk.workspace_id == KnowledgeDocument.workspace_id,
    ),
    foreign_keys=lambda: [KnowledgeChunk.document_id],
)
