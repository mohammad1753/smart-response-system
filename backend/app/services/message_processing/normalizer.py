
from app.schemas.message_processing import (
    IncomingMessageEnvelope,
    NormalizedIncomingMessage,
    StoredMessageType,
)


class MessageNormalizer:
    """Normalize platform-specific incoming messages."""

    TYPE_MAPPING = {
        "text": StoredMessageType.TEXT,
        "plain_text": StoredMessageType.TEXT,

        "image": StoredMessageType.IMAGE,
        "photo": StoredMessageType.IMAGE,

        "video": StoredMessageType.VIDEO,
        "video_message": StoredMessageType.VIDEO,
        "videomessage": StoredMessageType.VIDEO,

        "voice": StoredMessageType.AUDIO,
        "audio": StoredMessageType.AUDIO,
        "music": StoredMessageType.AUDIO,

        "file": StoredMessageType.DOCUMENT,
        "document": StoredMessageType.DOCUMENT,
        "attachment": StoredMessageType.DOCUMENT,

        "sticker": StoredMessageType.STICKER,
    }

    @classmethod
    def normalize(
        cls,
        envelope: IncomingMessageEnvelope,
    ) -> NormalizedIncomingMessage:
        """Convert an incoming envelope to the internal message schema."""

        message = envelope.message

        raw_type = message.message_type.strip().casefold()
        raw_type = raw_type.replace("-", "_").replace(" ", "_")

        normalized_type = cls.TYPE_MAPPING.get(
            raw_type,
            StoredMessageType.OTHER,
        )

        content = message.text

        if content is not None and not content.strip():
            content = None

        media = (
            dict(message.media)
            if message.media is not None
            else None
        )

        return NormalizedIncomingMessage(
            channel_account_id=envelope.channel_account_id,
            platform=message.platform.casefold(),
            external_message_id=message.external_message_id,
            external_chat_id=message.external_chat_id,
            external_user_id=message.external_user_id,
            content=content,
            message_type=normalized_type,
            media=media,
            reply_to_external_message_id=message.reply_to_message_id,
            occurred_at=message.timestamp,
            received_at=envelope.received_at,
            direction="INBOUND",
            sender_type="CUSTOMER",
            status="RECEIVED",
            raw_data=dict(message.raw_data),
        )
