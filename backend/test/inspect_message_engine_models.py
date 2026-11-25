
from pathlib import Path

from app.models.channel_account import ChannelAccount
from app.models.customer import Customer
from app.models.customer_identity import CustomerIdentity
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.conversation_event import ConversationEvent

from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    UniqueConstraint,
)


models = [
    ChannelAccount,
    Customer,
    CustomerIdentity,
    Conversation,
    Message,
    ConversationEvent,
]


for model in models:
    table = model.__table__

    print(f"\n{'=' * 65}")
    print(f"MODEL: {model.__name__} | TABLE: {table.name}")
    print("=" * 65)

    print("\nCOLUMNS:")
    for column in table.columns:
        default = (
            str(column.default.arg)
            if column.default is not None
            else None
        )
        server_default = (
            str(column.server_default.arg)
            if column.server_default is not None
            else None
        )

        print(
            column.name,
            "| type:", column.type,
            "| nullable:", column.nullable,
            "| primary_key:", column.primary_key,
            "| default:", default,
            "| server_default:", server_default,
        )

    print("\nCONSTRAINTS:")
    for constraint in table.constraints:
        if isinstance(constraint, UniqueConstraint):
            print(
                "UNIQUE:",
                [column.name for column in constraint.columns],
            )

        elif isinstance(constraint, ForeignKeyConstraint):
            print(
                "FOREIGN KEY:",
                [str(element) for element in constraint.elements],
            )

        elif isinstance(constraint, CheckConstraint):
            print("CHECK:", constraint.sqltext)

    print("\nINDEXES:")
    for index in table.indexes:
        print(
            index.name,
            "| columns:",
            [column.name for column in index.columns],
            "| unique:",
            index.unique,
        )

    print("\nRELATIONSHIPS:")
    for relationship in model.__mapper__.relationships:
        print(
            relationship.key,
            "->",
            relationship.mapper.class_.__name__,
        )


print("\n" + "=" * 65)
print("APP/CORE FILES")
print("=" * 65)

for path in sorted(Path("app/core").rglob("*.py")):
    print(path)



# python -c "import runpy; runpy.run_path('test/inspect_message_engine_models.py', run_name='__main__')"