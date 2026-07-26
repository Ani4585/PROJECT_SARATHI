"""
PROJECT SARATHI
Base Exception Framework

Central parent class for all application exceptions.
"""


class SarathiException(Exception):
    """
    Base exception for PROJECT SARATHI.

    All custom exceptions should inherit from this.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "SARATHI_ERROR",
        details: dict | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}

        super().__init__(self.message)


    def to_dict(self):
        """
        Convert exception into structured format.
        Useful for APIs and monitoring systems.
        """

        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


    def __str__(self):

        return (
            f"[{self.error_code}] "
            f"{self.message}"
        )