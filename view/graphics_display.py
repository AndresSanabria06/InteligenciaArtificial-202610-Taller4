import time
from view.graphics_utils import (
    Canvas, WALL_COLOR, FLOOR_COLOR, ROBOT_COLOR, PATIENT_COLOR,
    SUPPLIES_COLOR, MEDICAL_COLOR, RESCUED_COLOR, HOLDING_COLOR,
)

CELL_SIZE = 52  # base pixels per cell (slightly larger for clarity)
LABEL_STRIP = 28  # pixels for the action label strip at the bottom


class GraphicsDisplay:
    """
    Tkinter-based graphical display for the planning simulation.

    Visual language:
      - Walls      → dark slate filled rectangles
      - Floor      → warm ivory with subtle grid border
      - Robot (R)  → large cobalt-blue circle, white "R"
                     golden ring when holding an object
      - Supplies   → amber diamond (rotated square), white "T"
      - Patient    → crimson upward triangle, white "S"
                     turns emerald with "✓" after rescue
      - Med. Post  → forest-green square with white cross (+), label "M"
      - Base       → purple square with roof outline, label "B"
      - SuppliesReady → small golden dot on top-right corner of med. post
    """

    def __init__(self, layout, zoom=1.0, frame_time=0.1):
        self.layout = layout
        self.zoom = zoom
        self.frame_time = frame_time
        self.cell = int(CELL_SIZE * zoom)

        canvas_w = layout.width * self.cell
        canvas_h = layout.height * self.cell + LABEL_STRIP
        self.canvas = Canvas(canvas_w, canvas_h, zoom)

        self._items = {}       # tag -> list of canvas ids for a given entity
        self._action_label = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def initialize(self, layout, state):
        self._draw_base(layout)
        self._update_dynamic(state, action=None)
        self.canvas.update()

    def update(self, state, action=None):
        self._update_dynamic(state, action)
        self.canvas.update()
        self.canvas.sleep(self.frame_time)

    def finish(self):
        self.canvas.update()
        time.sleep(0.5)
        self.canvas.destroy()

    def pause(self):
        self.canvas.sleep(self.frame_time)

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------

    def _cell_to_screen(self, x, y):
        """Grid (x, y) → canvas top-left pixel of that cell."""
        px = x * self.cell
        py = (self.layout.height - 1 - y) * self.cell
        return px, py

    def _cell_center(self, x, y):
        px, py = self._cell_to_screen(x, y)
        return px + self.cell // 2, py + self.cell // 2

    # ------------------------------------------------------------------
    # Static map drawing
    # ------------------------------------------------------------------

    def _draw_base(self, layout):
        c = self.cell
        pad = 2
        arm = max(3, c // 6)   # cross arm half-width
        thick = max(2, c // 9)  # cross bar thickness

        # Floor and walls
        for x in range(layout.width):
            for y in range(layout.height):
                px, py = self._cell_to_screen(x, y)
                if layout.walls[x][y]:
                    self.canvas.draw_rect(px, py, c, c, WALL_COLOR, outline=WALL_COLOR)
                else:
                    self.canvas.draw_rect(px, py, c, c, FLOOR_COLOR,
                                          outline="#D5D0C5", width=1)

        # Medical posts: green square + white cross + "M" label
        for pos in layout.medical_posts:
            px, py = self._cell_to_screen(*pos)
            cx, cy = px + c // 2, py + c // 2
            self.canvas.draw_rect(px + pad, py + pad,
                                  c - 2 * pad, c - 2 * pad,
                                  MEDICAL_COLOR, outline="#145A32", width=2)
            # Horizontal bar of the cross
            self.canvas.draw_rect(cx - arm, cy - thick // 2,
                                  2 * arm, thick, "white", outline="white")
            # Vertical bar of the cross
            self.canvas.draw_rect(cx - thick // 2, cy - arm,
                                  thick, 2 * arm, "white", outline="white")
            # "M" label at the bottom of the cell
            self.canvas.draw_text(cx, py + c - max(8, c // 7),
                                  "M", color="#ABEBC6",
                                  size=max(7, c // 7), bold=True)

        # Bottom action-label strip
        strip_y = layout.height * c
        self.canvas.draw_rect(0, strip_y, layout.width * c, LABEL_STRIP,
                               "#1A252F", outline="#1A252F")

    # ------------------------------------------------------------------
    # Dynamic entity drawing
    # ------------------------------------------------------------------

    def _clear_items(self):
        for ids in self._items.values():
            for item_id in ids:
                self.canvas.delete(item_id)
        self._items = {}
        if self._action_label is not None:
            self.canvas.delete(self._action_label)
            self._action_label = None

    def _add(self, tag, *item_ids):
        self._items.setdefault(tag, []).extend(item_ids)

    def _update_dynamic(self, state, action=None):
        self._clear_items()
        c = self.cell
        pad = 3

        holding = {f[2] for f in state if f[0] == "Holding"}
        rescued = {f[1] for f in state if f[0] == "Rescued"}

        # ---- Robot -------------------------------------------------------
        for fluent in state:
            if fluent[0] == "At" and fluent[1] == "robot":
                pos = fluent[2]
                px, py = self._cell_to_screen(*pos)
                cx, cy = px + c // 2, py + c // 2
                r_outer = c // 2 - pad + 3
                r_inner = c // 2 - pad

                # Golden outer ring when holding something
                ring_color = HOLDING_COLOR if holding else ROBOT_COLOR
                ring = self.canvas.draw_oval(cx, cy, r_outer, ring_color,
                                             outline="#1A5276", width=3)
                body = self.canvas.draw_oval(cx, cy, r_inner, ROBOT_COLOR,
                                             outline="white", width=2)
                lbl = self.canvas.draw_text(cx, cy, "R",
                                            color="white", size=max(9, c // 5), bold=True)
                self._add(("robot", pos), ring, body, lbl)

                # Small indicator dot showing what is held
                if holding:
                    obj_name = next(iter(holding))
                    dot_color = SUPPLIES_COLOR if "supplies" in obj_name else PATIENT_COLOR
                    ind_r = max(4, c // 8)
                    ind = self.canvas.draw_oval(
                        px + c - pad - ind_r, py + pad + ind_r, ind_r,
                        dot_color, outline="white", width=1,
                    )
                    self._add(("robot_hold", pos), ind)

        # ---- Supplies — amber diamond ------------------------------------
        for fluent in state:
            if fluent[0] == "At" and str(fluent[1]).startswith("supplies"):
                obj, pos = fluent[1], fluent[2]
                px, py = self._cell_to_screen(*pos)
                # Diamond centered in lower-left quadrant of the cell
                cx = px + c // 4
                cy = py + 3 * c // 4
                hw = c // 4 - pad - 1
                diamond = [cx, cy - hw, cx + hw, cy, cx, cy + hw, cx - hw, cy]
                shape = self.canvas.draw_polygon(
                    diamond, fill=SUPPLIES_COLOR, outline="#784212", width=2,
                )
                lbl = self.canvas.draw_text(cx, cy, "T",
                                            color="white", size=max(7, c // 6), bold=True)
                self._add((obj, pos), shape, lbl)

        # ---- Patients — upward triangle ----------------------------------
        for fluent in state:
            if fluent[0] == "At" and str(fluent[1]).startswith("patient"):
                obj, pos = fluent[1], fluent[2]
                color = RESCUED_COLOR if obj in rescued else PATIENT_COLOR
                outline = "#1E8449" if obj in rescued else "#7B241C"
                label = "✓" if obj in rescued else "S"  # ✓ or S

                px, py = self._cell_to_screen(*pos)
                # Triangle in upper-right quadrant
                cx = px + 3 * c // 4
                cy = py + c // 4
                r = c // 4 - pad
                tri = [cx, cy - r, cx - r, cy + r, cx + r, cy + r]
                shape = self.canvas.draw_polygon(
                    tri, fill=color, outline=outline, width=2,
                )
                lbl = self.canvas.draw_text(cx, cy + r // 4, label,
                                            color="white", size=max(6, c // 7), bold=True)
                self._add((obj, pos), shape, lbl)

        # ---- SuppliesReady dot on medical post ---------------------------
        for fluent in state:
            if fluent[0] == "SuppliesReady":
                pos = fluent[1]
                px, py = self._cell_to_screen(*pos)
                dot_r = max(4, c // 9)
                dot = self.canvas.draw_oval(
                    px + c - pad - dot_r, py + pad + dot_r, dot_r,
                    HOLDING_COLOR, outline="#9A6900", width=1,
                )
                self._add(("supplies_ready", pos), dot)

        # ---- Action label in bottom strip --------------------------------
        if action is not None:
            name = action.name
            max_chars = max(30, self.layout.width * self.cell // 8)
            if len(name) > max_chars:
                name = name[:max_chars - 1] + "…"  # ellipsis
            strip_y = self.layout.height * c
            self._action_label = self.canvas.draw_text(
                self.layout.width * c // 2,
                strip_y + LABEL_STRIP // 2,
                name,
                color="#F0F3F4",
                size=max(7, int(9 * self.zoom)),
            )
