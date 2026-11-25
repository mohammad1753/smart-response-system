
"""add customers and customer identities

Revision ID: b50a78e3c5da
Revises: 27f417eb494e
Create Date: 2026-11-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b50a78e3c5da"
down_revision: Union[str, Sequence[str], None] = "27f417eb494e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------
    # Customers
    # ---------------------------------------------------------
    op.create_table(
        "customers",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "full_name",
            sa.String(length=150),
            nullable=True,
        ),
        sa.Column(
            "phone_number",
            sa.String(length=30),
            nullable=True,
        ),
        sa.Column(
            "email",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
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
            name="fk_customers_workspace",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id",
            "workspace_id",
            name="uq_customers_id_workspace",
        ),
    )

    op.create_index(
        "ix_customers_workspace_created",
        "customers",
        ["workspace_id", "created_at"],
        unique=False,
    )

    # ---------------------------------------------------------
    # Customer identities
    # ---------------------------------------------------------
    op.create_table(
        "customer_identities",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "channel_account_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "external_user_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "display_name",
            sa.String(length=150),
            nullable=True,
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
            ["customer_id", "workspace_id"],
            ["customers.id", "customers.workspace_id"],
            name="fk_identity_customer_workspace",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["channel_account_id", "workspace_id"],
            ["channel_accounts.id", "channel_accounts.workspace_id"],
            name="fk_identity_channel_workspace",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id",
            "workspace_id",
            name="uq_customer_identity_id_workspace",
        ),
        sa.UniqueConstraint(
            "channel_account_id",
            "external_user_id",
            name="uq_channel_external_user",
        ),
    )

    op.create_index(
        "ix_customer_identities_customer",
        "customer_identities",
        ["customer_id"],
        unique=False,
    )

def downgrade() -> None:
    # Drop dependent table first
    op.drop_index(
        "ix_customer_identities_customer",
        table_name="customer_identities",
    )
    op.drop_table("customer_identities")

    op.drop_index(
        "ix_customers_workspace_created",
        table_name="customers",
    )
    op.drop_table("customers")
