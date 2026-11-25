

class MessageProcessingError(Exception):
    """Base exception for message processing operations."""


class ChannelAccountNotFoundError(MessageProcessingError):
    """Raised when the channel account does not exist."""


class InactiveChannelAccountError(MessageProcessingError):
    """Raised when the channel account is inactive."""


class ChannelPlatformMismatchError(MessageProcessingError):
    """Raised when message platform does not match the channel account."""


class CustomerIntegrityError(MessageProcessingError):
    """Raised when customer identity data is inconsistent."""
