class NotFoundError(Exception):
    """Raised when an entity cannot be found."""


class ConflictError(Exception):
    """Raised when data would violate a uniqueness rule."""


class UnauthorizedError(Exception):
    """Raised when login credentials are invalid."""
