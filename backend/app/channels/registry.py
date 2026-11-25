
from collections.abc import Callable
from typing import Any

from app.channels.base.interface import BaseChannelInterface
from app.channels.base.platforms import ChannelPlatform


ConnectorFactory = Callable[..., BaseChannelInterface]


class ChannelRegistry:
    """Register and create messaging platform connectors."""

    def __init__(self) -> None:
        self._factories: dict[str, ConnectorFactory] = {}

    @staticmethod
    def _normalize_platform(
        platform: str | ChannelPlatform,
    ) -> str:
        if isinstance(platform, ChannelPlatform):
            value = platform.value
        elif isinstance(platform, str):
            value = platform
        else:
            raise TypeError("Platform must be a string or ChannelPlatform.")

        normalized = value.strip().casefold()

        if not normalized:
            raise ValueError("Platform name cannot be empty.")

        return normalized

    def register(
        self,
        platform: str | ChannelPlatform,
        factory: ConnectorFactory,
        *,
        replace: bool = False,
    ) -> None:
        """Register a connector factory for a platform."""

        key = self._normalize_platform(platform)

        if not callable(factory):
            raise TypeError("Connector factory must be callable.")

        if key in self._factories and not replace:
            raise ValueError(
                f"Connector for '{key}' is already registered."
            )

        self._factories[key] = factory

    def create(
        self,
        platform: str | ChannelPlatform,
        **kwargs: Any,
    ) -> BaseChannelInterface:
        """Create a connector using its registered factory."""

        key = self._normalize_platform(platform)

        factory = self._factories.get(key)

        if factory is None:
            raise ValueError(
                f"No connector registered for platform '{key}'."
            )

        connector = factory(**kwargs)

        if not isinstance(connector, BaseChannelInterface):
            raise TypeError(
                f"Factory for '{key}' did not return a "
                "BaseChannelInterface instance."
            )

        return connector

    def supported_platforms(self) -> tuple[str, ...]:
        """Return registered platform names."""

        return tuple(sorted(self._factories))
