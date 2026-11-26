
from types import SimpleNamespace

from app.schemas.message_processing import (
    ConversationStatus,
    ResolvedCustomer,
)
from app.services.message_processing.conversation_manager import (
    ConversationManager,
)
from app.services.message_processing.exceptions import (
    CustomerIdentityNotFoundError,
)


class FakeIdentityRepository:

    def __init__(self, identity=None):
        self.identity = identity
        self.lock_calls = 0

    def get_for_update(self, **kwargs):
        self.lock_calls += 1
        return self.identity


class FakeConversationRepository:

    def __init__(self, conversations=None):
        self.conversations = conversations or []
        self.next_id = 100
        self.add_calls = 0

    def get_active_by_identity(
        self,
        session,
        workspace_id,
        customer_identity_id,
        channel_account_id,
        active_statuses,
    ):
        for conversation in self.conversations:
            if (
                conversation.workspace_id == workspace_id
                and conversation.customer_identity_id == customer_identity_id
                and conversation.channel_account_id == channel_account_id
                and conversation.status in active_statuses
            ):
                return conversation

        return None

    def add(self, session, conversation):
        self.add_calls += 1
        conversation.id = self.next_id
        self.next_id += 1
        self.conversations.append(conversation)
        return conversation


class FakeSession:
    pass


def build_customer():
    return ResolvedCustomer(
        workspace_id=10,
        channel_account_id=20,
        customer_id=30,
        customer_identity_id=40,
        external_user_id="user_123",
        customer_created=False,
        identity_created=False,
    )


def build_identity():
    return SimpleNamespace(
        id=40,
        workspace_id=10,
        channel_account_id=20,
        customer_id=30,
        external_user_id="user_123",
    )


def build_manager(identity=None, conversations=None):
    identities = FakeIdentityRepository(
        identity if identity is not None else build_identity()
    )

    repository = FakeConversationRepository(conversations)

    manager = ConversationManager(
        identity_repository=identities,
        conversation_repository=repository,
    )

    return manager, identities, repository


def test_create_new_conversation():
    manager, identities, repository = build_manager()

    result = manager.resolve_or_create(
        FakeSession(),
        build_customer(),
    )

    assert result.conversation_id == 100
    assert result.status == ConversationStatus.AI_ACTIVE
    assert result.conversation_created is True

    assert identities.lock_calls == 1
    assert repository.add_calls == 1

    print("New conversation creation: PASS")


def test_reuse_active_conversation():
    existing = SimpleNamespace(
        id=200,
        workspace_id=10,
        customer_identity_id=40,
        channel_account_id=20,
        status="HUMAN_ACTIVE",
    )

    manager, identities, repository = build_manager(
        conversations=[existing]
    )

    result = manager.resolve_or_create(
        FakeSession(),
        build_customer(),
    )

    assert result.conversation_id == 200
    assert result.status == ConversationStatus.HUMAN_ACTIVE
    assert result.conversation_created is False

    assert repository.add_calls == 0

    print("Active conversation reuse: PASS")


def test_closed_conversation_creates_new():
    closed = SimpleNamespace(
        id=300,
        workspace_id=10,
        customer_identity_id=40,
        channel_account_id=20,
        status="CLOSED",
    )

    manager, identities, repository = build_manager(
        conversations=[closed]
    )

    result = manager.resolve_or_create(
        FakeSession(),
        build_customer(),
    )

    assert result.conversation_id == 100
    assert result.status == ConversationStatus.AI_ACTIVE
    assert result.conversation_created is True

    assert repository.add_calls == 1

    print("Closed conversation replacement: PASS")


def test_missing_identity():
    manager, identities, repository = build_manager(identity=None)

    # Explicitly simulate a missing identity.
    identities.identity = None

    try:
        manager.resolve_or_create(
            FakeSession(),
            build_customer(),
        )
    except CustomerIdentityNotFoundError:
        print("Missing identity protection: PASS")
    else:
        raise AssertionError("Missing identity was accepted.")


def test_workspace_scope_preservation():
    manager, _, _ = build_manager()

    result = manager.resolve_or_create(
        FakeSession(),
        build_customer(),
    )

    assert result.workspace_id == 10
    assert result.channel_account_id == 20
    assert result.customer_id == 30
    assert result.customer_identity_id == 40

    print("Workspace scope preservation: PASS")


if __name__ == "__main__":
    test_create_new_conversation()
    test_reuse_active_conversation()
    test_closed_conversation_creates_new()
    test_missing_identity()
    test_workspace_scope_preservation()

    print("\nAll conversation manager tests passed.")







# python -c "import runpy; runpy.run_path('test/conversation_manager_test.py', run_name='__main__')"