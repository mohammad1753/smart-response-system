
from datetime import datetime, timezone
from types import SimpleNamespace

from app.schemas.message_processing import (
    ConversationStatus,
    ConversationEventType,
    ConversationActorType,
)

from app.services.message_processing.event_manager import (
    ConversationEventManager,
)

from app.services.message_processing.conversation_state_manager import (
    ConversationStateManager,
)

from app.services.message_processing.exceptions import (
    ConversationNotFoundError,
    ConversationStateTransitionError,
)


class FakeSession:

    def __init__(self):
        self.flush_count = 0

    def flush(self):
        self.flush_count += 1


class FakeEventRepository:

    def __init__(self):
        self.records = []
        self.next_id = 1

    def add(self, session, event):
        event.id = self.next_id
        self.next_id += 1
        self.records.append(event)
        return event


class FakeConversationRepository:

    def __init__(self, conversation=None):
        self.conversation = conversation

    def get_by_id_for_update(
        self,
        session,
        *,
        conversation_id,
        workspace_id,
        channel_account_id,
    ):

        if self.conversation is None:
            return None

        if self.conversation.id != conversation_id:
            return None

        if self.conversation.workspace_id != workspace_id:
            return None

        if self.conversation.channel_account_id != channel_account_id:
            return None

        return self.conversation


def build_conversation(
    *,
    status=ConversationStatus.AI_ACTIVE,
):

    return SimpleNamespace(
        id=400,
        workspace_id=100,
        channel_account_id=10,
        customer_identity_id=300,
        assigned_user_id=None,
        status=status.value,
        handoff_reason=None,
        handed_off_at=None,
        updated_at=None,
    )


def build_managers(
    *,
    status=ConversationStatus.AI_ACTIVE,
):

    session = FakeSession()

    conversation = build_conversation(
        status=status,
    )

    conversation_repository = FakeConversationRepository(
        conversation
    )

    event_repository = FakeEventRepository()

    event_manager = ConversationEventManager(
        event_repository=event_repository
    )

    state_manager = ConversationStateManager(
        conversation_repository=conversation_repository,
        event_manager=event_manager,
    )

    return (
        session,
        conversation,
        event_repository,
        state_manager,
        event_manager,
    )


def test_event_recording():

    session = FakeSession()
    repository = FakeEventRepository()

    manager = ConversationEventManager(
        event_repository=repository
    )

    result = manager.record(
        session,
        workspace_id=100,
        conversation_id=400,
        event_type=ConversationEventType.HANDOFF_REQUESTED,
        actor_type=ConversationActorType.AI,
        details={
            "reason": "Human support required",
        },
    )

    assert result.id == 1
    assert result.workspace_id == 100
    assert result.conversation_id == 400
    assert result.event_type == "HANDOFF_REQUESTED"
    assert result.actor_type == "AI"
    assert result.actor_user_id is None
    assert result.details["reason"] == "Human support required"

    assert len(repository.records) == 1

    print("Conversation event recording: PASS")


def test_event_actor_validation():

    session = FakeSession()
    repository = FakeEventRepository()

    manager = ConversationEventManager(
        event_repository=repository
    )

    try:
        manager.record(
            session,
            workspace_id=100,
            conversation_id=400,
            event_type=ConversationEventType.AI_DISABLED,
            actor_type=ConversationActorType.ADMIN,
        )
    except ValueError:
        assert len(repository.records) == 0
        print("Conversation event actor validation: PASS")
    else:
        raise AssertionError(
            "ADMIN event without actor_user_id was accepted."
        )


def test_event_details_validation():

    session = FakeSession()
    repository = FakeEventRepository()

    manager = ConversationEventManager(
        event_repository=repository
    )

    try:
        manager.record(
            session,
            workspace_id=100,
            conversation_id=400,
            event_type=ConversationEventType.AI_DISABLED,
            details={
                "invalid": object(),
            },
        )
    except ValueError:
        assert len(repository.records) == 0
        print("Conversation event details validation: PASS")
    else:
        raise AssertionError(
            "Invalid event details were accepted."
        )


