from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation_event import ConversationEvent


class ConversationEventRepository:

    def add(
        self,
        session: Session,
        event: ConversationEvent,
    ) -> ConversationEvent:

        session.add(event)
        session.flush()

        return event

    def list_for_conversation(
        self,
        session: Session,
        *,
        conversation_id: int,
        workspace_id: int,
    ) -> list[ConversationEvent]:

        statement = (
            select(ConversationEvent)
            .where(
                ConversationEvent.conversation_id == conversation_id,
                ConversationEvent.workspace_id == workspace_id,
            )
            .order_by(
                ConversationEvent.created_at.asc(),
                ConversationEvent.id.asc(),
            )
        )

        return list(
            session.execute(statement).scalars().all()
        )