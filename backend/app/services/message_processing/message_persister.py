
from datetime import timezone

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.message import Message
from app.repositories.message_repository import MessageRepository

from app.schemas.message_processing import (
    ConversationStatus,
    MessagePersistenceResult,
    NormalizedIncomingMessage,
    ResolvedConversation,
)

from app.services.message_processing.exceptions import (
    ConversationScopeMismatchError,
    MessagePersistenceError,
)


class MessagePersister:
    """Persist incoming messages with duplicate protection."""

    def __init__(self, message_repository=None) -> None:
        self.messages = message_repository or MessageRepository()

    def persist(
        self,
        session: Session,
        message: NormalizedIncomingMessage,
        conversation: ResolvedConversation,
    ) -> MessagePersistenceResult:

        if (
            message.channel_account_id
            != conversation.channel_account_id
        ):
            raise ConversationScopeMismatchError(
                "Message channel account does not match conversation."
            )

        # Check duplicates before inserting.
        existing = self.messages.get_by_external_id(
            session=session,
            channel_account_id=message.channel_account_id,
            external_message_id=message.external_message_id,
        )

        if existing is not None:
            return self._duplicate_result(existing, message)

        if conversation.status == ConversationStatus.CLOSED:
            raise ConversationScopeMismatchError(
                "Cannot persist a message into a closed conversation."
            )

        created_at = (
            message.occurred_at
            .astimezone(timezone.utc)
            .replace(tzinfo=None)
        )

        record = Message(
            workspace_id=conversation.workspace_id,
            conversation_id=conversation.conversation_id,
            channel_account_id=conversation.channel_account_id,
            external_message_id=message.external_message_id,
            direction=message.direction,
            sender_type=message.sender_type,
            content=message.content,
            message_type=message.message_type.value,
            status=message.status,
            created_at=created_at,
        )

        try:
            # The savepoint protects the outer transaction from
            # a concurrent duplicate-key violation.
            with session.begin_nested():
                self.messages.add(session, record)

            return MessagePersistenceResult(
                message_id=record.id,
                conversation_id=record.conversation_id,
                external_message_id=record.external_message_id,
                is_duplicate=False,
            )

        except IntegrityError:
            # Another worker may have inserted the same message.
            existing = self.messages.get_by_external_id(
                session=session,
                channel_account_id=message.channel_account_id,
                external_message_id=message.external_message_id,
            )

            if existing is not None:
                return self._duplicate_result(existing, message)

            raise

        except SQLAlchemyError as exc:
            raise MessagePersistenceError(
                "Database error while persisting incoming message."
            ) from exc

    @staticmethod
    def _duplicate_result(
        existing: Message,
        message: NormalizedIncomingMessage,
    ) -> MessagePersistenceResult:

        if (
            existing.workspace_id is None
            or existing.channel_account_id != message.channel_account_id
            or existing.external_message_id != message.external_message_id
        ):
            raise MessagePersistenceError(
                "Existing message does not match the expected identity."
            )

        return MessagePersistenceResult(
            message_id=existing.id,
            conversation_id=existing.conversation_id,
            external_message_id=existing.external_message_id,
            is_duplicate=True,
        )
