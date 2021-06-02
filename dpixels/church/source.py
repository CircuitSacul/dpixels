from typing import Optional, TYPE_CHECKING, Tuple

from dpixels.abc.source import ABCSource

if TYPE_CHECKING:
    from dpixels.color import Color
    from dpixels.client import Client


class ChurchTask:
    def __init__(
        self,
        uid: int,
        xy: Tuple[int, int],
        color: Color,
    ):
        self.uid = uid
        self.x, self.y = xy
        self.color = color

    @property
    def xy(self):
        return (self.x, self.y)


class ChurchSource(ABCSource):
    def __init__(
        self,
        url: str,
        *,
        get_task: str = "task",
        complete_task: str = "complete",
    ):
        self.url = url
        self.e_get_task = get_task
        self.e_complete_task = complete_task

        self.current_task: Optional[ChurchTask] = None

    async def complete_task(self, client: "Client", task: ChurchTask):
        session = await client.get_session()
        async with session.request(
            "POST",
            self.url + self.e_complete_task,
            json={"task": task.uid},
        ) as resp:
            resp.raise_for_status()

    async def get_task(self, client: "Client") -> Optional[ChurchTask]:
        session = await client.get_session()
        async with session.request(
            "GET",
            self.url + self.e_get_task
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()

        data = data["task"]
        if data is None:
            return None

        return ChurchTask(
            int(data["uid"]),
            int(data["x"]),
            int(data["y"]),
            Color.from_hex(data["color"]),
        )

    async def needs_update(self) -> bool:
        return self.current_task is not None

    async def update(self, client: "Client"):
        self.current_task = await self.get_task(client)

    async def next(self) -> Optional[Tuple[int, int, Color]]:
        if self.current_task is None:
            return None
        t = self.current_task
        return (t.x, t.y, t.color)
