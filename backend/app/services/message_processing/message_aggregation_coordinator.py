
import asyncio

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable

from app.schemas.message_processing import (
    AggregatedMessageBatch,
    MessageAggregationTrigger,
    MessagePersistenceResult,
    NormalizedIncomingMessage,
    ResolvedConversation,
)

from app.services.message_processing.message_aggregator import (
    MessageAggregator,
)


BatchCallback = Callable[
    [AggregatedMessageBatch],
    Awaitable[None],
]


@dataclass
class _AggregationState:
    """Runtime state for one conversation aggregation window."""

    started_at: datetime
    last_message_at: datetime
    wake_event: asyncio.Event = field(
        default_factory=asyncio.Event
    )
    task: asyncio.Task | None = None


class MessageAggregationCoordinator:
    """Coordinate message aggregation and debounce scheduling."""

    def __init__(
        self,
        on_batch_ready: BatchCallback,
        aggregator: MessageAggregator | None = None,
        quiet_period: float = 2.0,
        max_batch_wait: float = 10.0,
    ) -> None:

        if quiet_period <= 0:
            raise ValueError("quiet_period must be greater than zero.")

        if max_batch_wait <= 0:
            raise ValueError("max_batch_wait must be greater than zero.")

        if max_batch_wait < quiet_period:
            raise ValueError(
                "max_batch_wait cannot be smaller than quiet_period."
            )

        if not callable(on_batch_ready):
            raise ValueError("on_batch_ready must be callable.")

        self.aggregator = aggregator or MessageAggregator()

        self.on_batch_ready = on_batch_ready

        self.quiet_period = quiet_period
        self.max_batch_wait = max_batch_wait

        self._states: dict[
            tuple[int, int, int],
            _AggregationState,
        ] = {}

        self._locks: dict[
            tuple[int, int, int],
            asyncio.Lock,
        ] = {}

        self._failed_batches: list[
            AggregatedMessageBatch
        ] = []

    @staticmethod
    def _get_key(
        workspace_id: int,
        channel_account_id: int,
        conversation_id: int,
    ) -> tuple[int, int, int]:

        if workspace_id <= 0:
            raise ValueError("workspace_id must be greater than zero.")

        if channel_account_id <= 0:
            raise ValueError(
                "channel_account_id must be greater than zero."
            )

        if conversation_id <= 0:
            raise ValueError(
                "conversation_id must be greater than zero."
            )

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

    async def add_persisted_message(
        self,
        persistence_result: MessagePersistenceResult,
        message: NormalizedIncomingMessage,
        conversation: ResolvedConversation,
    ) -> bool:
        """Add a persisted message and schedule its aggregation.

        Returns True when the message enters the aggregation buffer.
        Returns False for duplicate messages.
        """

        key = self._get_key(
            conversation.workspace_id,
            conversation.channel_account_id,
            conversation.conversation_id,
        )

        lock = self._get_lock(key)

        async with lock:

            added = await self.aggregator.add_persisted_message(
                persistence_result=persistence_result,
                message=message,
                conversation=conversation,
            )

            if not added:
                return False

            now = datetime.now(timezone.utc)

            state = self._states.get(key)

            if state is None:

                state = _AggregationState(
                    started_at=now,
                    last_message_at=now,
                )

                self._states[key] = state

                state.task = asyncio.create_task(
                    self._run_timer(key)
                )

            else:

                state.last_message_at = now
                state.wake_event.set()

            return True

    async def _run_timer(
        self,
        key: tuple[int, int, int],
    ) -> None:
        """Wait for quiet period or maximum batch wait."""

        while True:

            lock = self._get_lock(key)

            async with lock:

                state = self._states.get(key)

                if state is None:
                    return

                now = datetime.now(timezone.utc)

                quiet_deadline = (
                    state.last_message_at
                    + timedelta(seconds=self.quiet_period)
                )

                max_deadline = (
                    state.started_at
                    + timedelta(seconds=self.max_batch_wait)
                )

                quiet_remaining = (
                    quiet_deadline - now
                ).total_seconds()

                max_remaining = (
                    max_deadline - now
                ).total_seconds()

                if max_remaining <= 0:

                    trigger = MessageAggregationTrigger.MAX_WAIT

                elif quiet_remaining <= 0:

                    trigger = MessageAggregationTrigger.QUIET_PERIOD

                else:

                    trigger = None

                if trigger is not None:

                    batch = await self.aggregator.finalize_batch(
                        workspace_id=key[0],
                        channel_account_id=key[1],
                        conversation_id=key[2],
                        trigger=trigger,
                        finalized_at=now,
                    )

                    self._states.pop(key, None)

                    break

                timeout = min(
                    quiet_remaining,
                    max_remaining,
                )

                wake_event = state.wake_event

            try:

                await asyncio.wait_for(
                    wake_event.wait(),
                    timeout=timeout,
                )

                wake_event.clear()

            except asyncio.TimeoutError:
                # Recheck deadlines under the conversation lock.
                # A new message may have arrived at the same time.
                continue

        if batch is not None:
            await self._deliver_batch(batch)

    async def _deliver_batch(
        self,
        batch: AggregatedMessageBatch,
    ) -> None:
        """Deliver a completed batch to the downstream handler."""

        try:

            await self.on_batch_ready(batch)

        except Exception:

            # Keep failed batches available for explicit retry.
            self._failed_batches.append(batch)

    async def flush_now(
        self,
        workspace_id: int,
        channel_account_id: int,
        conversation_id: int,
    ) -> AggregatedMessageBatch | None:
        """Manually finalize a conversation batch."""

        key = self._get_key(
            workspace_id,
            channel_account_id,
            conversation_id,
        )

        lock = self._get_lock(key)

        async with lock:

            state = self._states.pop(key, None)

            if state is not None and state.task is not None:

                current_task = asyncio.current_task()

                if state.task is not current_task:
                    state.task.cancel()

            batch = await self.aggregator.finalize_batch(
                workspace_id=workspace_id,
                channel_account_id=channel_account_id,
                conversation_id=conversation_id,
                trigger=MessageAggregationTrigger.MANUAL,
            )

        if batch is not None:
            await self._deliver_batch(batch)

        return batch

    async def retry_failed_batches(self) -> int:
        """Retry batches whose callback previously failed.

        Returns the number of successfully delivered batches.
        """

        pending = list(self._failed_batches)
        self._failed_batches.clear()

        delivered = 0

        for batch in pending:

            try:

                await self.on_batch_ready(batch)
                delivered += 1

            except Exception:

                self._failed_batches.append(batch)

        return delivered

    def get_failed_batch_count(self) -> int:
        """Return the number of batches awaiting retry."""

        return len(self._failed_batches)

    async def shutdown(self) -> None:
        """Cancel active aggregation timers."""

        tasks = [
            state.task
            for state in self._states.values()
            if state.task is not None
        ]

        for task in tasks:
            task.cancel()

        if tasks:
            await asyncio.gather(
                *tasks,
                return_exceptions=True,
            )

        self._states.clear()
