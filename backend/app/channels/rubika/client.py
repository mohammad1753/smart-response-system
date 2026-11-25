
import asyncio
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from rupabik import Client as RupaBikClient
from rupabik.models.event import Event


MessageHandler = Callable[[Event], Awaitable[None]]


class RubikaClientAdapter:
    """Adapter responsible for managing the RupaBik client."""

    def __init__(
        self,
        session_path: str | Path,
        logger: logging.Logger | None = None,
    ) -> None:
        path = Path(session_path).expanduser()

        # RupaBik expects the session base path without .rupabik.
        if path.suffix.lower() == ".rupabik":
            path = path.with_suffix("")

        path.parent.mkdir(parents=True, exist_ok=True)

        self._session_path = path
        self._logger = logger or logging.getLogger(__name__)

        self._rupabik_logger = logging.getLogger(
            "smart_response.rupabik"
        )

        self._rupabik_logger.setLevel(logging.WARNING)
        self._rupabik_logger.propagate = False

        if not self._rupabik_logger.handlers:
            self._rupabik_logger.addHandler(logging.NullHandler())

        self._client: RupaBikClient | None = None
        self._run_task: asyncio.Task[Any] | None = None

    @property
    def is_running(self) -> bool:
        return (
            self._client is not None
            and self._run_task is not None
            and not self._run_task.done()
        )
    

    @property
    def is_connected(self) -> bool:
        """Check whether the RupaBik WebSocket is actually connected."""

        if self._client is None or not self.is_running:
            return False

        connection = getattr(self._client, "connection", None)
        ws = getattr(connection, "ws", None)

        return ws is not None and not ws.closed

    async def _wait_for_websocket(self, timeout: float = 30) -> None:
        """Wait until the WebSocket connection is established."""

        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout

        while loop.time() < deadline:
            if self._run_task is None or self._run_task.done():
                if self._run_task is not None:
                    await self._run_task

                raise RuntimeError(
                    "RupaBik update task stopped before WebSocket connection."
                )

            if self.is_connected:
                return

            await asyncio.sleep(0.1)

        raise TimeoutError(
            "Timed out while waiting for Rubika WebSocket connection."
        )





    async def connect(self, handler: MessageHandler) -> None:
        """Authenticate using the saved session and start updates."""

        if self.is_running:
            return

        await self.disconnect()

        self._client = RupaBikClient(
            session=str(self._session_path),
            logger=self._rupabik_logger,
            continue_on_error=False,
        )

        try:
            # Register the incoming-message handler.
            self._client.on_new_message()(handler)

            # Validate and load the existing saved session.
            await self._client.start()

            if not getattr(self._client, "guid", None):
                raise RuntimeError(
                    "RupaBik session authentication was unsuccessful."
                )

            # Start the WebSocket update loop.
            self._run_task = asyncio.create_task(
                self._client.run(),
                name="rubika-userbot-updates",
            )

            self._run_task.add_done_callback(self._observe_run_task)

            await self._wait_for_websocket()

            if self._run_task.done():
                await self._run_task
                raise RuntimeError(
                    "RupaBik update loop stopped during startup."
                )

        except BaseException:
            await self.disconnect()
            raise

    async def disconnect(self) -> None:
        """Stop the update task and close the RupaBik connection."""

        task = self._run_task
        client = self._client

        self._run_task = None
        self._client = None

        if task is not None:
            if not task.done():
                task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                self._logger.exception(
                    "RupaBik update task ended with an error."
                )

        if client is not None:
            try:
                await client.stop()
            except Exception:
                self._logger.exception(
                    "Error while closing RupaBik connection."
                )

    async def send_text(
        self,
        chat_id: str,
        text: str,
        reply_to_message_id: str | None = None,
    ) -> Any:
        """Send a text message through RupaBik."""

        if self._client is None or not self.is_connected:
            raise RuntimeError("Rubika WebSocket is not connected.")

        return await self._client.dispatch_message(
            chat=chat_id,
            text=text,
            reply_to_message_id=reply_to_message_id,
        )

    def _observe_run_task(self, task: asyncio.Task[Any]) -> None:
        """Observe unexpected errors from the background update task."""

        if task.cancelled():
            return

        error = task.exception()

        if error is not None:
            self._logger.error(
                "RupaBik update loop failed.",
                exc_info=(type(error), error, error.__traceback__),
            )
