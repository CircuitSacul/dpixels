# dpixels
A(nother) wrapper for the Python Discord Pixel API.

## Features
 - Proper ratelimite handeling.
 - Saves ratelimits in a json file, so restarting scripts won't trigger cooldowns.
 - Supports all Pixel API endpoints.
 - Supports autodrawing of images.

## Examples

### Note:
In order for the ratelimit to work cross-restart, you MUST do it like this:
```py
async def run():
    try:
        # code ehre
    finally:
        await client.close()
        
asyncio.run(run())
```

Get the canvas:
```py
client = dpixels.Client(token="your token")
canvas = await client.get_canvas()

# this also caches the canvas, so later you can do:
canvas = client.canvas
```

Get a specific pixel:
```py
pixel = canvas[0, 0]  # get the pixel at 0,0
pixel = await client.get_pixel(0, 0)  # fetch the pixel at 0, 0

pixel.hex  # the hex value
pixel.int  # the int value
pixel.rgb  # the rgb value
```

Setting a pixel:
```py
await client.set_pixel(0, 0, dpixels.Color(255, 255, 255))  # set the pixel at 0,0 to white
```

Autodrawing an image:
```py
from PIL import Image

im = Image.load("path_to_image.png")

ad = dpixels.AutoDraw.from_image(client, (0, 0), im)
await ad.draw()  # draw the image
await ad.draw_and_fix()  # or, draw and prioritize fixing existing pixels
```
