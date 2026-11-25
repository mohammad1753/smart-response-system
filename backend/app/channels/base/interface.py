from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


from app.channels.schemas import (
    IncomingMessage,
    OutgoingMessage,
    SendResult,
)

class BaseChannelInterface(ABC):
    """Base interface for all messaging platform connectors."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection with the messaging platform."""
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection with the messaging platform."""
        raise NotImplementedError

    @abstractmethod
    async def get_status(self) -> Any:
        """Return current connection status."""
        raise NotImplementedError

    @abstractmethod
    def receive(self) -> AsyncIterator[IncomingMessage]:
        """Yield incoming messages as an asynchronous stream."""
        raise NotImplementedError

    @abstractmethod
    async def send(self, message: OutgoingMessage) -> SendResult:
        """Send an outgoing message to the messaging platform."""
        raise NotImplementedError