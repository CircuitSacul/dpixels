# dpixels
A(nother) wrapper for the Python Discord Pixel API.

## Features
 - Proper ratelimite handeling.
 - Saves ratelimits in a json file, so restarting scripts won't trigger cooldowns.
 - Supports all Pixel API endpoints.
 - Supports autodrawing of images.

## Examples

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

im = Image.open("path_to_image.ext")

source = dpixels.Source.from_image((0, 0), im)
await client.draw_sources([source])  # draw the source
```

## Credits
This library is heavily based on [Artemis21/dpypx](https://github.com/Artemis21/dpypx)
