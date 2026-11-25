
import asyncio
import logging
from collections.abc import AsyncIterator, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.channels.base.exceptions import (
    AuthenticationError,
    ChannelError,
    ConnectionError as ChannelConnectionError,
    MessageError,
    RateLimitError,
)
from app.channels.base.interface import BaseChannelInterface
from app.channels.rubika.client import RubikaClientAdapter
from app.channels.rubika.mapper import RubikaMessageMapper
from app.channels.schemas import (
    IncomingMessage,
    OutgoingMessage,
    SendResult,
    SendStatus,
)



from rupabik.errors import (
    AuthError as RupaBikAuthError,
    CodeIsExpired as RupaBikCodeIsExpired,
    CodeIsUsed as RupaBikCodeIsUsed,
    InvalidAccess as RupaBikInvalidAccess,
    InvalidChatInput as RupaBikInvalidChatInput,
    InvalidInput as RupaBikInvalidInput,
    MaxRetriesError as RupaBikMaxRetriesError,
    NetworkError as RupaBikNetworkError,
    NoConnection as RupaBikNoConnection,
    NotRegistered as RupaBikNotRegistered,
    ProxyError as RupaBikProxyError,
    SessionError as RupaBikSessionError,
    TimeoutError as RupaBikTimeoutError,
    TooRequests as RupaBikTooRequests,
    Undeliverable as RupaBikUndeliverable,
)




def _translate_rubika_error(exc: Exception) -> ChannelError:
    """Translate RupaBik exceptions into application-level exceptions."""

    if isinstance(exc, ChannelError):
        return exc

    message = str(exc) or "Unknown Rubika error."

    # Authentication and session errors
    if isinstance(
        exc,
        (
            RupaBikAuthError,
            RupaBikCodeIsExpired,
            RupaBikCodeIsUsed,
            RupaBikInvalidAccess,
            RupaBikNotRegistered,
            RupaBikSessionError,
        ),
    ):
        return AuthenticationError(message)

    # Rate-limit errors
    if isinstance(exc, RupaBikTooRequests):
        return RateLimitError(
            message,
            retryable=True,
        )

    # Connection and transport errors
    if isinstance(
        exc,
        (
            RupaBikNetworkError,
            RupaBikNoConnection,
            RupaBikTimeoutError,
            RupaBikProxyError,
            RupaBikMaxRetriesError,
        ),
    ):
        return ChannelConnectionError(
            message,
            retryable=True,
        )

    # Message and recipient errors
    if isinstance(
        exc,
        (
            RupaBikInvalidChatInput,
            RupaBikInvalidInput,
            RupaBikUndeliverable,
        ),
    ):
        return MessageError(
            message,
            code=f"RUBIKA_{type(exc).__name__.upper()}",
            retryable=False,
        )

    # Unknown RupaBik errors
    return ChannelError(
        message,
        code=f"RUBIKA_{type(exc).__name__.upper()}",
        retryable=False,
    )


