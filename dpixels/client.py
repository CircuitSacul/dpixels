import asyncio
import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple, Union

import aiohttp

from .canvas import Canvas
from .color import Color
from .exceptions import Cooldown, HttpException, Ratelimit
from .ratelimits import Ratelimits

if TYPE_CHECKING:
    from .source import Source

logger = logging.getLogger("dpixels")


class Client:
    e_base_url = "https://pixels.pythondiscord.com/"

    e_get_size = "get_size"
    e_get_canvas = "get_pixels"
    e_get_pixel = "get_pixel"

    e_swap_pixel = "swap_pixel"
    e_set_pixel = "set_pixel"

    def __init__(
        self,
        token: str,
        save_file: str = "ratelimits.json",
        *,
        user_agent: str = "Ciruit dpixels (Python/aiohttp)",
    ):
        self.headers = {
            "Authorization": "Bearer " + token.strip(),
            "User-Agent": user_agent,
        }
        self.session: Optional[aiohttp.ClientSession] = None

        self.ratelimits = Ratelimits(save_file)
        self.canvas: Optional[Canvas] = None

    async def draw_sources_blind(
        self,
        sources: List["Source"],
        loop: bool = True,
    ):
        going = True
        while going:
            for s in sources:
                for x, y, p in s.pixels:
                    await self.set_pixel(x, y, p, retry=True)
            going = loop

    async def draw_sources(
        self, sources: List["Source"], forever: bool = True
    ):
        async def do_draw(s: "Source"):
            while True:
                val = s.get_next_pixel()
                if not val:
                    return
                x, y, p = val
                if self.canvas[x, y] == p:
                    continue
                try:
                    await self.set_pixel(x, y, p)
                except (Cooldown, Ratelimit) as e:
                    await e.ratelimit.pause()
                finally:
                    return

        def any_needs_update() -> bool:
            for s in sources:
                s.update_fix_queue(self.canvas)
                if s.needs_update:
                    return True
            return False

        going = True
        while going:
            await self.get_canvas()

            any_needs = any_needs_update()
            going = forever or any_needs

            for s in sources:
                if not s.needs_update:
                    continue
                await do_draw(s)
                break
            else:
                logger.info("All sources correct, sleeping 5s.")
                await asyncio.sleep(5)

    async def get_canvas_size(self):
        data = await self.request("GET", self.e_get_size)
        return int(data["width"]), int(data["height"])

    async def get_canvas(self):
        size = asyncio.create_task(self.get_canvas_size())
        data = await self.request("GET", self.e_get_canvas, parse_json=False)
        size = await size
        self.canvas = Canvas(size[0], size[1], data)
        return self.canvas

    async def set_pixel(
        self, x: int, y: int, color: "Color", *, retry: bool = False
    ):
        if self.canvas:
            current = self.canvas[x, y]
            rgb = current.add_color_with_alpha(color)
            current.r, current.g, current.b = rgb
            ashex = current.hex
        else:
            ashex = color.hex

        data = await self.request(
            "POST",
            self.e_set_pixel,
            data={
                "x": x,
                "y": y,
                "rgb": ashex,
            },
            retry_on_ratelimit=retry,
        )
        logger.debug(data["message"])
        return data["message"]

    async def get_pixel(
        self, x: int, y: int, *, retry: bool = True
    ) -> "Color":
        data = await self.request(
            "GET",
            self.e_get_pixel,
            params={
                "x": x,
                "y": y,
            },
            retry_on_ratelimit=retry,
        )
        c = Color.from_hex(data["rgb"])
        if self.canvas:
            self.canvas.grid[y][x] = c
        return c

    async def swap_pixels(
        self,
        xy0: Tuple[int, int],
        xy1: Tuple[int, int],
        *,
        retry: bool = False,
    ):
        data = await self.request(
            "POST",
            self.e_swap_pixel,
            data={
                "origin": {
                    "x": xy0[0],
                    "y": xy0[1],
                },
                "dest": {
                    "x": xy1[0],
                    "y": xy1[1],
                },
            },
            retry_on_ratelimit=retry,
        )
        return data["message"]

    async def get_session(self):
        if (not self.session) or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session

    async def request(
        self,
        *args,
        retry_on_ratelimit: bool = True,
        **kwargs,
    ):
        try:
            return await self.do_request(*args, **kwargs)
        except (Cooldown, Ratelimit) as e:
            if retry_on_ratelimit:
                await e.ratelimit.pause()
                return await self.request(
                    *args, **kwargs, retry_on_ratelimit=True
                )
            raise

    async def do_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[Any, Any]] = None,
        params: Optional[Dict[Any, Any]] = None,
        parse_json: bool = True,
    ) -> Union[Dict[Any, Any], str]:
        session = await self.get_session()
        ratelimit = self.ratelimits.ratelimits[endpoint]

        async with ratelimit.lock:
            if ratelimit.ratelimited:
                try:
                    _, headers, _ = await self.raw_request(
                        session,
                        "HEAD",
                        self.e_base_url + endpoint,
                        parse_json=False,
                    )
                    ratelimit.update(headers)
                except HttpException as e:
                    if e.status == 405:
                        ratelimit.ratelimited = False
                    else:
                        raise

            if ratelimit.retry_after:
                raise Ratelimit(
                    endpoint,
                    ratelimit.retry_after,
                    ratelimit,
                )

            result, headers, status = await self.raw_request(
                session,
                method,
                self.e_base_url + endpoint,
                data=data,
                params=params,
                parse_json=parse_json
            )

            if status == 429:
                ratelimit.update(headers)
                raise Cooldown(
                    endpoint,
                    ratelimit.retry_after,
                    ratelimit,
                )

            return result

    async def raw_request(
        self,
        session: aiohttp.ClientSession,
        method: str,
        url: str,
        data: Optional[Dict[Any, Any]] = None,
        params: Optional[Dict[Any, Any]] = None,
        parse_json: bool = True,
    ) -> Tuple[Union[Dict[Any, Any], str], Dict[Any, Any], int]:
        async with session.request(
            method,
            url,
            json=data,
            params=params
        ) as resp:
            if 500 > resp.status > 400:
                data = await resp.json()
                data = data.get("detail", None) if data else "None"
                raise HttpException(resp.status, data)
            if parse_json:
                data = await resp.json()
            else:
                data = await resp.read()
            return data, resp.headers, resp.status

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
