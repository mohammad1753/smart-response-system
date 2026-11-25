
from collections.abc import AsyncIterator

from app.channels.base.interface import BaseChannelInterface
from app.channels.base.platforms import ChannelPlatform
from app.channels.registry import ChannelRegistry
from app.channels.schemas import (
    IncomingMessage,
    OutgoingMessage,
    SendResult,
    SendStatus,
)


class DummyConnector(BaseChannelInterface):

    def __init__(self, label: str):
        self.label = label

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    async def get_status(self) -> str:
        return "connected"

    async def receive(self) -> AsyncIterator[IncomingMessage]:
        if False:
            yield None

    async def send(self, message: OutgoingMessage) -> SendResult:
        return SendResult(status=SendStatus.SENT)


def main():
    registry = ChannelRegistry()

    registry.register(ChannelPlatform.RUBIKA, DummyConnector)
    registry.register(ChannelPlatform.BALE, DummyConnector)
    registry.register(ChannelPlatform.EITAA, DummyConnector)

    expected = ("bale", "eitaa", "rubika")

    assert registry.supported_platforms() == expected
    print("Platform registration: PASS")

    connector = registry.create(
        "RUBIKA",
        label="test_connector",
    )

    assert isinstance(connector, BaseChannelInterface)
    assert connector.label == "test_connector"
    print("Connector creation: PASS")

    try:
        registry.register("rubika", DummyConnector)
    except ValueError:
        print("Duplicate registration protection: PASS")
    else:
        raise AssertionError("Duplicate registration was not rejected.")

    try:
        registry.create("unknown")
    except ValueError:
        print("Unsupported platform handling: PASS")
    else:
        raise AssertionError("Unknown platform was not rejected.")

    print("\nAll channel registry tests passed.")


if __name__ == "__main__":
    main()



# python -c "import runpy; runpy.run_path('test/channel_registry_test.py', run_name='__main__')"