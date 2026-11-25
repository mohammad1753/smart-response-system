"""add conversation response mode check

Revision ID: 3113ca25127d
Revises: 8d2f6c91a4b7
Create Date: 2026-11-24 14:54:45.626005

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3113ca25127d'
down_revision: Union[str, Sequence[str], None] = '8d2f6c91a4b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_check_constraint(
        "ck_conversation_response_mode",
        "conversations",
        "response_mode IN ('AI', 'HUMAN')",
    )


def downgrade():
    op.drop_constraint(
        "ck_conversation_response_mode",
        "conversations",
        type_="check",
    )