
from pathlib import Path

from rupabik.data import Data
from rupabik.errors import (
    AuthError,
    InvalidChatInput,
    InvalidInput,
    NetworkError,
    NoConnection,
    NotRegistered,
    TooRequests,
    Undeliverable,
)
from rupabik.models.event import Event

from app.channels.base.exceptions import (
    AuthenticationError,
    ConnectionError as ChannelConnectionError,
    ChannelError,
    MessageError,
    RateLimitError,
)
from app.channels.rubika import RubikaConnector
from app.channels.rubika.connector import _translate_rubika_error
from app.channels.rubika.mapper import RubikaMessageMapper


def test_error_mapping():
    cases = [
        (NotRegistered("test"), AuthenticationError),
        (AuthError("test"), AuthenticationError),
        (TooRequests("test"), RateLimitError),
        (NetworkError("test"), ChannelConnectionError),
        (NoConnection("test"), ChannelConnectionError),
        (InvalidInput("test"), MessageError),
        (InvalidChatInput("test"), MessageError),
        (Undeliverable("test"), MessageError),
    ]

    for original, expected in cases:
        translated = _translate_rubika_error(original)
        assert isinstance(translated, expected)

    unknown = _translate_rubika_error(RuntimeError("test"))

    assert isinstance(unknown, ChannelError)
    assert unknown.code == "RUBIKA_RUNTIMEERROR"

    print("Error mapping: PASS")


def test_event_mapper():
    raw = {
        "action": "New",
        "type": "Message",
        "message_id": "test_message",
        "object_guid": "u0_test_chat",
        "timestamp": 1764000000000,
        "user_guid": "u0_test_chat",
        "message": {
            "text": "Test message",
            "author_object_guid": "u0_test_user",
            "type": "Text",
        },
    }

    event = Event(raw)
    message = RubikaMessageMapper.to_incoming(event)

    assert message.platform == "rubika"
    assert message.external_message_id == "test_message"
    assert message.external_chat_id == "u0_test_chat"
    assert message.external_user_id == "u0_test_user"
    assert message.text == "Test message"
    assert message.timestamp.tzinfo is not None

    print("Event mapper: PASS")


def test_message_id_extraction():
    response = Data({
        "message_id": "test_sent_message",
    })

    message_id = RubikaConnector._extract_message_id(response)

    assert message_id == "test_sent_message"

    print("Message ID extraction: PASS")


def test_connector_initialization():
    connector = RubikaConnector(
        session_path=(
            Path.home()
            / ".smart_response_system"
            / "sessions"
            / "rubika_primary"
        )
    )

    assert not connector._connected
    assert connector._client.is_running is False

    print("Connector initialization: PASS")


if __name__ == "__main__":
    test_error_mapping()
    test_event_mapper()
    test_message_id_extraction()
    test_connector_initialization()

    print("\nAll Rubika connector regression tests passed.")












# python -c "import runpy; runpy.run_path('test/rubika_connector_unit_test.py', run_name='__main__')"
