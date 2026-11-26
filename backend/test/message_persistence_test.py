
from datetime import datetime, timezone, timedelta

from app.schemas.message_processing import (
    ConversationStatus,
    NormalizedIncomingMessage,
    ResolvedConversation,
    StoredMessageType,
)

from app.services.message_processing.message_persister import (
    MessagePersister,
)

from app.services.message_processing.exceptions import (
    ConversationScopeMismatchError,
    UnsupportedMessagePayloadError,
)


class FakeMessageRepository:

    def __init__(self):
        self.records = []
        self.next_id = 1

    def add(self, session, message):
        message.id = self.next_id
        self.next_id += 1
        self.records.append(message)
        return message


class FakeSession:
    pass


def build_message(
    *,
    channel_account_id=10,
    message_type=StoredMessageType.TEXT,
    media=None,
):
    return NormalizedIncomingMessage(
        channel_account_id=channel_account_id,
        platform="rubika",
        external_message_id="msg_123",
        external_chat_id="chat_456",
        external_user_id="user_789",
        content="سلام",
        message_type=message_type,
        media=media,
        occurred_at=datetime(
            2026, 11, 26, 8, 0,
            tzinfo=timezone(timedelta(hours=3, minutes=30)),
        ),
        received_at=datetime.now(timezone.utc),
    )


def build_conversation(
    *,
    channel_account_id=10,
    status=ConversationStatus.AI_ACTIVE,
):
    return ResolvedConversation(
        workspace_id=100,
        channel_account_id=channel_account_id,
        customer_id=200,
        customer_identity_id=300,
        conversation_id=400,
        status=status,
        conversation_created=False,
    )


def test_text_message_persistence():
    repository = FakeMessageRepository()
    persister = MessagePersister(repository)

    result = persister.persist(
        FakeSession(),
        build_message(),
        build_conversation(),
    )

    assert result.id == 1
    assert result.workspace_id == 100
    assert result.conversation_id == 400
    assert result.channel_account_id == 10
    assert result.external_message_id == "msg_123"
    assert result.direction == "INBOUND"
    assert result.sender_type == "CUSTOMER"
    assert result.content == "سلام"
    assert result.message_type == "TEXT"
    assert result.status == "RECEIVED"

    print("Text message persistence: PASS")


def test_utc_timestamp_storage():
    repository = FakeMessageRepository()
    persister = MessagePersister(repository)

    result = persister.persist(
        FakeSession(),
        build_message(),
        build_conversation(),
    )

    assert result.created_at.tzinfo is None
    assert result.created_at == datetime(2026, 11, 26, 4, 30)

    print("UTC timestamp conversion: PASS")


def test_channel_account_scope():
    persister = MessagePersister(FakeMessageRepository())

    try:
        persister.persist(
            FakeSession(),
            build_message(channel_account_id=99),
            build_conversation(),
        )
    except ConversationScopeMismatchError:
        print("Channel account scope protection: PASS")
    else:
        raise AssertionError("Invalid channel scope was accepted.")


def test_closed_conversation():
    persister = MessagePersister(FakeMessageRepository())

    try:
        persister.persist(
            FakeSession(),
            build_message(),
            build_conversation(status=ConversationStatus.CLOSED),
        )
    except ConversationScopeMismatchError:
        print("Closed conversation protection: PASS")
    else:
        raise AssertionError("Closed conversation was accepted.")


def test_media_message_persistence():
    repository = FakeMessageRepository()
    persister = MessagePersister(repository)

    message = build_message(
        message_type=StoredMessageType.IMAGE,
        media={"file_id": "image_123"},
    )

    result = persister.persist(
        FakeSession(),
        message,
        build_conversation(),
    )

    assert result.id == 1
    assert result.message_type == "IMAGE"
    assert result.content == "سلام"
    assert result.direction == "INBOUND"
    assert result.sender_type == "CUSTOMER"
    assert result.status == "RECEIVED"

    print("Media message persistence: PASS")



if __name__ == "__main__":
    test_text_message_persistence()
    test_utc_timestamp_storage()
    test_channel_account_scope()
    test_closed_conversation()
    test_media_message_persistence()
    
    print("\nAll message persistence tests passed.")






# python -c "import runpy; runpy.run_path('test/message_persistence_test.py', run_name='__main__')"