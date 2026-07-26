from .base import SarathiException


class ConfigurationError(SarathiException):
    """
    Raised when application configuration fails.
    """

    def __init__(
        self,
        message,
        details=None
    ):

        super().__init__(
            message,
            error_code="CONFIG_ERROR",
            details=details,
        )