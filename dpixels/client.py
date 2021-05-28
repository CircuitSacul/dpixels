import asyncio
import logging
from typing import Any, Dict, Optional, Tuple, Union

import aiohttp

from .ratelimits import Ratelimits
from .exceptions import Cooldown, HttpException, Ratelimit
from .canvas import Canvas
from .color import Color

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
        self,
        x: int,
        y: int,
        color: "Color",
        *,
        retry: bool = False
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
            retry_on_ratelimit=retry
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
            retry_on_ratelimit=retry
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
                }
            },
            retry_on_ratelimit=retry
        )
        return data["message"]

    async def get_session(self):
        if (not self.session) or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session

    async def request(
        self,
        method: str,
        endpoint: str,
        *,
        data: Optional[Dict[Any, Any]] = None,
        params: Optional[Dict[Any, Any]] = None,
        parse_json: bool = True,
        retry_on_ratelimit: bool = True,
    ) -> Union[Dict[Any, Any], str]:
        session = await self.get_session()

        ratelimit = self.ratelimits.ratelimits[endpoint]
        if not ratelimit.valid:
            logger.warning("Ratelimit is invalid.")
            retry_after = None
        else:
            retry_after = ratelimit.retry_after
        if retry_after:
            if not retry_on_ratelimit:
                raise Ratelimit(endpoint, retry_after, ratelimit)
            await ratelimit.pause()
            return await self.request(
                method, endpoint,
                data=data,
                params=params,
                parse_json=parse_json,
                retry_on_ratelimit=False
            )

        async with session.request(
            method,
            self.e_base_url + endpoint,
            json=data,
            params=params,
        ) as resp:
            ratelimit.update(resp.headers)
            if resp.status == 429:
                raise Cooldown(endpoint, ratelimit.retry_after, ratelimit)
            if 500 > resp.status > 400:
                data = await resp.json()
                raise HttpException(resp.status, data["detail"])

            if parse_json:
                return await resp.json()
            else:
                return await resp.read()

    async def close(self):
        await self.session.close()
        self.ratelimits.save()