def test_request_handoff():

    (
        session,
        conversation,
        event_repository,
        manager,
        _,
    ) = build_managers()

    result = manager.request_handoff(
        session,
        conversation_id=400,
        workspace_id=100,
        channel_account_id=10,
        reason="Customer needs human support",
    )

    assert result.status == "HUMAN_REQUIRED"
    assert result.handoff_reason == "Customer needs human support"
    assert result.handed_off_at is not None

    assert len(event_repository.records) == 1

    event = event_repository.records[0]

    assert event.event_type == "HANDOFF_REQUESTED"
    assert event.actor_type == "AI"

    print("Conversation handoff: PASS")


def test_disable_ai():

    (
        session,
        conversation,
        event_repository,
        manager,
        _,
    ) = build_managers()

    result = manager.disable_ai(
        session,
        conversation_id=400,
        workspace_id=100,
        channel_account_id=10,
        reason="AI temporarily disabled",
    )

    assert result.status == "HUMAN_REQUIRED"
    assert result.handoff_reason == "AI temporarily disabled"

    assert len(event_repository.records) == 1
    assert event_repository.records[0].event_type == "AI_DISABLED"

    print("AI disable: PASS")


def test_assign_to_operator():

    (
        session,
        conversation,
        event_repository,
        manager,
        _,
    ) = build_managers(
        status=ConversationStatus.HUMAN_REQUIRED,
    )

    result = manager.assign_to_operator(
        session,
        conversation_id=400,
        workspace_id=100,
        channel_account_id=10,
        assigned_user_id=25,
        actor_user_id=25,
    )

    assert result.status == "HUMAN_ACTIVE"
    assert result.assigned_user_id == 25

    assert len(event_repository.records) == 1

    event = event_repository.records[0]

    assert event.event_type == "ASSIGNED_TO_OPERATOR"
    assert event.actor_type == "OPERATOR"
    assert event.actor_user_id == 25

    print("Conversation operator assignment: PASS")


def test_operator_reply():

    (
        session,
        conversation,
        event_repository,
        manager,
        _,
    ) = build_managers(
        status=ConversationStatus.HUMAN_ACTIVE,
    )

    conversation.assigned_user_id = 25

    result = manager.record_operator_reply(
        session,
        conversation_id=400,
        workspace_id=100,
        channel_account_id=10,
        actor_user_id=25,
        message_id=500,
    )

    assert result.id == 1
    assert result.event_type == "OPERATOR_REPLIED"
    assert result.actor_type == "OPERATOR"
    assert result.actor_user_id == 25
    assert result.details["message_id"] == 500

    assert conversation.status == "HUMAN_ACTIVE"

    print("Operator reply event: PASS")


def test_operator_reply_invalid_status():

    (
        session,
        conversation,
        event_repository,
        manager,
        _,
    ) = build_managers(
        status=ConversationStatus.AI_ACTIVE,
    )

    try:
        manager.record_operator_reply(
            session,
            conversation_id=400,
            workspace_id=100,
            channel_account_id=10,
            actor_user_id=25,
        )
    except ConversationStateTransitionError:
        assert len(event_repository.records) == 0
        assert conversation.status == "AI_ACTIVE"
        print("Operator reply status protection: PASS")
    else:
        raise AssertionError(
            "Operator reply was accepted in AI_ACTIVE status."
        )


def test_return_to_ai():

    (
        session,
        conversation,
        event_repository,
        manager,
        _,
    ) = build_managers(
        status=ConversationStatus.HUMAN_ACTIVE,
    )

    conversation.assigned_user_id = 25
    conversation.handoff_reason = "Human support required"
    conversation.handed_off_at = datetime.now(timezone.utc)

    result = manager.return_to_ai(
        session,
        conversation_id=400,
        workspace_id=100,
        channel_account_id=10,
    )

    assert result.status == "AI_ACTIVE"
    assert result.assigned_user_id is None
    assert result.handoff_reason is None
    assert result.handed_off_at is None

    assert len(event_repository.records) == 1
    assert event_repository.records[0].event_type == "RETURNED_TO_AI"

    print("Conversation return to AI: PASS")