class RubikaConnector(BaseChannelInterface):
    """Rubika Userbot connector implemented with RupaBik."""

    def __init__(
        self,
        session_path: str | Path,
        *,
        queue_maxsize: int = 1000,
        logger: logging.Logger | None = None,
    ) -> None:
        if queue_maxsize < 0:
            raise ValueError("queue_maxsize cannot be negative.")

        self._logger = logger or logging.getLogger(__name__)

        self._client = RubikaClientAdapter(
            session_path=session_path,
            logger=self._logger,
        )

        self._incoming_queue: asyncio.Queue[IncomingMessage] = (
            asyncio.Queue(maxsize=queue_maxsize)
        )

        self._connected = False
        self._lifecycle_lock = asyncio.Lock()

    async def connect(self) -> None:
        """Connect using the saved Rubika user session."""

        async with self._lifecycle_lock:
            if await self.get_status() == "connected":
                return

            try:
                await self._client.connect(
                    handler=self._handle_new_message
                )
                self._connected = True

            except Exception as exc:
                self._connected = False
                translated = _translate_rubika_error(exc)
                raise translated from exc

    async def disconnect(self) -> None:
        """Stop receiving messages and disconnect from Rubika."""

        async with self._lifecycle_lock:
            self._connected = False
            await self._client.disconnect()

    async def get_status(self) -> str:
        if not self._connected:
            return "disconnected"

        if self._client.is_connected:
            return "connected"

        if self._client.is_running:
            return "reconnecting"

        return "error"

    async def receive(self) -> AsyncIterator[IncomingMessage]:
        """Yield normalized incoming messages."""

        if not self._connected and self._incoming_queue.empty():
            raise ChannelConnectionError(
                "Rubika connector is not running.",
                retryable=False,
            )

        while (
            (self._connected and self._client.is_running)
            or not self._incoming_queue.empty()
        ):
            try:
                message = await asyncio.wait_for(
                    self._incoming_queue.get(),
                    timeout=0.5,
                )
            except asyncio.TimeoutError:
                continue

            yield message

    async def send(self, message: OutgoingMessage) -> SendResult:
        """Send a normalized text message through Rubika."""

        if await self.get_status() != "connected":
            raise ChannelConnectionError(
                "Cannot send message: Rubika is not connected."
            )

        if message.platform.casefold() != "rubika":
            raise MessageError(
                "Outgoing message platform must be rubika.",
                code="INVALID_PLATFORM",
            )

        if message.media is not None:
            raise MessageError(
                "Media sending is not implemented in this connector version.",
                code="UNSUPPORTED_MEDIA",
            )

        if message.message_type.casefold() != "text":
            raise MessageError(
                "Only text messages are currently supported.",
                code="UNSUPPORTED_MESSAGE_TYPE",
            )

        if not message.text:
            raise MessageError(
                "Text message content cannot be empty.",
                code="EMPTY_MESSAGE",
            )

        try:
            result = await self._client.send_text(
                chat_id=message.external_chat_id,
                text=message.text,
                reply_to_message_id=message.reply_to_message_id,
            )

        except Exception as exc:
            translated = _translate_rubika_error(exc)

            if isinstance(
                translated,
                (
                    AuthenticationError,
                    ChannelConnectionError,
                    RateLimitError,
                ),
            ):
                raise translated from exc

            return SendResult(
                status=SendStatus.FAILED,
                timestamp=datetime.now(timezone.utc),
                error_code=translated.code,
                error_message=translated.message,
            )

        if result is None:
            return SendResult(
                status=SendStatus.FAILED,
                timestamp=datetime.now(timezone.utc),
                error_code="RUBIKA_EMPTY_RESPONSE",
                error_message="Rubika returned an empty send response.",
            )

        return SendResult(
            status=SendStatus.SENT,
            external_message_id=self._extract_message_id(result),
            timestamp=datetime.now(timezone.utc),
        )

    async def _handle_new_message(self, event: Any) -> None:
        """Normalize a RupaBik event and put it in the incoming queue."""

        try:
            # Prevent processing messages sent by this same account.
            if getattr(event, "is_me", False):
                return

            message = RubikaMessageMapper.to_incoming(event)

            await self._incoming_queue.put(message)

        except MessageError as exc:
            self._logger.warning(
                "Rubika event could not be normalized: %s",
                exc.message,
            )

        except Exception:
            self._logger.exception(
                "Unexpected error while processing a Rubika event."
            )

    @staticmethod
    def _extract_message_id(result: Any) -> str | None:
        """Find a message_id in the RupaBik response, if available."""

        if hasattr(result, "to_dict"):
            result = result.to_dict()

        def find_id(value: Any) -> str | None:
            if isinstance(value, Mapping):
                message_id = value.get("message_id")

                if isinstance(message_id, (str, int)):
                    return str(message_id)

                for child in value.values():
                    found = find_id(child)

                    if found is not None:
                        return found

            elif isinstance(value, (list, tuple)):
                for child in value:
                    found = find_id(child)

                    if found is not None:
                        return found

            return None

        return find_id(result)
