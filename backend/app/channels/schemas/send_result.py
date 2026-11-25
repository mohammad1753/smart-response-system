
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SendStatus(str, Enum):
    PENDING = "PENDING"
    SENDING = "SENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class SendResult(BaseModel):
    """Standardized result of an outgoing message operation."""

    model_config = ConfigDict(extra="forbid")

    status: SendStatus

    external_message_id: str | None = None

    timestamp: datetime | None = None

    error_code: str | None = None
    error_message: str | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_timezone(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if value is not None and (
            value.tzinfo is None or value.utcoffset() is None
        ):
            raise ValueError("timestamp must be timezone-aware")
        return value
