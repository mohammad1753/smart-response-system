
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.message import Message


class MessageRepository:
    """Database operations for messages."""

    def get_by_external_id(
        self,
        session: Session,
        channel_account_id: int,
        external_message_id: str,
    ) -> Message | None:

        statement = select(Message).where(
            Message.channel_account_id == channel_account_id,
            Message.external_message_id == external_message_id,
        )

        return session.scalar(statement)

    def add(
        self,
        session: Session,
        message: Message,
    ) -> Message:

        session.add(message)
        session.flush()

        return message
