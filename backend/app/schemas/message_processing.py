
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




class ConversationStatus(str, Enum):
    """Conversation statuses supported by the database."""

    AI_ACTIVE = "AI_ACTIVE"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"
    HUMAN_ACTIVE = "HUMAN_ACTIVE"
    CLOSED = "CLOSED"


class ResolvedConversation(BaseModel):
    """Result of conversation identification or creation."""

    model_config = ConfigDict(extra="forbid")

    workspace_id: int = Field(gt=0)
    channel_account_id: int = Field(gt=0)

    customer_id: int = Field(gt=0)
    customer_identity_id: int = Field(gt=0)
    conversation_id: int = Field(gt=0)

    status: ConversationStatus

    conversation_created: bool





class MessagePersistenceResult(BaseModel):
    """Result of an idempotent message persistence operation."""

    model_config = ConfigDict(extra="forbid")

    message_id: int = Field(gt=0)
    conversation_id: int = Field(gt=0)

    external_message_id: str = Field(min_length=1)

    is_duplicate: bool





class ConversationEventType(str, Enum):
    CONVERSATION_CREATED = "CONVERSATION_CREATED"
    AI_ENABLED = "AI_ENABLED"
    AI_DISABLED = "AI_DISABLED"
    HANDOFF_REQUESTED = "HANDOFF_REQUESTED"
    ASSIGNED_TO_OPERATOR = "ASSIGNED_TO_OPERATOR"
    OPERATOR_REPLIED = "OPERATOR_REPLIED"
    RETURNED_TO_AI = "RETURNED_TO_AI"
    CONVERSATION_CLOSED = "CONVERSATION_CLOSED"
    CONVERSATION_REOPENED = "CONVERSATION_REOPENED"


class ConversationActorType(str, Enum):
    SYSTEM = "SYSTEM"
    AI = "AI"
    OPERATOR = "OPERATOR"
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"



class MessageAggregationTrigger(str, Enum):
    """Reason why a message batch was finalized."""

    QUIET_PERIOD = "QUIET_PERIOD"
    MAX_WAIT = "MAX_WAIT"
    MANUAL = "MANUAL"


class MessageAggregationItem(BaseModel):
    """A persisted incoming message included in an aggregation batch."""

    model_config = ConfigDict(extra="forbid")

    message_id: int = Field(gt=0)
    external_message_id: str = Field(min_length=1)

    content: str | None = None

    message_type: StoredMessageType

    media: dict | None = None

    reply_to_external_message_id: str | None = None

    occurred_at: datetime
    received_at: datetime

    @field_validator("occurred_at", "received_at")
    @classmethod
    def validate_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Message timestamps must be timezone-aware")

        return value


class AggregatedMessageBatch(BaseModel):
    """A group of messages ready for downstream processing."""

    model_config = ConfigDict(extra="forbid")

    workspace_id: int = Field(gt=0)
    channel_account_id: int = Field(gt=0)
    conversation_id: int = Field(gt=0)

    messages: list[MessageAggregationItem] = Field(min_length=1)

    started_at: datetime
    last_message_at: datetime
    finalized_at: datetime

    trigger: MessageAggregationTrigger

    @field_validator(
        "started_at",
        "last_message_at",
        "finalized_at",
    )
    @classmethod
    def validate_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Batch timestamps must be timezone-aware")

        return value

    @property
    def message_ids(self) -> list[int]:
        """Return the database IDs of all messages in the batch."""

        return [message.message_id for message in self.messages]

    @property
    def combined_text(self) -> str:
        """Combine non-empty text contents in their original order."""

        return "\n".join(
            message.content.strip()
            for message in self.messages
            if message.content and message.content.strip()
        )

