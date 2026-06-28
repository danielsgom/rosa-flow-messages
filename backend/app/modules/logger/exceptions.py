class RosaFlowError(Exception):
    """Base exception for Rosa Flow Messages."""
    pass


class TelegramConnectionError(RosaFlowError):
    """Raised when Telegram MTProto connection fails."""
    pass


class OpenAIError(RosaFlowError):
    """Raised when OpenAI API call fails."""
    pass


class ContextLoadError(RosaFlowError):
    """Raised when system prompt fails to load."""
    pass


class PromptValidationError(RosaFlowError):
    """Raised when system prompt validation fails."""
    pass


class TriggerDelayError(RosaFlowError):
    """Raised when trigger delay calculation fails."""
    pass
