class Grid:
    """
    A 2D array of boolean values. Supports indexing as grid[x][y].
    The convention is (0,0) at the bottom-left corner.
    """

    def __init__(self, width, height, initial_value=False):
        if initial_value not in [False, True]:
            raise Exception("Grids can only contain booleans.")
        self.CELLS_PER_INT = 30
        self.width = width
        self.height = height
        self._cells = []
        for _ in range(self.width):
            column = [initial_value] * self.height
            self._cells.append(column)

    def __getitem__(self, i):
        return self._cells[i]

    def __setitem__(self, key, item):
        self._cells[key] = item

    def __str__(self):
        out = [[str(self._cells[x][y])[0] for x in range(self.width)] for y in range(self.height)]
        out.reverse()
        return "\n".join(["".join(row) for row in out])

    def __eq__(self, other):
        if other is None:
            return False
        return self._cells == other._cells

    def __hash__(self):
        base = 1
        h = 0
        for row in self._cells:
            for val in row:
                if val:
                    h += base
                base *= 2
        return hash(h)

    def copy(self):
        g = Grid(self.width, self.height)
        g._cells = [col[:] for col in self._cells]
        return g

    def deepCopy(self):
        return self.copy()

    def asList(self, key=True):
        lst = []
        for x in range(self.width):
            for y in range(self.height):
                if self._cells[x][y] == key:
                    lst.append((x, y))
        return lst

    def count(self, item=True):
        return sum(self._cells[x][y] == item for x in range(self.width) for y in range(self.height))
