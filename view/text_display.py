import time

SLEEP_TIME = 0.05


class NullGraphics:
    def initialize(self, layout, state): pass
    def update(self, state, action=None): pass
    def finish(self): pass
    def pause(self): pass


class TextDisplay:
    """Minimal text output for plan execution."""

    def initialize(self, layout, state):
        print("=" * 60)
        print("Operación Fénix – Modo Texto")
        print("=" * 60)
        self._print_state(state, action=None)

    def update(self, state, action=None):
        if action:
            print(f"\n  Ejecutando: {action.name}")
        self._print_state(state, action)
        time.sleep(SLEEP_TIME)

    def finish(self):
        print("\n" + "=" * 60)
        print("Misión completada.")
        print("=" * 60)

    def pause(self):
        time.sleep(SLEEP_TIME)

    def _print_state(self, state, action):
        # Print a subset of interesting fluents
        at_fluents = sorted(f for f in state if f[0] == "At")
        holding = sorted(f for f in state if f[0] == "Holding")
        rescued = sorted(f for f in state if f[0] == "Rescued")
        supplies_ready = sorted(f for f in state if f[0] == "SuppliesReady")

        print("  Posiciones:", at_fluents)
        if holding:
            print("  Sosteniendo:", holding)
        if rescued:
            print("  Rescatados:", rescued)
        if supplies_ready:
            print("  Suministros listos en:", supplies_ready)
