from typing import TYPE_CHECKING, Tuple, Optional


if TYPE_CHECKING:
    from dpixels.client import Client
    from dpixels.color import Color


class ABCSource:
    async def needs_update(self) -> bool:
        raise NotImplementedError

    async def update(self, client: "Client"):
        raise NotImplementedError

    async def next(self) -> Optional[Tuple[int, int, Color]]:
        raise NotImplementedError
