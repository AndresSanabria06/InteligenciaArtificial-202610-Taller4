from __future__ import annotations

from planning.pddl import Problem
from planning.domain import DOMAIN
from world.rescue_layout import RescueLayout
from world.rescue_rules import build_initial_state


class SimpleRescueProblem(Problem):
    """
    Planning problem with a single patient to rescue.

    Goal: Rescued(patient_0)

    The robot must:
      1. Pick up medical supplies and set them up at the medical post.
      2. Bring the patient to the medical post.
      3. Execute the Rescue action.

    Tip: The goal is a frozenset containing the single fluent ("Rescued", "patient_0").
         Use problem.isGoalState(state) to test whether a state satisfies the goal.
    """

    def __init__(self, layout: RescueLayout) -> None:
        initial_state, objects = build_initial_state(layout)

        ### Your code here ###
        # Define the goal: patient_0 must be rescued.
        # Tip: The goal is a frozenset of fluents that must all be True in the goal state.
        goal = frozenset({})
        ### End of your code ###

        super().__init__(initial_state, goal, DOMAIN, objects)
        self.layout = layout


class MultiRescueProblem(Problem):
    """
    Planning problem with multiple patients to rescue.

    Goal: Rescued(patient_0) ∧ Rescued(patient_1) ∧ ... ∧ Rescued(patient_n)

    The robot must rescue every patient listed in the layout.

    Tip: Build the goal as a frozenset of ("Rescued", patient) fluents,
         one for each patient in objects["patients"].
    """

    def __init__(self, layout: RescueLayout) -> None:
        initial_state, objects = build_initial_state(layout)

        ### Your code here ###
        # Define the goal: every patient must be rescued.
        # Tip: Use a set comprehension over objects["patients"].
        goal = frozenset({})
        ### End of your code ###

        super().__init__(initial_state, goal, DOMAIN, objects)
        self.layout = layout
