from __future__ import annotations
from collections import deque

from planning.pddl import Action, Problem, apply_action, is_applicable
from planning.domain import MOVE, PICKUP, PUTDOWN, RESCUE, SETUP_SUPPLIES


# ---------------------------------------------------------------------------
# HTN Infrastructure
# ---------------------------------------------------------------------------


class HLA:
    """
    A High-Level Action (HLA) in HTN planning.

    An HLA is an abstract task that can be refined into sequences of
    more primitive actions (or other HLAs). Each refinement is a list
    of HLA or Action objects.

    name:        Human-readable name for display
    refinements: List of possible refinements, each a list of HLA/Action objects
    """

    def __init__(self, name: str, refinements: list[list] | None = None) -> None:
        self.name = name
        self.refinements = refinements or []

    def __repr__(self) -> str:
        return f"HLA({self.name})"


def is_primitive(action: Action | HLA) -> bool:
    """Return True if action is a primitive (grounded Action), False if it is an HLA."""
    return isinstance(action, Action)


def is_plan_primitive(plan: list[Action | HLA]) -> bool:
    """Return True if every step in the plan is a primitive action."""
    return all(is_primitive(step) for step in plan)


# ---------------------------------------------------------------------------
# Punto 5a – hierarchicalSearch
# ---------------------------------------------------------------------------


def hierarchicalSearch(problem: Problem, hlas: list[HLA]) -> list[Action]:
    """
    HTN planning via BFS over hierarchical plan refinements.

    Start with an initial plan containing a single top-level HLA.
    At each step, find the first non-primitive step in the plan and
    replace it with one of its refinements. Continue until the plan
    is fully primitive and achieves the goal when executed from the
    initial state.

    Returns a list of primitive Action objects, or [] if no plan found.
    """

    def simulate_execution(plan: list[Action | HLA], initial_state, goal_test) -> bool:
        state = initial_state
        for step in plan:
            if not is_primitive(step):
                return False  # Should not happen for primitive plans
            if not is_applicable(state, step):
                return False
            state = apply_action(state, step)
        return goal_test(state)

    if not hlas:
        return []

    initial_plan = [hlas[0]]
    queue = deque([initial_plan])

    while queue:
        plan = queue.popleft()
        if is_plan_primitive(plan) and simulate_execution(plan, problem.initial_state, problem.isGoalState):
            return plan

        for i, step in enumerate(plan):
            if not is_primitive(step):
                hla = step
                break
        else:
            continue

        for refinement in hla.refinements:
            new_plan = plan[:i] + refinement + plan[i + 1 :]
            queue.append(new_plan)

    return []


# ---------------------------------------------------------------------------
# Punto 5b – HLA Definitions
# ---------------------------------------------------------------------------


