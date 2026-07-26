from .base import SarathiException


class DatabaseError(SarathiException):
    """
    Database operation failures.
    """

    def __init__(
        self,
        message,
        details=None
    ):

        super().__init__(
            message,
            error_code="DATABASE_ERROR",
            details=details,
        )
        