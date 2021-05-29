from typing import Any


class Color:
    def __init__(self, r: int, g: int, b: int, a: int = 1):
        self.r, self.g, self.b, self.a = r, g, b, a

    def add_color_with_alpha(self, color: "Color"):
        a = color.a
        return [
            int(a * c1 + (1 - a) * c2) for (c1, c2) in zip(color.rgb, self.rgb)
        ]

    @property
    def int(self):
        """Get the color as a 3 byte int."""
        return self.r << 16 | self.g << 8 | self.b

    @property
    def hex(self):
        """Get the color has a hex string."""
        return f"{self.r:0>2x}{self.g:0>2x}{self.b:0>2x}"

    @property
    def rgba(self):
        return self.r, self.g, self.b, self.a

    @property
    def rgb(self):
        return self.r, self.g, self.b

    def __eq__(self, val: Any) -> bool:
        if isinstance(val, Color):
            return val.rgb == self.rgb
        return False

    @classmethod
    def from_hex(cls, hex_value: str) -> "Color":
        hex_value = hex_value.lstrip("#")
        return cls(*(int(hex_value[i : i + 2], 16) for i in range(0, 6, 2)))