def build_htn_hierarchy(problem: Problem) -> list[HLA]:
    """
    Build HTN HLAs for the rescue domain.

    The hierarchy defines four HLA types:
      - Navigate(from, to):       Move the robot step by step from one cell to another
      - PrepareSupplies(s, m):    Collect supplies and set them up at the medical post
      - ExtractPatient(p, m):     Pick up the patient and bring them to the medical post
      - FullRescueMission(s,p,m): Complete one rescue: prepare supplies + extract + rescue
    """
    from itertools import permutations

    layout = problem.layout
    robot_pos = layout.robot_position
    supplies = problem.objects["supplies"]
    patients = problem.objects["patients"]
    medical_posts = problem.objects["medical_posts"]

    if not medical_posts or not patients or not supplies:
        return []

    primary_post = medical_posts[0]
    all_cells = layout.get_all_cells()

    adjacency: dict[tuple[int, int], list[tuple[int, int]]] = {cell: [] for cell in all_cells}
    for a, b in layout.get_adjacent_pairs():
        adjacency[a].append(b)
        adjacency[b].append(a)

    def find_shortest_paths(start: tuple[int, int], goal: tuple[int, int], limit: int = 3) -> list[list[tuple[int, int]]]:
        if start == goal:
            return [[start]]

        distances: dict[tuple[int, int], int] = {start: 0}
        predecessors: dict[tuple[int, int], list[tuple[int, int]]] = {start: []}
        queue = deque([start])

        while queue:
            current = queue.popleft()
            current_dist = distances[current]
            for neighbor in adjacency[current]:
                if neighbor not in distances:
                    distances[neighbor] = current_dist + 1
                    predecessors[neighbor] = [current]
                    queue.append(neighbor)
                elif distances[neighbor] == current_dist + 1:
                    predecessors[neighbor].append(current)

        if goal not in predecessors:
            return []

        paths: list[list[tuple[int, int]]] = []

        def backtrack(cell: tuple[int, int], path: list[tuple[int, int]]) -> None:
            if len(paths) >= limit:
                return
            if cell == start:
                paths.append([start] + path)
                return
            for pred in predecessors[cell]:
                backtrack(pred, [cell] + path)

        backtrack(goal, [])
        return paths

    navigate_hlas: dict[tuple[tuple[int, int], tuple[int, int]], HLA] = {}
    for source in all_cells:
        for target in all_cells:
            navigate_hlas[(source, target)] = HLA(f"Navigate({source},{target})")

    for source in all_cells:
        for target in all_cells:
            hla = navigate_hlas[(source, target)]
            if source == target:
                hla.refinements.append([])
                continue
            for path in find_shortest_paths(source, target):
                moves: list[Action] = []
                for current, next_cell in zip(path, path[1:]):
                    moves.append(
                        MOVE.ground({"r": "robot", "from_cell": current, "to_cell": next_cell})
                    )
                if moves:
                    hla.refinements.append(moves)

    def make_prepare_supplies(start: tuple[int, int], supply_name: str, supply_pos: tuple[int, int], post_pos: tuple[int, int]) -> HLA:
        pickup = PICKUP.ground({"r": "robot", "obj": supply_name, "loc": supply_pos})
        setup = SETUP_SUPPLIES.ground({"r": "robot", "s": supply_name, "loc": post_pos})
        return HLA(
            f"PrepareSupplies({start},{supply_name},{post_pos})",
            [[
                navigate_hlas[(start, supply_pos)],
                pickup,
                navigate_hlas[(supply_pos, post_pos)],
                setup,
            ]],
        )

    def make_extract_patient(start: tuple[int, int], patient_name: str, patient_pos: tuple[int, int], post_pos: tuple[int, int]) -> HLA:
        pickup = PICKUP.ground({"r": "robot", "obj": patient_name, "loc": patient_pos})
        putdown = PUTDOWN.ground({"r": "robot", "obj": patient_name, "loc": post_pos})
        rescue = RESCUE.ground({"r": "robot", "p": patient_name, "loc": post_pos})
        return HLA(
            f"ExtractPatient({start},{patient_name},{post_pos})",
            [[
                navigate_hlas[(start, patient_pos)],
                pickup,
                navigate_hlas[(patient_pos, post_pos)],
                putdown,
                rescue,
            ]],
        )

    def make_full_rescue(
        start: tuple[int, int],
        supply_name: str,
        supply_pos: tuple[int, int],
        patient_name: str,
        patient_pos: tuple[int, int],
        post_pos: tuple[int, int],
    ) -> tuple[HLA, HLA, HLA]:
        prepare = make_prepare_supplies(start, supply_name, supply_pos, post_pos)
        extract = make_extract_patient(post_pos, patient_name, patient_pos, post_pos)
        full = HLA(
            f"FullRescueMission({supply_name},{patient_name},{post_pos})",
            [[prepare, extract]],
        )
        return full, prepare, extract

    def build_ordered_mission_sequence(order: tuple[int, ...]) -> list[HLA]:
        sequence: list[HLA] = []
        start_pos = robot_pos
        for idx in order:
            supply_name = supplies[idx]
            patient_name = patients[idx]
            supply_pos = layout.supplies[idx]
            patient_pos = layout.patients[idx]
            full, _, _ = make_full_rescue(
                start_pos,
                supply_name,
                supply_pos,
                patient_name,
                patient_pos,
                primary_post,
            )
            sequence.append(full)
            start_pos = primary_post
        return sequence

    root = HLA("AllRescueMissions")
    mission_hlas: list[HLA] = []

    if len(patients) == 1:
        order = (0,)
        sequence = build_ordered_mission_sequence(order)
        root.refinements.append(sequence)
    else:
        max_orders = 6
        all_orders = list(permutations(range(len(patients))))
        if len(all_orders) > max_orders:
            all_orders = all_orders[:max_orders]
        for order in all_orders:
            sequence = build_ordered_mission_sequence(order)
            root.refinements.append(sequence)

    return [root] + list(navigate_hlas.values())
