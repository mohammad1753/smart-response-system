
"""add knowledge base and faq

Revision ID: c7e91a4b2f60
Revises: 54a38d6bbc33
Create Date: 2026-11-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7e91a4b2f60"
down_revision: Union[str, Sequence[str], None] = "54a38d6bbc33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------
    # Knowledge bases
    # ---------------------------------------------------------
    op.create_table(
        "knowledge_bases",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "name",
            sa.String(150),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspace.id"],
            name="fk_knowledge_base_workspace",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            name="uq_knowledge_base_workspace",
        ),
        sa.UniqueConstraint(
            "id",
            "workspace_id",
            name="uq_knowledge_base_id_workspace",
        ),
    )

    # ---------------------------------------------------------
    # FAQ categories
    # ---------------------------------------------------------
    op.create_table(
        "faq_categories",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("slug", sa.String(180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "sort_order",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "sort_order >= 0",
            name="ck_faq_category_sort_order",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspace.id"],
            name="fk_faq_category_workspace",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id",
            "workspace_id",
            name="uq_faq_category_id_workspace",
        ),
        sa.UniqueConstraint(
            "workspace_id",
            "slug",
            name="uq_faq_category_workspace_slug",
        ),
    )

    op.create_index(
        "ix_faq_categories_workspace_active",
        "faq_categories",
        ["workspace_id", "is_active"],
        unique=False,
    )

    # ---------------------------------------------------------
    # FAQ items
    # ---------------------------------------------------------
    op.create_table(
        "faq_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.BigInteger(), nullable=False),
        sa.Column("category_id", sa.BigInteger(), nullable=True),
        sa.Column("question", sa.String(1000), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column(
            "priority",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "priority >= 0",
            name="ck_faq_item_priority",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspace.id"],
            name="fk_faq_item_workspace",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["category_id", "workspace_id"],
            ["faq_categories.id", "faq_categories.workspace_id"],
            name="fk_faq_item_category_workspace",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id",
            "workspace_id",
            name="uq_faq_item_id_workspace",
        ),
    )

    op.create_index(
        "ix_faq_items_workspace_active",
        "faq_items",
        ["workspace_id", "is_active"],
        unique=False,
    )

    op.create_index(
        "ix_faq_items_workspace_category",
        "faq_items",
        ["workspace_id", "category_id"],
        unique=False,
    )

    # ---------------------------------------------------------
    # Knowledge documents
    # ---------------------------------------------------------
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.BigInteger(), nullable=False),
        sa.Column("knowledge_base_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("source_name", sa.String(255), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("mime_type", sa.String(150), nullable=True),
        sa.Column("storage_key", sa.String(500), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            server_default=sa.text("'PENDING'"),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "source_type IN ('FILE', 'TEXT')",
            name="ck_knowledge_document_source_type",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'READY', 'FAILED', 'ARCHIVED')",
            name="ck_knowledge_document_status",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspace.id"],
            name="fk_knowledge_document_workspace",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["knowledge_base_id", "workspace_id"],
            ["knowledge_bases.id", "knowledge_bases.workspace_id"],
            name="fk_document_knowledge_base_workspace",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id",
            "workspace_id",
            name="uq_knowledge_document_id_workspace",
        ),
    )

    op.create_index(
        "ix_knowledge_documents_workspace_status",
        "knowledge_documents",
        ["workspace_id", "status"],
        unique=False,
    )

    op.create_index(
        "ix_knowledge_documents_knowledge_base",
        "knowledge_documents",
        ["knowledge_base_id"],
        unique=False,
    )

    # ---------------------------------------------------------
    # Knowledge chunks
    # ---------------------------------------------------------
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.BigInteger(), nullable=False),
        sa.Column("document_id", sa.BigInteger(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "chunk_index >= 0",
            name="ck_knowledge_chunk_index",
        ),
        sa.CheckConstraint(
            "token_count IS NULL OR token_count >= 0",
            name="ck_knowledge_chunk_token_count",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspace.id"],
            name="fk_knowledge_chunk_workspace",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["document_id", "workspace_id"],
            ["knowledge_documents.id", "knowledge_documents.workspace_id"],
            name="fk_knowledge_chunk_document_workspace",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id",
            "workspace_id",
            name="uq_knowledge_chunk_id_workspace",
        ),
        sa.UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_knowledge_chunk_document_index",
        ),
    )

    op.create_index(
        "ix_knowledge_chunks_workspace_document",
        "knowledge_chunks",
        ["workspace_id", "document_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop child tables before parent tables.
    op.drop_index(
        "ix_knowledge_chunks_workspace_document",
        table_name="knowledge_chunks",
    )
    op.drop_table("knowledge_chunks")

    op.drop_index(
        "ix_knowledge_documents_knowledge_base",
        table_name="knowledge_documents",
    )
    op.drop_index(
        "ix_knowledge_documents_workspace_status",
        table_name="knowledge_documents",
    )
    op.drop_table("knowledge_documents")

    op.drop_index(
        "ix_faq_items_workspace_category",
        table_name="faq_items",
    )
    op.drop_index(
        "ix_faq_items_workspace_active",
        table_name="faq_items",
    )
    op.drop_table("faq_items")

    op.drop_index(
        "ix_faq_categories_workspace_active",
        table_name="faq_categories",
    )
    op.drop_table("faq_categories")

    op.drop_table("knowledge_bases")