def test_enable_ai():

    (
        session,
        conversation,
        event_repository,
        manager,
        _,
    ) = build_managers(
        status=ConversationStatus.HUMAN_REQUIRED,
    )

    result = manager.enable_ai(
        session,
        conversation_id=400,
        workspace_id=100,
        channel_account_id=10,
    )

    assert result.status == "AI_ACTIVE"
    assert result.assigned_user_id is None

    assert len(event_repository.records) == 1
    assert event_repository.records[0].event_type == "AI_ENABLED"

    print("AI enable: PASS")


def test_close_conversation():

    (
        session,
        conversation,
        event_repository,
        manager,
        _,
    ) = build_managers(
        status=ConversationStatus.HUMAN_ACTIVE,
    )

    conversation.assigned_user_id = 25

    result = manager.close_conversation(
        session,
        conversation_id=400,
        workspace_id=100,
        channel_account_id=10,
    )

    assert result.status == "CLOSED"
    assert result.assigned_user_id is None

    assert len(event_repository.records) == 1

    event = event_repository.records[0]

    assert event.event_type == "CONVERSATION_CLOSED"

    print("Conversation close: PASS")


def test_reopen_conversation():

    (
        session,
        conversation,
        event_repository,
        manager,
        _,
    ) = build_managers(
        status=ConversationStatus.CLOSED,
    )

    result = manager.reopen_conversation(
        session,
        conversation_id=400,
        workspace_id=100,
        channel_account_id=10,
    )

    assert result.status == "AI_ACTIVE"
    assert result.assigned_user_id is None

    assert len(event_repository.records) == 1

    event = event_repository.records[0]

    assert event.event_type == "CONVERSATION_REOPENED"

    print("Conversation reopen: PASS")


def test_invalid_state_transition():

    (
        session,
        conversation,
        event_repository,
        manager,
        _,
    ) = build_managers(
        status=ConversationStatus.AI_ACTIVE,
    )

    try:
        manager.assign_to_operator(
            session,
            conversation_id=400,
            workspace_id=100,
            channel_account_id=10,
            assigned_user_id=25,
            actor_user_id=25,
        )
    except ConversationStateTransitionError:
        assert conversation.status == "AI_ACTIVE"
        assert len(event_repository.records) == 0
        print("Invalid state transition protection: PASS")
    else:
        raise AssertionError(
            "Invalid conversation state transition was accepted."
        )


def test_conversation_not_found():

    session = FakeSession()

    conversation_repository = FakeConversationRepository(
        conversation=None
    )

    event_repository = FakeEventRepository()

    event_manager = ConversationEventManager(
        event_repository=event_repository
    )

    manager = ConversationStateManager(
        conversation_repository=conversation_repository,
        event_manager=event_manager,
    )

    try:
        manager.request_handoff(
            session,
            conversation_id=400,
            workspace_id=100,
            channel_account_id=10,
        )
    except ConversationNotFoundError:
        assert len(event_repository.records) == 0
        print("Conversation not found protection: PASS")
    else:
        raise AssertionError(
            "Non-existing conversation was accepted."
        )


def test_conversation_scope_protection():

    (
        session,
        conversation,
        event_repository,
        manager,
        _,
    ) = build_managers()

    try:
        manager.request_handoff(
            session,
            conversation_id=400,
            workspace_id=999,
            channel_account_id=10,
        )
    except ConversationNotFoundError:
        assert conversation.status == "AI_ACTIVE"
        assert len(event_repository.records) == 0
        print("Conversation workspace scope protection: PASS")
    else:
        raise AssertionError(
            "Conversation from another workspace was accepted."
        )


if __name__ == "__main__":

    test_event_recording()
    test_event_actor_validation()
    test_event_details_validation()

    test_request_handoff()
    test_disable_ai()

    test_assign_to_operator()
    test_operator_reply()
    test_operator_reply_invalid_status()

    test_return_to_ai()
    test_enable_ai()

    test_close_conversation()
    test_reopen_conversation()

    test_invalid_state_transition()
    test_conversation_not_found()
    test_conversation_scope_protection()

    print("\nAll conversation state and event tests passed.")





# python -c "import runpy; runpy.run_path('test/conversation_state_test.py', run_name='__main__')"