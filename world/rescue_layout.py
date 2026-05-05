from __future__ import annotations

import os
from world.game import Grid


class RescueLayout:
    """
    Manages the static geometry of the rescue area.

    Symbols in .lay files:
        %  – Wall / Obstacle (impassable)
        R  – Robot SAR starting position
        S  – Survivor / Patient to rescue
        M  – Medical Post (destination for rescue operations)
        T  – Medical Supplies (must be delivered to M before rescue)
        .  – Free floor cell
        (space) – Free floor cell
    """

    def __init__(self, layout_text: list[str]) -> None:
        self.width         = len(layout_text[0])
        self.height        = len(layout_text)
        self.walls         = Grid(self.width, self.height, False)
        self.robot_position: tuple[int, int] | None = None
        self.patients:       list[tuple[int, int]] = []
        self.supplies:       list[tuple[int, int]] = []
        self.medical_posts:  list[tuple[int, int]] = []
        self.layout_text   = layout_text
        self._process(layout_text)

    def _process(self, layout_text: list[str]) -> None:
        max_y = self.height - 1
        for y in range(self.height):
            for x in range(self.width):
                char = layout_text[max_y - y][x]
                self._process_char(x, y, char)

    def _process_char(self, x: int, y: int, char: str) -> None:
        if char == "%":
            self.walls[x][y] = True
        elif char == "R":
            self.robot_position = (x, y)
        elif char == "S":
            self.patients.append((x, y))
        elif char == "T":
            self.supplies.append((x, y))
        elif char == "M":
            self.medical_posts.append((x, y))

    def get_all_cells(self) -> list[tuple[int, int]]:
        """Return all non-wall cell positions."""
        cells: list[tuple[int, int]] = []
        for x in range(self.width):
            for y in range(self.height):
                if not self.walls[x][y]:
                    cells.append((x, y))
        return cells

    def get_adjacent_pairs(self) -> list[tuple[tuple[int, int], tuple[int, int]]]:
        """Return all pairs of adjacent (non-wall) cells."""
        pairs = []
        for x in range(self.width):
            for y in range(self.height):
                if self.walls[x][y]:
                    continue
                for dx, dy in [(1, 0), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if not self.walls[nx][ny]:
                            pairs.append(((x, y), (nx, ny)))
        return pairs

    def __str__(self) -> str:
        return "\n".join(self.layout_text)


def get_layout(name: str) -> RescueLayout | None:
    """Load a layout file by name, searching recursively inside layouts/."""
    filename = name if name.endswith(".lay") else name + ".lay"
    for root, _dirs, files in os.walk("layouts"):
        if filename in files:
            return _try_load(os.path.join(root, filename))
    return None


def _try_load(fullname: str) -> RescueLayout | None:
    if not os.path.exists(fullname):
        return None
    with open(fullname) as f:
        return RescueLayout([line.rstrip("\n") for line in f])
