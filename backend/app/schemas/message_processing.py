
from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.channels.schemas import IncomingMessage


class StoredMessageType(str, Enum):
    """Message types supported by the database schema."""

    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"
    STICKER = "STICKER"
    OTHER = "OTHER"


class IncomingMessageEnvelope(BaseModel):
    """Application-level envelope for a message received from a channel."""

    model_config = ConfigDict(extra="forbid")

    channel_account_id: int = Field(gt=0)
    message: IncomingMessage

    received_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("received_at")
    @classmethod
    def validate_received_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("received_at must be timezone-aware")

        return value


class NormalizedIncomingMessage(BaseModel):
    """Platform-independent representation of an incoming message."""

    model_config = ConfigDict(extra="forbid")

    channel_account_id: int = Field(gt=0)

    platform: str = Field(min_length=1)

    external_message_id: str = Field(min_length=1)
    external_chat_id: str = Field(min_length=1)
    external_user_id: str = Field(min_length=1)

    content: str | None = None

    message_type: StoredMessageType

    media: dict | None = None

    reply_to_external_message_id: str | None = None

    occurred_at: datetime
    received_at: datetime

    direction: Literal["INBOUND"] = "INBOUND"
    sender_type: Literal["CUSTOMER"] = "CUSTOMER"
    status: Literal["RECEIVED"] = "RECEIVED"

    raw_data: dict = Field(default_factory=dict)

    @field_validator("occurred_at", "received_at")
    @classmethod
    def validate_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Message timestamps must be timezone-aware")

        return value




class ResolvedCustomer(BaseModel):
    """Result of customer identification."""

    model_config = ConfigDict(extra="forbid")

    workspace_id: int = Field(gt=0)
    channel_account_id: int = Field(gt=0)

    customer_id: int = Field(gt=0)
    customer_identity_id: int = Field(gt=0)

    external_user_id: str = Field(min_length=1)

    customer_created: bool
    identity_created: bool
