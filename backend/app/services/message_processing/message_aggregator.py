
from datetime import datetime

from app.schemas.message_processing import (
    AggregatedMessageBatch,
    ConversationStatus,
    MessageAggregationItem,
    MessageAggregationTrigger,
    MessagePersistenceResult,
    NormalizedIncomingMessage,
    ResolvedConversation,
)

from app.services.message_processing.message_buffer import (
    MessageBuffer,
)


class MessageAggregator:
    """Coordinate persisted messages and conversation buffers."""

    def __init__(
        self,
        message_buffer: MessageBuffer | None = None,
    ) -> None:
        self.buffer = message_buffer or MessageBuffer()

    async def add_persisted_message(
        self,
        persistence_result: MessagePersistenceResult,
        message: NormalizedIncomingMessage,
        conversation: ResolvedConversation,
    ) -> bool:
        """Add a successfully persisted, non-duplicate message.

        Returns True when the message is added to the buffer.
        Returns False when the message was already persisted
        or already exists in the buffer.
        """

        if persistence_result.is_duplicate:
            return False

        if (
            persistence_result.conversation_id
            != conversation.conversation_id
        ):
            raise ValueError(
                "Persisted message conversation does not match "
                "the resolved conversation."
            )

        if (
            persistence_result.external_message_id
            != message.external_message_id
        ):
            raise ValueError(
                "Persisted message external ID does not match "
                "the normalized message."
            )

        if (
            message.channel_account_id
            != conversation.channel_account_id
        ):
            raise ValueError(
                "Message channel account does not match conversation."
            )

        if conversation.status == ConversationStatus.CLOSED:
            raise ValueError(
                "Cannot aggregate a message for a closed conversation."
            )

        item = MessageAggregationItem(
            message_id=persistence_result.message_id,
            external_message_id=message.external_message_id,
            content=message.content,
            message_type=message.message_type,
            media=message.media,
            reply_to_external_message_id=(
                message.reply_to_external_message_id
            ),
            occurred_at=message.occurred_at,
            received_at=message.received_at,
        )

        return await self.buffer.add_message(
            workspace_id=conversation.workspace_id,
            channel_account_id=conversation.channel_account_id,
            conversation_id=conversation.conversation_id,
            message=item,
        )

    async def get_pending_messages(
        self,
        workspace_id: int,
        channel_account_id: int,
        conversation_id: int,
    ) -> list[MessageAggregationItem]:
        """Get messages waiting in a conversation buffer."""

        return await self.buffer.get_messages(
            workspace_id=workspace_id,
            channel_account_id=channel_account_id,
            conversation_id=conversation_id,
        )

    async def get_pending_count(
        self,
        workspace_id: int,
        channel_account_id: int,
        conversation_id: int,
    ) -> int:
        """Get the number of messages waiting for aggregation."""

        return await self.buffer.get_message_count(
            workspace_id=workspace_id,
            channel_account_id=channel_account_id,
            conversation_id=conversation_id,
        )

    async def has_pending_messages(
        self,
        workspace_id: int,
        channel_account_id: int,
        conversation_id: int,
    ) -> bool:
        """Check whether a conversation has pending messages."""

        return await self.buffer.has_messages(
            workspace_id=workspace_id,
            channel_account_id=channel_account_id,
            conversation_id=conversation_id,
        )

    async def finalize_batch(
        self,
        workspace_id: int,
        channel_account_id: int,
        conversation_id: int,
        trigger: MessageAggregationTrigger = (
            MessageAggregationTrigger.MANUAL
        ),
        finalized_at: datetime | None = None,
    ) -> AggregatedMessageBatch | None:
        """Finalize and retrieve a conversation's pending batch."""

        return await self.buffer.flush(
            workspace_id=workspace_id,
            channel_account_id=channel_account_id,
            conversation_id=conversation_id,
            trigger=trigger,
            finalized_at=finalized_at,
        )

    async def clear_pending_messages(
        self,
        workspace_id: int,
        channel_account_id: int,
        conversation_id: int,
    ) -> int:
        """Clear pending messages for a conversation."""

        return await self.buffer.clear(
            workspace_id=workspace_id,
            channel_account_id=channel_account_id,
            conversation_id=conversation_id,
        )
