import json

from enum import Enum
from sqlalchemy.orm import Session

from app.models.conversation_event import ConversationEvent

from app.repositories.conversation_event_repository import (
    ConversationEventRepository,
)

from app.schemas.message_processing import (
    ConversationActorType,
    ConversationEventType,
    ResolvedConversation,
)


class ConversationEventManager:

    def __init__(
        self,
        event_repository: ConversationEventRepository | None = None,
    ):

        self.event_repository = (
            event_repository
            if event_repository is not None
            else ConversationEventRepository()
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
    def _normalize_enum(
        value,
        enum_class,
        field_name: str,
    ):

        if isinstance(value, enum_class):
            return value

        if isinstance(value, Enum):
            value = value.value

        if not isinstance(value, str):
            raise ValueError(
                f"{field_name} must be a valid string or Enum."
            )

        try:
            return enum_class(value.strip().upper())

        except ValueError as exc:
            raise ValueError(
                f"Invalid {field_name}: {value}"
            ) from exc

    @classmethod
    def _normalize_event_type(
        cls,
        event_type,
    ) -> ConversationEventType:

        return cls._normalize_enum(
            event_type,
            ConversationEventType,
            "event_type",
        )

    @classmethod
    def _normalize_actor_type(
        cls,
        actor_type,
    ) -> ConversationActorType:

        return cls._normalize_enum(
            actor_type,
            ConversationActorType,
            "actor_type",
        )

    @classmethod
    def _validate_actor(
        cls,
        actor_type: ConversationActorType,
        actor_user_id: int | None,
    ) -> None:

        user_required = {
            ConversationActorType.OPERATOR,
            ConversationActorType.ADMIN,
        }

        if actor_type in user_required:

            if actor_user_id is None:
                raise ValueError(
                    "actor_user_id is required for OPERATOR and ADMIN."
                )

            cls._validate_positive_id(
                actor_user_id,
                "actor_user_id",
            )

        elif actor_user_id is not None:

            raise ValueError(
                "actor_user_id must be None for SYSTEM, AI and CUSTOMER."
            )

    @staticmethod
    def _prepare_details(
        details: dict | None,
    ) -> dict | None:

        if details is None:
            return None

        if not isinstance(details, dict):
            raise ValueError(
                "details must be a dictionary or None."
            )

        try:
            serialized = json.dumps(
                details,
                ensure_ascii=False,
                allow_nan=False,
            )

            return json.loads(serialized)

        except (TypeError, ValueError) as exc:
            raise ValueError(
                "details must contain valid JSON-compatible data."
            ) from exc

    def record(
        self,
        session: Session,
        *,
        workspace_id: int,
        conversation_id: int,
        event_type: ConversationEventType,
        actor_type: ConversationActorType = ConversationActorType.SYSTEM,
        actor_user_id: int | None = None,
        details: dict | None = None,
    ) -> ConversationEvent:

        self._validate_positive_id(
            workspace_id,
            "workspace_id",
        )

        self._validate_positive_id(
            conversation_id,
            "conversation_id",
        )

        normalized_event_type = self._normalize_event_type(
            event_type
        )

        normalized_actor_type = self._normalize_actor_type(
            actor_type
        )

        self._validate_actor(
            normalized_actor_type,
            actor_user_id,
        )

        prepared_details = self._prepare_details(details)

        event = ConversationEvent(
            workspace_id=workspace_id,
            conversation_id=conversation_id,
            event_type=normalized_event_type.value,
            actor_type=normalized_actor_type.value,
            actor_user_id=actor_user_id,
            details=prepared_details,
        )

        return self.event_repository.add(
            session,
            event,
        )

    def record_conversation_created(
        self,
        session: Session,
        *,
        resolved_conversation: ResolvedConversation,
        actor_type: ConversationActorType = ConversationActorType.SYSTEM,
        actor_user_id: int | None = None,
    ) -> ConversationEvent | None:

        if not resolved_conversation.conversation_created:
            return None

        status = resolved_conversation.status

        if isinstance(status, Enum):
            status = status.value

        details = {
            "channel_account_id": (
                resolved_conversation.channel_account_id
            ),
            "customer_id": resolved_conversation.customer_id,
            "customer_identity_id": (
                resolved_conversation.customer_identity_id
            ),
            "initial_status": status,
        }

        return self.record(
            session,
            workspace_id=resolved_conversation.workspace_id,
            conversation_id=resolved_conversation.conversation_id,
            event_type=ConversationEventType.CONVERSATION_CREATED,
            actor_type=actor_type,
            actor_user_id=actor_user_id,
            details=details,
        )