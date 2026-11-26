
import asyncio

from datetime import datetime, timezone

from app.schemas.message_processing import (
    AggregatedMessageBatch,
    MessageAggregationItem,
    MessageAggregationTrigger,
)


class MessageBuffer:
    """Store incoming persisted messages separately for each conversation."""

    def __init__(self) -> None:
        self._buffers: dict[tuple[int, int, int], list[MessageAggregationItem]] = {}
        self._locks: dict[tuple[int, int, int], asyncio.Lock] = {}

    @staticmethod
    def _get_key(
        workspace_id: int,
        channel_account_id: int,
        conversation_id: int,
    ) -> tuple[int, int, int]:

        if workspace_id <= 0:
            raise ValueError("workspace_id must be greater than zero.")

        if channel_account_id <= 0:
            raise ValueError("channel_account_id must be greater than zero.")

        if conversation_id <= 0:
            raise ValueError("conversation_id must be greater than zero.")

        return (
            workspace_id,
            channel_account_id,
            conversation_id,
        )

    def _get_lock(
        self,
        key: tuple[int, int, int],
    ) -> asyncio.Lock:

        if key not in self._locks:
            self._locks[key] = asyncio.Lock()

        return self._locks[key]

    async def add_message(
        self,
        workspace_id: int,
        channel_account_id: int,
        conversation_id: int,
        message: MessageAggregationItem,
    ) -> bool:
        """Add a message to its conversation buffer.

        Returns False if the message is already present.
        """

        key = self._get_key(
            workspace_id,
            channel_account_id,
            conversation_id,
        )

        lock = self._get_lock(key)

        async with lock:
            messages = self._buffers.setdefault(key, [])

            if any(
                item.message_id == message.message_id
                or item.external_message_id == message.external_message_id
                for item in messages
            ):
                return False

            messages.append(message)

            messages.sort(
                key=lambda item: item.received_at
            )

            return True

    async def get_messages(
        self,
        workspace_id: int,
        channel_account_id: int,
        conversation_id: int,
    ) -> list[MessageAggregationItem]:
        """Return a copy of the buffered messages."""

        key = self._get_key(
            workspace_id,
            channel_account_id,
            conversation_id,
        )

        lock = self._get_lock(key)

        async with lock:
            return list(self._buffers.get(key, []))

    async def get_message_count(
        self,
        workspace_id: int,
        channel_account_id: int,
        conversation_id: int,
    ) -> int:
        """Return the number of messages in a conversation buffer."""

        key = self._get_key(
            workspace_id,
            channel_account_id,
            conversation_id,
        )

        lock = self._get_lock(key)

        async with lock:
            return len(self._buffers.get(key, []))

    async def flush(
        self,
        workspace_id: int,
        channel_account_id: int,
        conversation_id: int,
        trigger: MessageAggregationTrigger,
        finalized_at: datetime | None = None,
    ) -> AggregatedMessageBatch | None:
        """Create a batch and remove its messages from the buffer."""

        key = self._get_key(
            workspace_id,
            channel_account_id,
            conversation_id,
        )

        lock = self._get_lock(key)

        async with lock:
            messages = self._buffers.get(key)

            if not messages:
                return None

            batch_messages = list(messages)

            batch = AggregatedMessageBatch(
                workspace_id=workspace_id,
                channel_account_id=channel_account_id,
                conversation_id=conversation_id,
                messages=batch_messages,
                started_at=batch_messages[0].received_at,
                last_message_at=batch_messages[-1].received_at,
                finalized_at=(
                    finalized_at or datetime.now(timezone.utc)
                ),
                trigger=trigger,
            )

            self._buffers.pop(key, None)

            return batch

    async def clear(
        self,
        workspace_id: int,
        channel_account_id: int,
        conversation_id: int,
    ) -> int:
        """Remove all messages from a conversation buffer.

        Returns the number of removed messages.
        """

        key = self._get_key(
            workspace_id,
            channel_account_id,
            conversation_id,
        )

        lock = self._get_lock(key)

        async with lock:
            messages = self._buffers.pop(key, [])

            return len(messages)

    async def has_messages(
        self,
        workspace_id: int,
        channel_account_id: int,
        conversation_id: int,
    ) -> bool:
        """Check whether a conversation has buffered messages."""

        count = await self.get_message_count(
            workspace_id,
            channel_account_id,
            conversation_id,
        )

        return count > 0
