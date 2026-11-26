
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation


class ConversationRepository:
    """Database operations for conversations."""

    def get_active_by_identity(
        self,
        session: Session,
        workspace_id: int,
        customer_identity_id: int,
        channel_account_id: int,
        active_statuses: tuple[str, ...],
    ) -> Conversation | None:
        """Find the most recent active conversation."""

        statement = (
            select(Conversation)
            .where(
                Conversation.workspace_id == workspace_id,
                Conversation.customer_identity_id == customer_identity_id,
                Conversation.channel_account_id == channel_account_id,
                Conversation.status.in_(active_statuses),
            )
            .order_by(
                func.coalesce(
                    Conversation.last_message_at,
                    Conversation.created_at,
                ).desc(),
                Conversation.id.desc(),
            )
            .limit(1)
        )

        return session.scalar(statement)

    def add(
        self,
        session: Session,
        conversation: Conversation,
    ) -> Conversation:
        """Add a new conversation and populate its generated ID."""

        session.add(conversation)
        session.flush()

        return conversation
    
    def get_by_id_for_update(
        self,
        session: Session,
        conversation_id: int,
        workspace_id: int,
        channel_account_id: int,
    ) -> Conversation | None:
        """Lock a conversation within its workspace and channel scope."""

        statement = (
            select(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.workspace_id == workspace_id,
                Conversation.channel_account_id == channel_account_id,
            )
            .with_for_update()
        )

        return session.scalar(statement)

