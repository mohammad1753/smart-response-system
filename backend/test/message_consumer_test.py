
import asyncio
from collections.abc import AsyncIterator
from datetime import datetime, timezone

from app.channels.base.interface import BaseChannelInterface
from app.channels.schemas import IncomingMessage, SendResult, SendStatus
from app.schemas.message_processing import IncomingMessageEnvelope
from app.services.message_processing.consumer import (
    ConnectorMessageConsumer,
)


class FakeConnector(BaseChannelInterface):

    def __init__(self, message: IncomingMessage):
        self.message = message
        self.connected = False
        self.disconnected = False

    async def connect(self) -> None:
        self.connected = True

    async def disconnect(self) -> None:
        self.disconnected = True

    async def get_status(self) -> str:
        return "connected" if self.connected else "disconnected"

    async def receive(self) -> AsyncIterator[IncomingMessage]:
        yield self.message

    async def send(self, message) -> SendResult:
        return SendResult(status=SendStatus.SENT)


async def main():
    message = IncomingMessage(
        platform="rubika",
        external_message_id="test_123",
        external_chat_id="chat_456",
        external_user_id="user_789",
        text="سلام",
        message_type="text",
        timestamp=datetime.now(timezone.utc),
    )

    # Test Envelope validation
    envelope = IncomingMessageEnvelope(
        channel_account_id=10,
        message=message,
    )

    assert envelope.channel_account_id == 10
    assert envelope.message.external_message_id == "test_123"
    assert envelope.received_at.tzinfo is not None

    print("Envelope validation: PASS")

    # Test invalid account ID
    try:
        IncomingMessageEnvelope(
            channel_account_id=0,
            message=message,
        )
    except Exception:
        print("Invalid account ID protection: PASS")
    else:
        raise AssertionError("Invalid account ID was accepted.")

    # Test Consumer
    connector = FakeConnector(message)
    processed_messages = []

    async def processor(envelope: IncomingMessageEnvelope) -> None:
        processed_messages.append(envelope)

    consumer = ConnectorMessageConsumer(
        channel_account_id=10,
        connector=connector,
        processor=processor,
    )

    await consumer.run()

    assert connector.connected
    assert connector.disconnected
    assert len(processed_messages) == 1

    processed = processed_messages[0]

    assert processed.channel_account_id == 10
    assert processed.message.text == "سلام"

    print("Connector connection: PASS")
    print("Message consumption: PASS")
    print("Envelope delivery: PASS")
    print("Connector disconnection: PASS")

    print("\nAll message consumer tests passed.")


if __name__ == "__main__":
    asyncio.run(main())
