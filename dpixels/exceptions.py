from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ratelimits import RateLimitedEndpoint

__all__ = [
    "DPixelsError",
    "Cooldown",
    "Ratelimit",
    "HttpException",
]


class DPixelsError(Exception):
    pass


class Cooldown(DPixelsError):
    def __init__(
        self, endpoint: str, time: int, ratelimit: "RateLimitedEndpoint"
    ):
        self.ratelimit = ratelimit
        super().__init__(
            f"The endpoint {endpoint} has hit a ratelimit. "
            f"Cooldown resets in {time}s."
        )


class Ratelimit(DPixelsError):
    def __init__(
        self,
        endpoint: str,
        retry_after: int,
        ratelimit: "RateLimitedEndpoint",
    ):
        self.ratelimit = ratelimit
        super().__init__(
            f"Endpoint {endpoint} has reached its ratelimit. "
            f"Retry again in {retry_after}s."
        )


class HttpException(DPixelsError):
    def __init__(self, status: int, detail: str):
        self.status = status
        super().__init__(f"HTTP Error {status}: {detail}")
