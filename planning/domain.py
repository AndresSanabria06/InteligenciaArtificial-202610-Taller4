from __future__ import annotations

from planning.pddl import ActionSchema

# ---------------------------------------------------------------------------
# Punto 1a – Complete the preconditions and effects of each action schema.
#
# Each schema uses string variable names as placeholders:
#   "r"         → the robot
#   "from_cell" → source cell       "to_cell" → destination cell
#   "obj"       → any pickable object
#   "s"         → medical supplies  "p" → patient
#   "loc"       → a cell (used as the robot's current location)
#
# Fluent templates are tuples whose elements are either variable names or
# literal constant strings. get_applicable_actions() will substitute
# variable names with real constants during grounding.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Move(r, from_cell, to_cell)
# Move the robot one step to an adjacent, free cell.
# This one is given as an example. You can use it as a template for the other actions.
# ---------------------------------------------------------------------------

MOVE: ActionSchema = ActionSchema(
    name="Move",
    parameters=["r", "from_cell", "to_cell"],
    precond_pos=[
        ("At", "r", "from_cell"),
        ("Adjacent", "from_cell", "to_cell"),
        ("Free", "to_cell"),
    ],
    precond_neg=[],
    add_list=[
        ("At", "r", "to_cell"),
        ("Free", "from_cell"),
    ],
    del_list=[
        ("At", "r", "from_cell"),
        ("Free", "to_cell"),
    ],
)


# ---------------------------------------------------------------------------
# PickUp(r, obj, loc)
# Pick up a pickable object at the robot's current cell.
# After pickup: the object is no longer At loc, and the robot is no longer HandsFree.
# ---------------------------------------------------------------------------

### Your code here ###
PICKUP: ActionSchema = None
### End of your code ###


# ---------------------------------------------------------------------------
# PutDown(r, obj, loc)
# Place a held object at the robot's current cell.
# After putdown: the object is At loc, and the robot is HandsFree again.
# ---------------------------------------------------------------------------

### Your code here ###
PUTDOWN: ActionSchema = None
### End of your code ###


# ---------------------------------------------------------------------------
# Rescue(r, p, loc)
# Rescue a patient who is at a medical post where supplies are ready.
# After rescue: patient is marked as Rescued and no longer At loc.
# ---------------------------------------------------------------------------

### Your code here ###
RESCUE: ActionSchema = None
### End of your code ###


# ---------------------------------------------------------------------------
# SetupSupplies(r, s, loc)
# Set up medical supplies at a medical post.
# The robot must be at loc, holding the supplies, and loc must be a MedicalPost.
# Note: there is no At(s, loc) precondition because the robot is carrying s;
# the fluent At(s, loc) was removed when the robot picked it up.
# ---------------------------------------------------------------------------

### Your code here ###
SETUP_SUPPLIES: ActionSchema = None
### End of your code ###


DOMAIN: list[ActionSchema] = [MOVE, PICKUP, PUTDOWN, RESCUE, SETUP_SUPPLIES]
