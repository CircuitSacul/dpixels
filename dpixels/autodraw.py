import asyncio
from typing import TYPE_CHECKING, List, Optional, Tuple

from PIL import Image

from .exceptions import Cooldown, Ratelimit
from .color import Color

if TYPE_CHECKING:
    from .client import Client


def map_255_to_1(value: int):
    max1, min1 = (255, 0)
    max2, min2 = (1, 0)

    # Figure out how 'wide' each range is
    span1 = max1 - min1
    span2 = max2 - min2

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - min1) / float(span1)

    # Convert the 0-1 range into a value in the right range.
    return min2 + (valueScaled * span2)


class AutoDraw:
    def __init__(
        self,
        client: "Client",
        x: int,
        y: int,
        pixels: List[Tuple[int, int, Color]],
    ):
        self.client = client
        self.x = x
        self.y = y
        self.pixels = []
        for x, y, p in pixels:
            if p.a == 0:
                continue
            p.a = 1
            self.pixels.append((x, y, p))

    async def do_pixel(self, x: int, y: int, p: Color):
        try:
            await self.client.set_pixel(x, y, p)
        except (Ratelimit, Cooldown) as r:
            await r.ratelimit.pause()
            return await self.do_pixel(x, y, p)

    async def draw(self):
        canvas = await self.client.get_canvas()
        for _x, _y, pix in self.pixels:
            x = _x + self.x
            y = _y + self.y
            if canvas[x, y] != pix:
                await self.do_pixel(x, y, pix)

    async def draw_and_fix(
        self,
        forever: bool = True,
        guard_delay: int = 3,
    ):
        done: bool = False
        while not done:
            canvas = await self.client.get_canvas()
            for _x, _y, pix in self.pixels:
                x = _x + self.x
                y = _y + self.y
                if canvas[x, y] != pix:
                    await self.do_pixel(x, y, pix)
                    continue
            if not forever:
                return
            await asyncio.sleep(guard_delay)

    @classmethod
    def from_image(
        cls,
        client: "Client",
        xy: Tuple[int, int],
        image: Image.Image,
        scale: int = 1,
        bg_color: Optional[Color] = None,
    ) -> "AutoDraw":
        if image.mode not in ["RGB", "RGBA"]:
            raise RuntimeError("Images must be either RGB or RGBA.")

        width = round(image.width * scale)
        height = round(image.width * scale)
        if scale != 1:
            image = image.resize((width, height))

        data = list(image.getdata())
        pixels: List[Tuple[int, int, Color]] = []

        for y, start in enumerate(range(0, len(data), width)):
            for x, p in enumerate(data[start : start + width]):
                c = Color(*p)
                if image.mode == "RGBA":
                    p = list(p)
                    p[-1] = map_255_to_1(p[-1])
                    if bg_color:
                        c = Color(*bg_color.add_color_with_alpha(c))
                pixels.append((x, y, c))

        return cls(client, *xy, pixels)

    @classmethod
    def from_array(
        cls,
        client: "Client",
        xy: Tuple[int, int],
        array: List[List[Color]],
    ):
        lst: List[Tuple[int, int, Color]] = []
        for y, col in enumerate(array):
            for x, pix in enumerate(col):
                lst.append((x, y, pix))
        return cls(client, *xy, lst)
