
from sqlalchemy.orm import Session

from app.repositories.message_repository import MessageRepository

from app.schemas.message_processing import (
    NormalizedIncomingMessage,
)


class MessageIdempotencyService:
    """Check whether an incoming message has already been persisted."""

    def __init__(self, message_repository=None) -> None:
        self.messages = message_repository or MessageRepository()

    def is_duplicate(
        self,
        session: Session,
        message: NormalizedIncomingMessage,
    ) -> bool:
        """Return True when the external message already exists."""

        existing = self.messages.get_by_external_id(
            session=session,
            channel_account_id=message.channel_account_id,
            external_message_id=message.external_message_id,
        )

        return existing is not None
