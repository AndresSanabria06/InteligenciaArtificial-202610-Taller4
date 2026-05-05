def format_color(r, g, b):
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


# Color palette — high contrast, visually distinct per element type
WALL_COLOR     = "#2C3E50"  # dark slate
FLOOR_COLOR    = "#F5F2EC"  # warm ivory
ROBOT_COLOR    = "#2471A3"  # cobalt blue
PATIENT_COLOR  = "#C0392B"  # crimson red
SUPPLIES_COLOR = "#E67E22"  # amber orange
MEDICAL_COLOR  = "#1E8449"  # forest green
RESCUED_COLOR  = "#27AE60"  # bright emerald
HOLDING_COLOR  = "#F39C12"  # golden yellow (holding indicator ring)


def _import_tk():
    try:
        import tkinter as tk
        return tk
    except ImportError:
        return None


class Canvas:
    """
    Tkinter canvas wrapper for the planning visualizer.
    Falls back gracefully when tkinter is unavailable.
    """

    def __init__(self, width, height, zoom=1.0):
        self.tk = _import_tk()
        self.available = self.tk is not None
        self.zoom = zoom
        self.w = int(width * zoom)
        self.h = int(height * zoom)
        self.root = None
        self.canvas = None

        if self.available:
            try:
                self.root = self.tk.Tk()
                self.root.title("Operación Fénix – Planificador SAR")
                self.canvas = self.tk.Canvas(
                    self.root, width=self.w, height=self.h, bg=WALL_COLOR
                )
                self.canvas.pack()
                self.root.update()
            except Exception:
                self.available = False

    def draw_rect(self, x, y, w, h, fill, outline="", width=1):
        if not self.available:
            return None
        return self.canvas.create_rectangle(
            x, y, x + w, y + h, fill=fill, outline=outline, width=width
        )

    def draw_oval(self, cx, cy, r, fill, outline="black", width=2):
        if not self.available:
            return None
        return self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r, fill=fill, outline=outline, width=width
        )

    def draw_polygon(self, points, fill, outline="black", width=2):
        if not self.available:
            return None
        return self.canvas.create_polygon(
            points, fill=fill, outline=outline, width=width
        )

    def draw_line(self, x1, y1, x2, y2, fill="black", width=2):
        if not self.available:
            return None
        return self.canvas.create_line(x1, y1, x2, y2, fill=fill, width=width)

    def draw_text(self, x, y, text, color="black", size=10, bold=False):
        if not self.available:
            return None
        weight = "bold" if bold else "normal"
        font = ("Helvetica", max(1, int(size * self.zoom)), weight)
        return self.canvas.create_text(x, y, text=text, fill=color, font=font)

    def delete(self, item):
        if self.available and item is not None:
            self.canvas.delete(item)

    def update(self):
        if self.available:
            try:
                self.root.update()
            except Exception:
                self.available = False

    def sleep(self, seconds):
        if self.available:
            try:
                self.root.after(int(seconds * 1000), self.root.quit)
                self.root.mainloop()
            except Exception:
                import time
                time.sleep(seconds)
        else:
            import time
            time.sleep(seconds)

    def destroy(self):
        if self.available and self.root:
            try:
                self.root.destroy()
            except Exception:
                pass
