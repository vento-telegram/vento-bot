class OpenAIBadRequestError(Exception):
    pass


class InsufficientBalanceError(Exception):
    """Raised when a user has not enough tokens to perform an action."""
    pass