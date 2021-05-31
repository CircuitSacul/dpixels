from typing import Callable, TYPE_CHECKING, List, Optional, Tuple

from PIL import Image

from .color import Color

if TYPE_CHECKING:
    from .canvas import Canvas

MAX1, MIN1 = (255, 0)
MAX2, MIN2 = (1, 0)


def map_255_to_1(value: int):
    return MIN2 + (((value - MIN1) / (MAX1 - MIN1)) * (MAX2 - MIN2))


class Source:
    def __init__(
        self,
        x: int,
        y: int,
        pixels: List[Tuple[int, int, Color]],
        fix: bool,
    ):
        self.x = x
        self.y = y
        self.fix = fix
        self.pixels = []
        for x, y, p in pixels:
            if p.a == 0:
                continue
            p.a = 1
            self.pixels.append((x, y, p))

        self.pixel_queue: List[Tuple[int, int, Color]] = self.pixels.copy()
        self.fix_queue: List[Tuple[int, int, Color]] = []

    @property
    def needs_update(self) -> bool:
        return (self.fix and self.fix_queue) or self.pixel_queue

    def get_next_pixel(self) -> Optional[Tuple[int,  int, "Color"]]:
        if self.fix and self.fix_queue:
            return self.fix_queue.pop(0)
        if self.pixel_queue:
            return self.pixel_queue.pop(0)
        return None

    def update_fix_queue(self, canvas: "Canvas"):
        if not self.fix:
            return
        for x, y, p in self.pixels:
            v = (x, y, p)
            if v in self.pixel_queue:
                continue
            if v in self.fix_queue:
                continue
            if canvas[x, y] != p:
                self.fix_queue.append((x, y, p))

    @classmethod
    def from_image(
        cls,
        xy: Tuple[int, int],
        image: Image.Image,
        *,
        skip_pixel_if: Callable[[Tuple[int, int], Color, Color], bool] = None,
        fix: bool = True,
        scale: int = 1,
        bg_color: Optional[Color] = None,
    ) -> "Source":
        if image.mode not in ["RGB", "RGBA"]:
            raise RuntimeError("Images must be either RGB or RGBA.")

        width = round(image.width * scale)
        height = round(image.width * scale)
        if scale != 1:
            image = image.resize((width, height))

        data = list(image.getdata())
        pixels: List[Tuple[int, int, Color]] = []

        for _y, start in enumerate(range(0, len(data), width)):
            y = _y + xy[1]
            for _x, p in enumerate(data[start : start + width]):
                x = _x + xy[0]
                if image.mode == "RGBA":
                    p = list(p)
                    p[-1] = map_255_to_1(p[-1])
                    orig = c = Color(*p)
                    if bg_color:
                        after = c = Color(*bg_color.add_color_with_alpha(c))
                    else:
                        after = orig
                else:
                    after = orig = c = Color(*p)

                if skip_pixel_if:
                    if skip_pixel_if((x, y), orig, after):
                        continue

                pixels.append((x, y, c))

        return cls(*xy, pixels, fix=fix)

    @classmethod
    def from_array(
        cls,
        xy: Tuple[int, int],
        array: List[List[Color]],
        *,
        fix: bool = True,
    ) -> "Source":
        lst: List[Tuple[int, int, Color]] = []
        for _y, col in enumerate(array):
            y = xy[1] + _y
            for _x, pix in enumerate(col):
                x = xy[0] + _x
                lst.append((x, y, pix))
        return cls(*xy, lst, fix=fix)
