from .base import SarathiException


class ServiceError(SarathiException):
    """
    Business/service layer failures.
    """

    def __init__(
        self,
        message,
        details=None
    ):

        super().__init__(
            message,
            error_code="SERVICE_ERROR",
            details=details,
        )