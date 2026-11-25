
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OutgoingMessage(BaseModel):
    """Normalized outgoing message for any messaging platform."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    platform: str = Field(min_length=1)
    external_chat_id: str = Field(min_length=1)

    text: str | None = Field(default=None, min_length=1)
    message_type: str = Field(min_length=1)

    media: dict[str, Any] | None = None

    reply_to_message_id: str | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_message_content(self):
        if self.text is None and self.media is None:
            raise ValueError(
                "Outgoing message must contain text or media"
            )
        return self
