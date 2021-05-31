import asyncio
import datetime
import logging
from asyncio import Lock
from collections import defaultdict
from typing import Any, Dict, Optional

logger = logging.getLogger("dpixels")


class RateLimitedEndpoint:
    """A representation of an endpoint that has a ratelimit."""

    def __init__(self):
        self.valid = False
        self.ratelimited = True

        self.remaining = 0
        self.limit = None

        self.reset: datetime.datetime = None
        self.cooldown_reset: datetime.datetime = None

        self.lock = Lock()

    def update(self, headers: Dict[str, Any]):
        """Update the ratelimiter based on the latest headers."""
        self.valid = True
        if "Cooldown-Reset" in headers:
            self.remaining = 0
            cooldown_reset = float(headers["Cooldown-Reset"])
            self.cooldown_reset = (
                datetime.timedelta(seconds=cooldown_reset)
                + datetime.datetime.now()
            )
            return
        if "Requests-Remaining" not in headers:
            self.ratelimited = False
            return
        self.remaining = int(headers["Requests-Remaining"])
        self.limit = int(headers["Requests-Limit"])
        reset = float(headers.get("Requests-Reset", self.reset))
        self.reset = (
            datetime.timedelta(seconds=reset) + datetime.datetime.now()
        )

    @property
    def retry_after(self) -> Optional[int]:
        now = datetime.datetime.now()
        total = 0
        if self.cooldown_reset and now < self.cooldown_reset:
            total += (self.cooldown_reset - now).total_seconds()
        if not self.ratelimited or self.remaining:
            return total
        if self.reset and now < self.reset:
            total += (self.reset - now).total_seconds()
        return total

    @retry_after.setter
    def retry_after(self, _):
        self.cooldown_reset = self.reset = None

    async def pause(self):
        total = self.retry_after
        logger.debug(f"Sleeping for {total}s")
        await asyncio.sleep(total)
        self.retry_after = 0


class Ratelimits:
    def __init__(self, save_file: str):
        self.save_file = save_file
        self.ratelimits = defaultdict(RateLimitedEndpoint)
