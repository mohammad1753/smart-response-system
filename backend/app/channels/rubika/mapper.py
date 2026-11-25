
from datetime import datetime, timezone
from typing import Any

from rupabik.models.event import Event

from app.channels.base.exceptions import MessageError
from app.channels.schemas import IncomingMessage


class RubikaMessageMapper:
    """Convert RupaBik events into normalized incoming messages."""

    PLATFORM = "rubika"

    @classmethod
    def to_incoming(cls, event: Event) -> IncomingMessage:
        message_id = cls._required_id(
            getattr(event, "message_id", None),
            "message_id",
        )

        chat_id = cls._required_id(
            getattr(event, "object_guid", None),
            "object_guid",
        )

        user_id = cls._required_id(
            getattr(event, "author_guid", None),
            "author_guid",
        )

        timestamp = cls._parse_timestamp(
            getattr(event, "timestamp", None)
        )

        raw_message_type = str(
            getattr(event, "message_type", "") or ""
        )

        file_type = str(
            getattr(event, "file_type", "") or ""
        )

        sticker_data = getattr(event, "sticker_raw", None)
        file_data = getattr(event, "file_inline_raw", None)

        if sticker_data is not None:
            message_type = "sticker"
            media = {
                "type": "sticker",
                "data": sticker_data,
            }

        elif file_type:
            message_type = file_type.strip().lower()
            media = dict(file_data) if isinstance(file_data, dict) else None

        elif raw_message_type:
            message_type = raw_message_type.strip().lower()
            media = None

        else:
            message_type = "unknown"
            media = None

        text = getattr(event, "text", None)

        if text is not None and not isinstance(text, str):
            text = str(text)

        reply_id = getattr(event, "reply_to_message_id", None)

        raw_data = getattr(event, "original_data", {})

        if not isinstance(raw_data, dict):
            raw_data = {}

        # The raw event includes an internal Client reference.
        # Never include that object in the normalized payload.
        raw_data = dict(raw_data)
        raw_data.pop("client", None)
        raw_data.pop("_client", None)

        return IncomingMessage(
            platform=cls.PLATFORM,
            external_message_id=message_id,
            external_chat_id=chat_id,
            external_user_id=user_id,
            text=text,
            message_type=message_type,
            media=media,
            reply_to_message_id=(
                str(reply_id) if reply_id is not None else None
            ),
            timestamp=timestamp,
            raw_data=raw_data,
        )

    @staticmethod
    def _required_id(value: Any, field_name: str) -> str:
        if value is None:
            raise MessageError(
                f"Missing required Rubika field: {field_name}",
                code="RUBIKA_MISSING_FIELD",
            )

        normalized = str(value).strip()

        if not normalized:
            raise MessageError(
                f"Empty Rubika field: {field_name}",
                code="RUBIKA_EMPTY_FIELD",
            )

        return normalized

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        """Convert Rubika timestamps to timezone-aware UTC datetimes."""

        try:
            if isinstance(value, datetime):
                if value.tzinfo is None or value.utcoffset() is None:
                    raise ValueError("Naive datetime is not supported.")

                return value.astimezone(timezone.utc)

            if isinstance(value, (int, float)) and not isinstance(value, bool):
                timestamp = float(value)

                # Rubika timestamps may be in seconds or milliseconds.
                if abs(timestamp) >= 100_000_000_000:
                    timestamp /= 1000

                return datetime.fromtimestamp(
                    timestamp,
                    tz=timezone.utc,
                )

            if isinstance(value, str) and value.strip():
                normalized = value.strip()

                try:
                    return RubikaMessageMapper._parse_timestamp(
                        float(normalized)
                    )
                except ValueError:
                    parsed = datetime.fromisoformat(
                        normalized.replace("Z", "+00:00")
                    )

                    if parsed.tzinfo is None or parsed.utcoffset() is None:
                        raise ValueError(
                            "Timestamp string must include timezone."
                        )

                    return parsed.astimezone(timezone.utc)

        except (ValueError, TypeError, OverflowError, OSError) as exc:
            raise MessageError(
                "Invalid Rubika message timestamp.",
                code="RUBIKA_INVALID_TIMESTAMP",
            ) from exc

        raise MessageError(
            "Rubika message timestamp is missing.",
            code="RUBIKA_MISSING_TIMESTAMP",
        )
