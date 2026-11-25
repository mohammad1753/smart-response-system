
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IncomingMessage(BaseModel):
    """Normalized incoming message from any messaging platform."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    platform: str = Field(min_length=1)

    external_message_id: str = Field(min_length=1)
    external_chat_id: str = Field(min_length=1)
    external_user_id: str = Field(min_length=1)

    text: str | None = None
    message_type: str = Field(min_length=1)

    media: dict[str, Any] | None = None

    reply_to_message_id: str | None = None

    timestamp: datetime

    raw_data: dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        return value
