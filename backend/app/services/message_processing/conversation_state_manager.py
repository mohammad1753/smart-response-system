from datetime import datetime, timezone
from enum import Enum
from typing import Callable

from sqlalchemy.orm import Session

from app.repositories.conversation_repository import (
    ConversationRepository,
)

from app.schemas.message_processing import (
    ConversationStatus,
    ConversationEventType,
    ConversationActorType,
)

from app.services.message_processing.event_manager import (
    ConversationEventManager,
)

from app.services.message_processing.exceptions import (
    ConversationNotFoundError,
    ConversationStateTransitionError,
)


class ConversationStateManager:

    def __init__(
        self,
        conversation_repository: ConversationRepository | None = None,
        event_manager: ConversationEventManager | None = None,
    ):

        self.conversation_repository = (
            conversation_repository
            if conversation_repository is not None
            else ConversationRepository()
        )

        self.event_manager = (
            event_manager
            if event_manager is not None
            else ConversationEventManager()
        )

    @staticmethod
    def _validate_positive_id(
        value: int,
        field_name: str,
    ) -> None:

        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value <= 0
        ):
            raise ValueError(
                f"{field_name} must be a positive integer."
            )

    @staticmethod
    def _normalize_status(value) -> ConversationStatus:

        if isinstance(value, ConversationStatus):
            return value

        if isinstance(value, Enum):
            value = value.value

        try:
            return ConversationStatus(str(value).upper())

        except ValueError as exc:
            raise ConversationStateTransitionError(
                f"Unknown conversation status: {value}"
            ) from exc

    @staticmethod
    def _normalize_actor_value(actor_type) -> str:

        if isinstance(actor_type, Enum):
            actor_type = actor_type.value

        if not isinstance(actor_type, str):
            raise ValueError("actor_type must be a string or Enum.")

        return actor_type.strip().upper()

    def _get_locked_conversation(
        self,
        session: Session,
        *,
        conversation_id: int,
        workspace_id: int,
        channel_account_id: int,
    ):

        self._validate_positive_id(
            conversation_id,
            "conversation_id",
        )

        self._validate_positive_id(
            workspace_id,
            "workspace_id",
        )

        self._validate_positive_id(
            channel_account_id,
            "channel_account_id",
        )

        conversation = (
            self.conversation_repository.get_by_id_for_update(
                session,
                conversation_id=conversation_id,
                workspace_id=workspace_id,
                channel_account_id=channel_account_id,
            )
        )

        if conversation is None:
            raise ConversationNotFoundError(
                "Conversation not found within the specified scope."
            )

        return conversation

    def _apply_transition(
        self,
        session: Session,
        *,
        conversation,
        current_status: ConversationStatus,
        allowed_from: set[ConversationStatus],
        target_status: ConversationStatus,
        event_type: ConversationEventType,
        actor_type: ConversationActorType,
        actor_user_id: int | None,
        details: dict | None,
        mutation: Callable | None = None,
    ):

        if current_status not in allowed_from:

            raise ConversationStateTransitionError(
                f"Cannot apply {event_type.value} "
                f"from status {current_status.value}."
            )

        now = datetime.now(timezone.utc)

        conversation.status = target_status.value
        conversation.updated_at = now

        if mutation is not None:
            mutation(conversation, now)

        self.event_manager.record(
            session,
            workspace_id=conversation.workspace_id,
            conversation_id=conversation.id,
            event_type=event_type,
            actor_type=actor_type,
            actor_user_id=actor_user_id,
            details=details,
        )

        session.flush()

        return conversation

    def request_handoff(
        self,
        session: Session,
        *,
        conversation_id: int,
        workspace_id: int,
        channel_account_id: int,
        reason: str | None = None,
        actor_type: ConversationActorType = ConversationActorType.AI,
        actor_user_id: int | None = None,
    ):

        if reason is not None and not isinstance(reason, str):
            raise ValueError("reason must be a string or None.")

        normalized_reason = (
            reason.strip()
            if reason and reason.strip()
            else None
        )

        conversation = self._get_locked_conversation(
            session,
            conversation_id=conversation_id,
            workspace_id=workspace_id,
            channel_account_id=channel_account_id,
        )

        current_status = self._normalize_status(
            conversation.status
        )

        def mutation(conv, now):
            conv.handoff_reason = normalized_reason
            conv.handed_off_at = now

        return self._apply_transition(
            session,
            conversation=conversation,
            current_status=current_status,
            allowed_from={
                ConversationStatus.AI_ACTIVE,
            },
            target_status=ConversationStatus.HUMAN_REQUIRED,
            event_type=ConversationEventType.HANDOFF_REQUESTED,
            actor_type=actor_type,
            actor_user_id=actor_user_id,
            details={
                "reason": normalized_reason,
            },
            mutation=mutation,
        )

    def disable_ai(
        self,
        session: Session,
        *,
        conversation_id: int,
        workspace_id: int,
        channel_account_id: int,
        reason: str | None = None,
        actor_type: ConversationActorType = ConversationActorType.SYSTEM,
        actor_user_id: int | None = None,
    ):

        if reason is not None and not isinstance(reason, str):
            raise ValueError("reason must be a string or None.")

        normalized_reason = (
            reason.strip()
            if reason and reason.strip()
            else "AI_DISABLED"
        )

        conversation = self._get_locked_conversation(
            session,
            conversation_id=conversation_id,
            workspace_id=workspace_id,
            channel_account_id=channel_account_id,
        )

        current_status = self._normalize_status(
            conversation.status
        )

        def mutation(conv, now):
            conv.handoff_reason = normalized_reason
            conv.handed_off_at = now

        return self._apply_transition(
            session,
            conversation=conversation,
            current_status=current_status,
            allowed_from={
                ConversationStatus.AI_ACTIVE,
            },
            target_status=ConversationStatus.HUMAN_REQUIRED,
            event_type=ConversationEventType.AI_DISABLED,
            actor_type=actor_type,
            actor_user_id=actor_user_id,
            details={
                "reason": normalized_reason,
            },
            mutation=mutation,
        )

    def assign_to_operator(
        self,
        session: Session,
        *,
        conversation_id: int,
        workspace_id: int,
        channel_account_id: int,
        assigned_user_id: int,
        actor_user_id: int,
        actor_type: ConversationActorType = ConversationActorType.OPERATOR,
    ):

        self._validate_positive_id(
            assigned_user_id,
            "assigned_user_id",
        )

        actor_value = self._normalize_actor_value(actor_type)

        if actor_value not in {"OPERATOR", "ADMIN"}:
            raise ValueError(
                "Only OPERATOR or ADMIN can assign a conversation."
            )

        conversation = self._get_locked_conversation(
            session,
            conversation_id=conversation_id,
            workspace_id=workspace_id,
            channel_account_id=channel_account_id,
        )

        current_status = self._normalize_status(
            conversation.status
        )

        def mutation(conv, now):
            conv.assigned_user_id = assigned_user_id

        return self._apply_transition(
            session,
            conversation=conversation,
            current_status=current_status,
            allowed_from={
                ConversationStatus.HUMAN_REQUIRED,
            },
            target_status=ConversationStatus.HUMAN_ACTIVE,
            event_type=ConversationEventType.ASSIGNED_TO_OPERATOR,
            actor_type=actor_type,
            actor_user_id=actor_user_id,
            details={
                "assigned_user_id": assigned_user_id,
            },
            mutation=mutation,
        )

    def record_operator_reply(
        self,
        session: Session,
        *,
        conversation_id: int,
        workspace_id: int,
        channel_account_id: int,
        actor_user_id: int,
        message_id: int | None = None,
        details: dict | None = None,
    ):

        if details is not None and not isinstance(details, dict):
            raise ValueError("details must be a dictionary or None.")

        if message_id is not None:
            self._validate_positive_id(
                message_id,
                "message_id",
            )

        conversation = self._get_locked_conversation(
            session,
            conversation_id=conversation_id,
            workspace_id=workspace_id,
            channel_account_id=channel_account_id,
        )

        current_status = self._normalize_status(
            conversation.status
        )

        if current_status != ConversationStatus.HUMAN_ACTIVE:
            raise ConversationStateTransitionError(
                "Operator cannot reply unless conversation is HUMAN_ACTIVE."
            )

        event_details = dict(details or {})

        if message_id is not None:
            event_details["message_id"] = message_id

        event = self.event_manager.record(
            session,
            workspace_id=workspace_id,
            conversation_id=conversation_id,
            event_type=ConversationEventType.OPERATOR_REPLIED,
            actor_type=ConversationActorType.OPERATOR,
            actor_user_id=actor_user_id,
            details=event_details,
        )

        conversation.updated_at = datetime.now(timezone.utc)

        session.flush()

        return event

    def return_to_ai(
        self,
        session: Session,
        *,
        conversation_id: int,
        workspace_id: int,
        channel_account_id: int,
        actor_type: ConversationActorType = ConversationActorType.SYSTEM,
        actor_user_id: int | None = None,
    ):

        conversation = self._get_locked_conversation(
            session,
            conversation_id=conversation_id,
            workspace_id=workspace_id,
            channel_account_id=channel_account_id,
        )

        current_status = self._normalize_status(
            conversation.status
        )

        def mutation(conv, now):
            conv.assigned_user_id = None
            conv.handoff_reason = None
            conv.handed_off_at = None

        return self._apply_transition(
            session,
            conversation=conversation,
            current_status=current_status,
            allowed_from={
                ConversationStatus.HUMAN_REQUIRED,
                ConversationStatus.HUMAN_ACTIVE,
            },
            target_status=ConversationStatus.AI_ACTIVE,
            event_type=ConversationEventType.RETURNED_TO_AI,
            actor_type=actor_type,
            actor_user_id=actor_user_id,
            details=None,
            mutation=mutation,
        )

    def enable_ai(
        self,
        session: Session,
        *,
        conversation_id: int,
        workspace_id: int,
        channel_account_id: int,
        actor_type: ConversationActorType = ConversationActorType.SYSTEM,
        actor_user_id: int | None = None,
    ):

        conversation = self._get_locked_conversation(
            session,
            conversation_id=conversation_id,
            workspace_id=workspace_id,
            channel_account_id=channel_account_id,
        )

        current_status = self._normalize_status(
            conversation.status
        )

        def mutation(conv, now):
            conv.assigned_user_id = None
            conv.handoff_reason = None
            conv.handed_off_at = None

        return self._apply_transition(
            session,
            conversation=conversation,
            current_status=current_status,
            allowed_from={
                ConversationStatus.HUMAN_REQUIRED,
                ConversationStatus.HUMAN_ACTIVE,
            },
            target_status=ConversationStatus.AI_ACTIVE,
            event_type=ConversationEventType.AI_ENABLED,
            actor_type=actor_type,
            actor_user_id=actor_user_id,
            details=None,
            mutation=mutation,
        )

    def close_conversation(
        self,
        session: Session,
        *,
        conversation_id: int,
        workspace_id: int,
        channel_account_id: int,
        actor_type: ConversationActorType = ConversationActorType.SYSTEM,
        actor_user_id: int | None = None,
    ):

        conversation = self._get_locked_conversation(
            session,
            conversation_id=conversation_id,
            workspace_id=workspace_id,
            channel_account_id=channel_account_id,
        )

        current_status = self._normalize_status(
            conversation.status
        )

        def mutation(conv, now):
            conv.assigned_user_id = None

        return self._apply_transition(
            session,
            conversation=conversation,
            current_status=current_status,
            allowed_from={
                ConversationStatus.AI_ACTIVE,
                ConversationStatus.HUMAN_REQUIRED,
                ConversationStatus.HUMAN_ACTIVE,
            },
            target_status=ConversationStatus.CLOSED,
            event_type=ConversationEventType.CONVERSATION_CLOSED,
            actor_type=actor_type,
            actor_user_id=actor_user_id,
            details=None,
            mutation=mutation,
        )

    def reopen_conversation(
        self,
        session: Session,
        *,
        conversation_id: int,
        workspace_id: int,
        channel_account_id: int,
        actor_type: ConversationActorType = ConversationActorType.SYSTEM,
        actor_user_id: int | None = None,
    ):

        conversation = self._get_locked_conversation(
            session,
            conversation_id=conversation_id,
            workspace_id=workspace_id,
            channel_account_id=channel_account_id,
        )

        current_status = self._normalize_status(
            conversation.status
        )

        def mutation(conv, now):
            conv.assigned_user_id = None
            conv.handoff_reason = None
            conv.handed_off_at = None

        return self._apply_transition(
            session,
            conversation=conversation,
            current_status=current_status,
            allowed_from={
                ConversationStatus.CLOSED,
            },
            target_status=ConversationStatus.AI_ACTIVE,
            event_type=ConversationEventType.CONVERSATION_REOPENED,
            actor_type=actor_type,
            actor_user_id=actor_user_id,
            details=None,
            mutation=mutation,
        )