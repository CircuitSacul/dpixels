from typing import List, Tuple

from .color import Color


class Canvas:
    def __init__(self, w: int, h: int, data: bytes):
        self.width = w
        self.height = h
        self.raw = data

        assert len(data) == w * h * 3, "Got an unexpcted data length."

        pixels = []
        for start_idx in range(0, len(data), 3):
            pixels.append(Color(*data[start_idx : start_idx + 3]))
        self.grid: List[List[Color]] = [
            pixels[row * self.width : (row + 1) * self.width]
            for row in range(self.height)
        ]

    def __getitem__(self, xy: Tuple[int, int]):
        x, y = xy
        return self.grid[y][x]
