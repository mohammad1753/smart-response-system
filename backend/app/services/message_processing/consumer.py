
import logging
from collections.abc import Awaitable, Callable

from app.channels.base.interface import BaseChannelInterface
from app.channels.schemas import IncomingMessage
from app.schemas.message_processing import IncomingMessageEnvelope


MessageProcessor = Callable[
    [IncomingMessageEnvelope],
    Awaitable[None],
]


class ConnectorMessageConsumer:
    """Consume incoming messages from a channel connector."""

    def __init__(
        self,
        channel_account_id: int,
        connector: BaseChannelInterface,
        processor: MessageProcessor,
        logger: logging.Logger | None = None,
    ) -> None:
        if channel_account_id <= 0:
            raise ValueError("channel_account_id must be positive.")

        if not isinstance(connector, BaseChannelInterface):
            raise TypeError(
                "connector must implement BaseChannelInterface."
            )

        self.channel_account_id = channel_account_id
        self.connector = connector
        self.processor = processor
        self.logger = logger or logging.getLogger(__name__)

    async def run(self) -> None:
        """Connect, consume messages, and disconnect on shutdown."""

        self.logger.info(
            "Starting message consumer for channel account %s.",
            self.channel_account_id,
        )

        try:
            await self.connector.connect()

            self.logger.info(
                "Channel connected for account %s.",
                self.channel_account_id,
            )

            async for message in self.connector.receive():
                if not isinstance(message, IncomingMessage):
                    raise TypeError(
                        "Connector returned an invalid incoming message."
                    )

                envelope = IncomingMessageEnvelope(
                    channel_account_id=self.channel_account_id,
                    message=message,
                )

                await self.processor(envelope)

        except Exception:
            self.logger.exception(
                "Message consumer failed for channel account %s.",
                self.channel_account_id,
            )
            raise

        finally:
            await self.connector.disconnect()

            self.logger.info(
                "Message consumer stopped for channel account %s.",
                self.channel_account_id,
            )
