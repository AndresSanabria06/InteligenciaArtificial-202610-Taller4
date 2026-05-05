from __future__ import annotations

from planning.pddl import State, Objects
from world.rescue_layout import RescueLayout


def build_initial_state(layout: RescueLayout) -> tuple[State, Objects]:
    """
    Convert a RescueLayout into a PDDL initial state (frozenset of fluents)
    and an objects dictionary for grounding action schemas.

    Fluent format (all are tuples):
        ("At", entity, cell)         – entity is at cell
        ("Adjacent", cell_a, cell_b) – cells are adjacent (bidirectional)
        ("Free", cell)               – cell is not occupied by the robot
        ("HandsFree", "robot")       – robot holds nothing
        ("Holding", "robot", obj)    – robot holds obj
        ("Pickable", obj)            – obj can be picked up
        ("MedicalPost", cell)        – cell is a medical post
        ("SuppliesReady", cell)      – supplies set up at medical post
        ("Rescued", patient)         – patient has been rescued
    """
    fluents: set = set()
    robot = "robot"

    robot_pos = layout.robot_position
    fluents.add(("At", robot, robot_pos))
    fluents.add(("HandsFree", robot))

    supplies = [f"supplies_{i}" for i in range(len(layout.supplies))]
    patients = [f"patient_{i}" for i in range(len(layout.patients))]

    for name, pos in zip(supplies, layout.supplies):
        fluents.add(("At", name, pos))
        fluents.add(("Pickable", name))

    for name, pos in zip(patients, layout.patients):
        fluents.add(("At", name, pos))
        fluents.add(("Pickable", name))

    for pos in layout.medical_posts:
        fluents.add(("MedicalPost", pos))

    for a, b in layout.get_adjacent_pairs():
        fluents.add(("Adjacent", a, b))
        fluents.add(("Adjacent", b, a))

    for cell in layout.get_all_cells():
        if cell != robot_pos:
            fluents.add(("Free", cell))

    objects: Objects = {
        "robots":        [robot],
        "cells":         layout.get_all_cells(),
        "supplies":      supplies,
        "patients":      patients,
        "medical_posts": layout.medical_posts[:],
        "objects":       supplies + patients,
    }

    return frozenset(fluents), objects
