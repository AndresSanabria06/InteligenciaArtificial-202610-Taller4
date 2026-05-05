from __future__ import annotations

from itertools import product


# ---------------------------------------------------------------------------
# Type aliases (for readability in signatures and docstrings)
#
#   Fluent  – an immutable tuple representing one logical fact, e.g.
#             ("At", "robot", (1, 2))  or  ("HandsFree", "robot")
#   State   – a frozenset of Fluents describing the world at one moment
#   Objects – a dict produced by build_initial_state:
#             {"robots": [...], "cells": [...], "supplies": [...],
#              "patients": [...], "medical_posts": [...], "objects": [...]}
# ---------------------------------------------------------------------------
Fluent = tuple
State = frozenset[Fluent]
Objects = dict[str, list]


class ActionSchema:
    """
    A lifted (schematic) PDDL action with variable placeholders.

    Parameters are variable names (strings). Fluent templates are tuples
    whose elements are either variable names (found in parameters) or
    literal constant strings/values.

    Example:
        ActionSchema("Move", ["r", "from_cell", "to_cell"],
            precond_pos=[("At", "r", "from_cell"), ...], ...)
    """

    def __init__(
        self,
        name: str,
        parameters: list[str],
        precond_pos: list[Fluent],
        precond_neg: list[Fluent],
        add_list: list[Fluent],
        del_list: list[Fluent],
    ) -> None:
        self.name = name
        self.parameters = parameters
        self.precond_pos = precond_pos
        self.precond_neg = precond_neg
        self.add_list = add_list
        self.del_list = del_list

    def ground(self, binding: dict[str, object]) -> Action:
        """
        Return a grounded Action by substituting variable names with constants.
        binding: dict mapping variable name -> constant value.
        """

        def sub(fluent: Fluent) -> Fluent:
            return tuple(binding.get(arg, arg) for arg in fluent)  # type: ignore[return-value]

        name = (
            self.name + "(" + ", ".join(str(binding[p]) for p in self.parameters) + ")"
        )
        return Action(
            name,
            [sub(f) for f in self.precond_pos],
            [sub(f) for f in self.precond_neg],
            [sub(f) for f in self.add_list],
            [sub(f) for f in self.del_list],
        )


class Action:
    """
    A fully grounded PDDL action with concrete fluent tuples.

    precond_pos: fluents that must be TRUE for the action to apply
    precond_neg: fluents that must be FALSE for the action to apply
    add_list:    fluents added to the state after execution
    del_list:    fluents removed from the state after execution
    """

    precond_pos: frozenset[Fluent]
    precond_neg: frozenset[Fluent]
    add_list: frozenset[Fluent]
    del_list: frozenset[Fluent]

    def __init__(
        self,
        name: str,
        precond_pos: list[Fluent],
        precond_neg: list[Fluent],
        add_list: list[Fluent],
        del_list: list[Fluent],
    ) -> None:
        self.name = name
        self.precond_pos = frozenset(precond_pos)
        self.precond_neg = frozenset(precond_neg)
        self.add_list = frozenset(add_list)
        self.del_list = frozenset(del_list)

    def __repr__(self) -> str:
        return f"Action({self.name})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Action) and self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)


class Problem:
    """
    A PDDL planning problem.

    initial_state: frozenset of fluents describing the world at time 0
    goal:          frozenset of fluents that must hold in the goal state
    domain:        list of ActionSchema objects (the available action templates)
    objects:       dict mapping type names to lists of constants
    """

    initial_state: State
    goal: State
    domain: list[ActionSchema]
    objects: Objects

    def __init__(
        self,
        initial_state: State,
        goal: State,
        domain: list[ActionSchema],
        objects: Objects,
    ) -> None:
        self.initial_state = initial_state
        self.goal = goal
        self.domain = domain
        self.objects = objects
        self._expanded = 0

    def getStartState(self) -> State:
        return self.initial_state

    def isGoalState(self, state: State) -> bool:
        return self.goal.issubset(state)

    def getSuccessors(self, state: State) -> list[tuple[State, Action, int]]:
        """Return list of (next_state, action, cost=1) triples."""
        self._expanded += 1
        if not hasattr(self, "_all_groundings"):
            self._all_groundings = get_all_groundings(self.domain, self.objects)
        successors = []
        for action in self._all_groundings:
            if is_applicable(state, action):
                successors.append((apply_action(state, action), action, 1))
        return successors

    def getCostOfActions(self, actions: list[Action]) -> int:
        return len(actions) if actions else 0


# ---------------------------------------------------------------------------
# Punto 1b – Functions students must implement
# ---------------------------------------------------------------------------


def is_applicable(state: State, action: Action) -> bool:
    """
    Return True if action can be executed in state.

    An action is applicable if:
      - All fluents in action.precond_pos are present in state.
      - No fluent  in action.precond_neg is present in state.

    Tip: frozenset supports the .issubset() method and the .isdisjoint() method.
    """
    ### Your code here ###
    return False
    ### End of your code ###


def apply_action(state: State, action: Action) -> State:
    """
    Return the new state obtained by executing action in state.

    RESULT(s, a) = (s − DEL(a)) ∪ ADD(a)

    Tip: frozenset supports set arithmetic: `|` (union) and `-` (difference).
    The order matters: first remove del_list, then add add_list.
    """
    ### Your code here ###
    return frozenset({})
    ### End of your code ###


def get_all_groundings(domain: list[ActionSchema], objects: Objects) -> list[Action]:
    """
    Return ALL grounded actions for every schema in domain,
    regardless of applicability. Used internally by Problem and backward search.
    """
    type_map: dict[str, list] = {
        "r": objects["robots"],
        "loc": objects["cells"],
        "from_cell": objects["cells"],
        "to_cell": objects["cells"],
        "obj": objects["objects"],
        "s": objects["supplies"],
        "p": objects["patients"],
    }
    groundings: list[Action] = []
    for schema in domain:
        domains = [type_map.get(param, []) for param in schema.parameters]
        if any(len(d) == 0 for d in domains):
            continue
        for values in product(*domains):
            if schema.name == "Move" and len(set(values)) < len(values):
                continue
            binding = dict(zip(schema.parameters, values))
            groundings.append(schema.ground(binding))
    return groundings


def get_applicable_actions(
    state: State,
    domain: list[ActionSchema],
    objects: Objects,
) -> list[Action]:
    """
    Return a list of all grounded actions that are applicable in state.

    For each ActionSchema in domain, enumerate every possible binding of its
    parameters to constants from objects, ground the schema, and check if
    the grounded action is applicable.

    Parameter types are inferred from the parameter names:
        - Parameters named "r"                        → objects["robots"]
        - Parameters named "loc", "from_cell", "to_cell" → objects["cells"]
        - Parameters named "obj"                      → objects["objects"]
        - Parameters named "s"                        → objects["supplies"]
        - Parameters named "p"                        → objects["patients"]

    Tip: Use itertools.product to enumerate all combinations of constants.
         Then call action_schema.ground(binding) and is_applicable(state, grounded).
         Or use get_all_groundings() and filter the results by applicability.
    """
    ### Your code here ###
    return []
    ### End of your code ###
