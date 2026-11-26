
import asyncio

from datetime import datetime, timezone

from app.schemas.message_processing import (
    ConversationStatus,
    MessageAggregationTrigger,
    MessagePersistenceResult,
    NormalizedIncomingMessage,
    ResolvedConversation,
    StoredMessageType,
)

from app.services.message_processing.message_aggregator import (
    MessageAggregator,
)

from app.services.message_processing.message_aggregation_coordinator import (
    MessageAggregationCoordinator,
)


def build_message(message_number: int):

    now = datetime.now(timezone.utc)

    return NormalizedIncomingMessage(
        channel_account_id=1,
        platform="RUBIKA",
        external_message_id=f"external-{message_number}",
        external_chat_id="chat-100",
        external_user_id="user-100",
        content=f"Test message {message_number}",
        message_type=StoredMessageType.TEXT,
        occurred_at=now,
        received_at=now,
    )


def build_conversation(
    conversation_id: int = 10,
    workspace_id: int = 1,
    channel_account_id: int = 1,
):

    return ResolvedConversation(
        workspace_id=workspace_id,
        channel_account_id=channel_account_id,
        customer_id=20,
        customer_identity_id=30,
        conversation_id=conversation_id,
        status=ConversationStatus.AI_ACTIVE,
        conversation_created=False,
    )


def build_persistence_result(
    message_number: int,
    conversation_id: int = 10,
    is_duplicate: bool = False,
):

    return MessagePersistenceResult(
        message_id=message_number,
        conversation_id=conversation_id,
        external_message_id=f"external-{message_number}",
        is_duplicate=is_duplicate,
    )


async def test_quiet_period_aggregation():

    received_batches = []
    completed = asyncio.Event()

    async def on_batch_ready(batch):
        received_batches.append(batch)
        completed.set()

    coordinator = MessageAggregationCoordinator(
        on_batch_ready=on_batch_ready,
        quiet_period=0.05,
        max_batch_wait=0.3,
    )

    conversation = build_conversation()

    try:

        for number in (1, 2, 3):

            added = await coordinator.add_persisted_message(
                persistence_result=build_persistence_result(number),
                message=build_message(number),
                conversation=conversation,
            )

            assert added is True

            if number < 3:
                await asyncio.sleep(0.02)

        await asyncio.wait_for(
            completed.wait(),
            timeout=1.0,
        )

        assert len(received_batches) == 1

        batch = received_batches[0]

        assert batch.message_ids == [1, 2, 3]

        assert batch.trigger == (
            MessageAggregationTrigger.QUIET_PERIOD
        )

        assert batch.combined_text == (
            "Test message 1\n"
            "Test message 2\n"
            "Test message 3"
        )

        print("Quiet period aggregation: PASS")

    finally:
        await coordinator.shutdown()


async def test_duplicate_message_protection():

    received_batches = []

    async def on_batch_ready(batch):
        received_batches.append(batch)

    coordinator = MessageAggregationCoordinator(
        on_batch_ready=on_batch_ready,
        quiet_period=0.1,
        max_batch_wait=0.5,
    )

    conversation = build_conversation()

    try:

        added = await coordinator.add_persisted_message(
            persistence_result=build_persistence_result(1),
            message=build_message(1),
            conversation=conversation,
        )

        assert added is True

        duplicate_added = await coordinator.add_persisted_message(
            persistence_result=build_persistence_result(
                1,
                is_duplicate=True,
            ),
            message=build_message(1),
            conversation=conversation,
        )

        assert duplicate_added is False

        count = await coordinator.aggregator.get_pending_count(
            workspace_id=1,
            channel_account_id=1,
            conversation_id=10,
        )

        assert count == 1

        print("Duplicate message protection: PASS")

    finally:
        await coordinator.shutdown()


async def test_conversation_isolation():

    received_batches = []
    completed = asyncio.Event()

    async def on_batch_ready(batch):

        received_batches.append(batch)

        if len(received_batches) == 2:
            completed.set()

    coordinator = MessageAggregationCoordinator(
        on_batch_ready=on_batch_ready,
        quiet_period=0.05,
        max_batch_wait=0.3,
    )

    conversation_one = build_conversation(
        conversation_id=10,
    )

    conversation_two = build_conversation(
        conversation_id=11,
    )

    try:

        await coordinator.add_persisted_message(
            persistence_result=build_persistence_result(
                1,
                conversation_id=10,
            ),
            message=build_message(1),
            conversation=conversation_one,
        )

        await coordinator.add_persisted_message(
            persistence_result=build_persistence_result(
                2,
                conversation_id=11,
            ),
            message=build_message(2),
            conversation=conversation_two,
        )

        await asyncio.wait_for(
            completed.wait(),
            timeout=1.0,
        )

        assert len(received_batches) == 2

        batches_by_conversation = {
            batch.conversation_id: batch
            for batch in received_batches
        }

        assert batches_by_conversation[10].message_ids == [1]
        assert batches_by_conversation[11].message_ids == [2]

        print("Conversation isolation: PASS")

    finally:
        await coordinator.shutdown()


