
from contextlib import contextmanager
from datetime import datetime, timezone
from types import SimpleNamespace

from sqlalchemy.exc import IntegrityError

from app.schemas.message_processing import (
    ConversationStatus,
    NormalizedIncomingMessage,
    ResolvedConversation,
    StoredMessageType,
)

from app.services.message_processing.idempotency import (
    MessageIdempotencyService,
)

from app.services.message_processing.message_persister import (
    MessagePersister,
)


class FakeSession:

    @contextmanager
    def begin_nested(self):
        yield


class FakeMessageRepository:

    def __init__(self):
        self.records = {}
        self.next_id = 1
        self.simulate_race = False

    def get_by_external_id(
        self,
        session,
        channel_account_id,
        external_message_id,
    ):
        return self.records.get(
            (channel_account_id, external_message_id)
        )

    def add(self, session, message):
        key = (
            message.channel_account_id,
            message.external_message_id,
        )

        if self.simulate_race:
            self.simulate_race = False

            existing = SimpleNamespace(
                id=99,
                workspace_id=message.workspace_id,
                conversation_id=message.conversation_id,
                channel_account_id=message.channel_account_id,
                external_message_id=message.external_message_id,
            )

            self.records[key] = existing

            raise IntegrityError(
                "INSERT",
                {},
                Exception("Duplicate entry"),
            )

        if key in self.records:
            raise IntegrityError(
                "INSERT",
                {},
                Exception("Duplicate entry"),
            )

        message.id = self.next_id
        self.next_id += 1
        self.records[key] = message

        return message


def build_message(external_message_id="msg_123"):
    return NormalizedIncomingMessage(
        channel_account_id=10,
        platform="rubika",
        external_message_id=external_message_id,
        external_chat_id="chat_456",
        external_user_id="user_789",
        content="سلام",
        message_type=StoredMessageType.TEXT,
        occurred_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
    )


def build_conversation():
    return ResolvedConversation(
        workspace_id=100,
        channel_account_id=10,
        customer_id=200,
        customer_identity_id=300,
        conversation_id=400,
        status=ConversationStatus.AI_ACTIVE,
        conversation_created=False,
    )


def test_new_message():
    repository = FakeMessageRepository()

    service = MessageIdempotencyService(repository)

    result = service.is_duplicate(
        FakeSession(),
        build_message(),
    )

    assert result is False

    print("New message detection: PASS")


def test_duplicate_detection():
    repository = FakeMessageRepository()

    message = build_message()

    existing = SimpleNamespace(
        id=10,
        workspace_id=100,
        conversation_id=400,
        channel_account_id=10,
        external_message_id=message.external_message_id,
    )

    repository.records[(10, "msg_123")] = existing

    service = MessageIdempotencyService(repository)

    result = service.is_duplicate(
        FakeSession(),
        message,
    )

    assert result is True

    print("Duplicate message detection: PASS")


def test_first_persistence():
    repository = FakeMessageRepository()
    persister = MessagePersister(repository)

    result = persister.persist(
        FakeSession(),
        build_message(),
        build_conversation(),
    )

    assert result.message_id == 1
    assert result.is_duplicate is False

    print("First message persistence: PASS")


def test_repeated_persistence():
    repository = FakeMessageRepository()
    persister = MessagePersister(repository)

    session = FakeSession()
    message = build_message()

    first = persister.persist(
        session,
        message,
        build_conversation(),
    )

    second = persister.persist(
        session,
        message,
        build_conversation(),
    )

    assert first.message_id == second.message_id
    assert first.is_duplicate is False
    assert second.is_duplicate is True
    assert len(repository.records) == 1

    print("Repeated persistence protection: PASS")


def test_concurrent_duplicate_conflict():
    repository = FakeMessageRepository()
    repository.simulate_race = True

    persister = MessagePersister(repository)

    result = persister.persist(
        FakeSession(),
        build_message(),
        build_conversation(),
    )

    assert result.is_duplicate is True
    assert result.message_id == 99

    print("Concurrent duplicate conflict handling: PASS")


if __name__ == "__main__":
    test_new_message()
    test_duplicate_detection()
    test_first_persistence()
    test_repeated_persistence()
    test_concurrent_duplicate_conflict()

    print("\nAll idempotency tests passed.")






# python -c "import runpy; runpy.run_path('test/message_idempotency_test.py', run_name='__main__')"