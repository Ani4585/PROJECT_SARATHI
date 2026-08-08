from dataclasses import dataclass

@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_after: float
    retry_after: float

class RateLimitExceededException(Exception):
    def __init__(self, message: str, result: RateLimitResult):
        super().__init__(message)
        self.result = result