async def test_maximum_batch_wait():

    received_batches = []
    completed = asyncio.Event()

    async def on_batch_ready(batch):
        received_batches.append(batch)
        completed.set()

    coordinator = MessageAggregationCoordinator(
        on_batch_ready=on_batch_ready,
        quiet_period=0.08,
        max_batch_wait=0.16,
    )

    conversation = build_conversation()

    try:

        for number in range(1, 5):

            added = await coordinator.add_persisted_message(
                persistence_result=build_persistence_result(number),
                message=build_message(number),
                conversation=conversation,
            )

            assert added is True

            if number < 4:
                await asyncio.sleep(0.04)

        await asyncio.wait_for(
            completed.wait(),
            timeout=1.0,
        )

        assert len(received_batches) == 1

        batch = received_batches[0]

        assert batch.trigger == (
            MessageAggregationTrigger.MAX_WAIT
        )

        assert batch.message_ids == [1, 2, 3, 4]

        print("Maximum batch wait: PASS")

    finally:
        await coordinator.shutdown()


async def test_manual_flush():

    received_batches = []

    async def on_batch_ready(batch):
        received_batches.append(batch)

    coordinator = MessageAggregationCoordinator(
        on_batch_ready=on_batch_ready,
        quiet_period=1.0,
        max_batch_wait=2.0,
    )

    conversation = build_conversation()

    try:

        await coordinator.add_persisted_message(
            persistence_result=build_persistence_result(1),
            message=build_message(1),
            conversation=conversation,
        )

        batch = await coordinator.flush_now(
            workspace_id=1,
            channel_account_id=1,
            conversation_id=10,
        )

        assert batch is not None

        assert batch.trigger == (
            MessageAggregationTrigger.MANUAL
        )

        assert batch.message_ids == [1]

        assert len(received_batches) == 1

        print("Manual batch flush: PASS")

    finally:
        await coordinator.shutdown()


async def test_failed_callback_retry():

    callback_calls = 0
    received_batches = []

    async def on_batch_ready(batch):

        nonlocal callback_calls

        callback_calls += 1

        if callback_calls == 1:
            raise RuntimeError("Simulated downstream failure.")

        received_batches.append(batch)

    coordinator = MessageAggregationCoordinator(
        on_batch_ready=on_batch_ready,
        quiet_period=1.0,
        max_batch_wait=2.0,
    )

    conversation = build_conversation()

    try:

        await coordinator.add_persisted_message(
            persistence_result=build_persistence_result(1),
            message=build_message(1),
            conversation=conversation,
        )

        await coordinator.flush_now(
            workspace_id=1,
            channel_account_id=1,
            conversation_id=10,
        )

        assert coordinator.get_failed_batch_count() == 1

        retried = await coordinator.retry_failed_batches()

        assert retried == 1

        assert coordinator.get_failed_batch_count() == 0

        assert len(received_batches) == 1

        assert received_batches[0].message_ids == [1]

        print("Failed callback retry: PASS")

    finally:
        await coordinator.shutdown()


async def test_invalid_timing_configuration():

    async def on_batch_ready(batch):
        pass

    try:

        MessageAggregationCoordinator(
            on_batch_ready=on_batch_ready,
            quiet_period=5.0,
            max_batch_wait=2.0,
        )

    except ValueError:
        print("Invalid timing configuration: PASS")

    else:
        raise AssertionError(
            "Invalid timing configuration was accepted."
        )


def run_all_tests():

    asyncio.run(test_quiet_period_aggregation())

    asyncio.run(test_duplicate_message_protection())

    asyncio.run(test_conversation_isolation())

    asyncio.run(test_maximum_batch_wait())

    asyncio.run(test_manual_flush())

    asyncio.run(test_failed_callback_retry())

    asyncio.run(test_invalid_timing_configuration())

    print()
    print("All message aggregation tests passed.")


if __name__ == "__main__":
    run_all_tests()
