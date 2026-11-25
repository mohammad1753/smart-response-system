
from datetime import datetime, timezone

from app.channels.schemas import IncomingMessage
from app.schemas.message_processing import (
    IncomingMessageEnvelope,
    StoredMessageType,
)
from app.services.message_processing.normalizer import MessageNormalizer


def build_envelope(
    message_type: str,
    *,
    text: str | None = None,
    media: dict | None = None,
) -> IncomingMessageEnvelope:

    message = IncomingMessage(
        platform="rubika",
        external_message_id="msg_123",
        external_chat_id="chat_456",
        external_user_id="user_789",
        text=text,
        message_type=message_type,
        media=media,
        timestamp=datetime.now(timezone.utc),
        raw_data={"test": True},
    )

    return IncomingMessageEnvelope(
        channel_account_id=10,
        message=message,
    )


def test_text_normalization():
    envelope = build_envelope(
        "text",
        text="سلام، وقتتون بخیر",
    )

    result = MessageNormalizer.normalize(envelope)

    assert result.message_type == StoredMessageType.TEXT
    assert result.content == "سلام، وقتتون بخیر"
    assert result.direction == "INBOUND"
    assert result.sender_type == "CUSTOMER"
    assert result.status == "RECEIVED"

    print("Text normalization: PASS")


def test_media_type_mapping():
    cases = {
        "image": StoredMessageType.IMAGE,
        "video": StoredMessageType.VIDEO,
        "voice": StoredMessageType.AUDIO,
        "audio": StoredMessageType.AUDIO,
        "music": StoredMessageType.AUDIO,
        "file": StoredMessageType.DOCUMENT,
        "document": StoredMessageType.DOCUMENT,
        "sticker": StoredMessageType.STICKER,
        "gif": StoredMessageType.OTHER,
        "location": StoredMessageType.OTHER,
    }

    for source_type, expected_type in cases.items():
        envelope = build_envelope(
            source_type,
            text=None,
            media={"source": source_type},
        )

        result = MessageNormalizer.normalize(envelope)

        assert result.message_type == expected_type

    print("Media type mapping: PASS")


def test_envelope_context_preservation():
    envelope = build_envelope(
        "text",
        text="سلام",
    )

    result = MessageNormalizer.normalize(envelope)

    assert result.channel_account_id == 10
    assert result.external_chat_id == "chat_456"
    assert result.external_user_id == "user_789"
    assert result.external_message_id == "msg_123"

    print("Envelope context preservation: PASS")


def test_timestamp_preservation():
    envelope = build_envelope(
        "text",
        text="سلام",
    )

    result = MessageNormalizer.normalize(envelope)

    assert result.occurred_at == envelope.message.timestamp
    assert result.received_at == envelope.received_at
    assert result.occurred_at.tzinfo is not None
    assert result.received_at.tzinfo is not None

    print("Timestamp preservation: PASS")


def test_media_and_raw_data_preservation():
    envelope = build_envelope(
        "image",
        text="تصویر محصول",
        media={"file_id": "image_123"},
    )

    result = MessageNormalizer.normalize(envelope)

    assert result.content == "تصویر محصول"
    assert result.media == {"file_id": "image_123"}
    assert result.raw_data == {"test": True}

    print("Media and raw data preservation: PASS")


if __name__ == "__main__":
    test_text_normalization()
    test_media_type_mapping()
    test_envelope_context_preservation()
    test_timestamp_preservation()
    test_media_and_raw_data_preservation()

    print("\nAll message normalizer tests passed.")
