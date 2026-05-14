from __future__ import annotations

from planning.pddl import ActionSchema, State, Objects, get_all_groundings
from planning.pddl import is_applicable

def nullHeuristic(
    state: State,
    goal: State,
    domain: list[ActionSchema],
    objects: Objects,
) -> float:
    """Trivial heuristic — always returns 0 (equivalent to uniform-cost search)."""
    return 0


# ---------------------------------------------------------------------------
# Punto 4a – Ignore-Preconditions Heuristic
# ---------------------------------------------------------------------------


def ignorePreconditionsHeuristic(
    state: State,
    goal: State,
    domain: list[ActionSchema],
    objects: Objects,
) -> float:
    """
    Estimate the number of actions needed to satisfy all goal fluents,
    ignoring all action preconditions.

    With no preconditions, any action can be applied at any time.
    Each action can satisfy all goal fluents in its add_list in one step.
    The minimum number of actions to cover all unsatisfied goal fluents is
    a lower bound on the true plan length → this heuristic is admissible.

    Algorithm (greedy set cover):
      1. Compute unsatisfied = goal − state  (fluents still needed).
      2. Ground all actions ignoring preconditions and collect their add_lists.
      3. Greedily pick the action whose add_list covers the most unsatisfied fluents.
      4. Repeat until all fluents are covered; count the actions used.

    Tip: frozenset supports set difference (-) and intersection (&).
         You only need to ground actions once per call (use get_applicable_actions
         with the initial state, or generate all groundings regardless of state).
         Remember: with no preconditions, every grounding is "applicable".
    """
    unsatisfied = goal - state
    if not unsatisfied:
        return 0

    all_actions = get_all_groundings(domain, objects)

    count = 0
    while unsatisfied:
        best_action = max(all_actions, key=lambda a: len(a.add_list & unsatisfied))

        covered = best_action.add_list & unsatisfied
        if not covered:
            return float('inf')

        unsatisfied -= covered
        count += 1

    return count


# ---------------------------------------------------------------------------
# Punto 4b – Ignore-Delete-Lists Heuristic
# ---------------------------------------------------------------------------


def ignoreDeleteListsHeuristic(
    state: State,
    goal: State,
    domain: list[ActionSchema],
    objects: Objects,
) -> float:
    """
    Estimate the plan cost by solving a relaxed problem where no action
    has a delete list (effects never remove fluents from the state).

    In this monotone relaxation, the state only grows over time (fluents are
    never removed), so hill-climbing always makes progress and cannot loop.

    Algorithm (hill-climbing on the relaxed problem):
      1. Start from the current state with a relaxed (monotone) apply function.
      2. At each step, pick the grounded action that adds the most unsatisfied
         goal fluents (greedy hill-climbing).
      3. Count steps until all goal fluents are satisfied (or until no progress).

    Tip: In the relaxed problem, apply_action never removes fluents.
         You can implement this by treating del_list as empty for all actions.
         Use get_applicable_actions to enumerate applicable grounded actions at
         each step (preconditions still apply in the relaxed model).
    """
    relaxed_state = set(state)
    count = 0
    max_steps = 1000  
    while not goal.issubset(frozenset(relaxed_state)):
        unsatisfied = goal - frozenset(relaxed_state)

        all_actions = get_all_groundings(domain, objects)
        applicable = [
            a for a in all_actions
            if is_applicable(frozenset(relaxed_state), a)
        ]

        if not applicable:
            return float('inf')

        best = max(applicable, key=lambda a: len(a.add_list & unsatisfied))

        if not (best.add_list & unsatisfied):
            return float('inf')

        relaxed_state |= best.add_list

        count += 1
        if count >= max_steps:
            return float('inf')

    return count