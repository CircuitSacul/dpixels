from dpixels.color import Color
import os
import logging
import asyncio

from dotenv import load_dotenv

from dpixels import Client, AutoDraw
from PIL import Image

logging.basicConfig(level=logging.DEBUG)

load_dotenv()

client = Client(token=os.getenv("TOKEN"))


async def main():
    im = Image.open("starboard.png")
    im = im.resize((10, 10))
    ad = AutoDraw.from_image(client, (100, 0), im, bg_color=Color(0, 0, 0))
    await ad.draw_and_fix()


async def go():
    try:
        await main()
    except KeyboardInterrupt:
        pass
    finally:
        await client.close()


try:
    asyncio.run(go())
except KeyboardInterrupt:
    pass
