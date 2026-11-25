
class ChannelError(Exception):
    """Base exception for all channel-related errors."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "CHANNEL_ERROR",
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.retryable = retryable


class ConnectionError(ChannelError):
    """Raised when channel connection fails."""

    def __init__(
        self,
        message: str = "Channel connection failed",
        *,
        retryable: bool = True,
    ) -> None:
        super().__init__(
            message,
            code="CONNECTION_ERROR",
            retryable=retryable,
        )


class AuthenticationError(ChannelError):
    """Raised when channel authentication fails."""

    def __init__(
        self,
        message: str = "Channel authentication failed",
    ) -> None:
        super().__init__(
            message,
            code="AUTHENTICATION_ERROR",
            retryable=False,
        )


class RateLimitError(ChannelError):
    """Raised when channel rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Channel rate limit exceeded",
        *,
        retryable: bool = True,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(
            message,
            code="RATE_LIMIT_ERROR",
            retryable=retryable,
        )
        self.retry_after = retry_after


class MessageError(ChannelError):
    """Raised when message sending or receiving fails."""

    def __init__(
        self,
        message: str = "Channel message operation failed",
        *,
        code: str = "MESSAGE_ERROR",
        retryable: bool = False,
    ) -> None:
        super().__init__(
            message,
            code=code,
            retryable=retryable,
        )
