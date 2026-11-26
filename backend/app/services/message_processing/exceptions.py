

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




class CustomerIdentityNotFoundError(MessageProcessingError):
    """Raised when the resolved customer identity cannot be found."""


class ConversationIntegrityError(MessageProcessingError):
    """Raised when conversation data violates expected integrity."""





class ConversationScopeMismatchError(MessageProcessingError):
    """Raised when a message and conversation have different scopes."""


class UnsupportedMessagePayloadError(MessageProcessingError):
    """Raised when the current database schema cannot persist a payload."""


class MessagePersistenceError(MessageProcessingError):
    """Raised when message persistence fails."""



class ConversationNotFoundError(MessageProcessingError):
    """Raised when the target conversation cannot be found."""


class InvalidConversationTransitionError(MessageProcessingError):
    """Raised when a conversation state transition is not allowed."""


class ConversationStateTransitionError(MessageProcessingError):
    """Raised when a conversation state transition is not allowed."""
