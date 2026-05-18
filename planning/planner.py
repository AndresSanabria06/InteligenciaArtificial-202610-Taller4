from __future__ import annotations
from collections import *
from collections.abc import Callable
import time
from planning.pddl import (
    Action,
    ActionSchema,
    Problem,
    State,
    Objects,
    get_all_groundings,
)
from planning.utils import Queue, PriorityQueue
from planning.heuristics import nullHeuristic


# ---------------------------------------------------------------------------
# Reference implementation – read and understand before coding the rest.
# ---------------------------------------------------------------------------


def tinyBaseSearch(problem: Problem) -> list[Action]:
    """
    Hardcoded plan for the tinyBase layout.
    The robot at (1,4) must: pick up supplies at (1,3), set them up at (1,2),
    pick up the patient at (1,1), bring them to (1,2), and execute Rescue.

    Useful to understand the Action object format and plan structure.
    """
    robot = "robot"
    supplies = "supplies_0"
    patient = "patient_0"

    c14 = (1, 4)  # robot start
    c13 = (1, 3)  # supplies
    c12 = (1, 2)  # medical post
    c11 = (1, 1)  # patient

    plan = [
        Action(
            "Move(robot,(1,4),(1,3))",
            [("At", robot, c14), ("Adjacent", c14, c13), ("Free", c13)],
            [],
            [("At", robot, c13), ("Free", c14)],
            [("At", robot, c14), ("Free", c13)],
        ),
        Action(
            "PickUp(robot,supplies_0,(1,3))",
            [
                ("At", robot, c13),
                ("At", supplies, c13),
                ("HandsFree", robot),
                ("Pickable", supplies),
            ],
            [],
            [("Holding", robot, supplies)],
            [("At", supplies, c13), ("HandsFree", robot)],
        ),
        Action(
            "Move(robot,(1,3),(1,2))",
            [("At", robot, c13), ("Adjacent", c13, c12), ("Free", c12)],
            [],
            [("At", robot, c12), ("Free", c13)],
            [("At", robot, c13), ("Free", c12)],
        ),
        Action(
            "SetupSupplies(robot,supplies_0,(1,2))",
            [("At", robot, c12), ("MedicalPost", c12), ("Holding", robot, supplies)],
            [("SuppliesReady", c12)],
            [("SuppliesReady", c12), ("HandsFree", robot)],
            [("Holding", robot, supplies)],
        ),
        Action(
            "Move(robot,(1,2),(1,1))",
            [("At", robot, c12), ("Adjacent", c12, c11), ("Free", c11)],
            [],
            [("At", robot, c11), ("Free", c12)],
            [("At", robot, c12), ("Free", c11)],
        ),
        Action(
            "PickUp(robot,patient_0,(1,1))",
            [
                ("At", robot, c11),
                ("At", patient, c11),
                ("HandsFree", robot),
                ("Pickable", patient),
            ],
            [],
            [("Holding", robot, patient)],
            [("At", patient, c11), ("HandsFree", robot)],
        ),
        Action(
            "Move(robot,(1,1),(1,2))",
            [("At", robot, c11), ("Adjacent", c11, c12), ("Free", c12)],
            [],
            [("At", robot, c12), ("Free", c11)],
            [("At", robot, c11), ("Free", c12)],
        ),
        Action(
            "PutDown(robot,patient_0,(1,2))",
            [("At", robot, c12), ("Holding", robot, patient)],
            [],
            [("At", patient, c12), ("HandsFree", robot)],
            [("Holding", robot, patient)],
        ),
        Action(
            "Rescue(robot,patient_0,(1,2))",
            [
                ("At", robot, c12),
                ("At", patient, c12),
                ("MedicalPost", c12),
                ("SuppliesReady", c12),
            ],
            [],
            [("Rescued", patient)],
            [("At", patient, c12)],
        ),
    ]
    return plan


# ---------------------------------------------------------------------------
# Punto 2 – Forward Planning
# ---------------------------------------------------------------------------


def forwardBFS(problem: Problem) -> list[Action]:
    """
    Forward BFS in state space.

    Explore states reachable from the initial state by applying actions,
    in breadth-first order, until a goal state is found.

    Returns a list of Action objects forming a valid plan, or [] if no plan exists.

    Tip: The state is a frozenset of fluents. Use problem.getSuccessors(state)
         to get (next_state, action, cost) triples. Track visited states to
         avoid revisiting the same state twice (graph search, not tree search).
    """
    ### Your code here ###
    estado_inicial = problem.getStartState()
    if problem.isGoalState(estado_inicial):
        return []
    cola_por_revisar = [(estado_inicial, [])]
    ya_visitados = {estado_inicial}
    while len(cola_por_revisar) > 0:
        state, plan = cola_por_revisar.pop(0)
        sucesores = problem.getSuccessors(state)
        for next_state, action, cost in sucesores:
            if next_state not in ya_visitados:
                ya_visitados.add(next_state)
                plan_nuevo= plan + [action]
                if problem.isGoalState(next_state):
                    return plan_nuevo
                cola_por_revisar.append((next_state, plan_nuevo))
    return []
    ### End of your code ###


# ---------------------------------------------------------------------------
# Punto 3 – Backward Planning
# ---------------------------------------------------------------------------


def regress(goal_set: State, action: Action) -> State | None:
    """
    Compute the regression of goal_set through action.

    Given a goal description (set of fluents that must be true) and an action,
    return the new goal description that, if satisfied, guarantees the original
    goal is satisfied after executing action.

    REGRESS(g, a) = (g − ADD(a)) ∪ PRECOND_pos(a)
        IF:  ADD(a) ∩ g ≠ ∅   (action is relevant: contributes to the goal)
        AND: DEL(a) ∩ g = ∅   (action does not undo any goal fluent)
    Returns None if the action is not relevant or creates a contradiction.

    Tip: Use frozenset operations: intersection (&), difference (-), union (|).
         Check relevance first, then check for contradictions, then compute.
    """
    ### Your code here ###
    objetivo = frozenset(goal_set)

    efectos_agregados = frozenset(action.add_list)
    efectos_eliminados = frozenset(action.del_list)
    precondiciones = frozenset(action.precond_pos)

    if not (efectos_agregados & objetivo):
        return None

    if efectos_eliminados & objetivo:
        return None

    objetivo_regresado = ((objetivo - efectos_agregados)| precondiciones)

    return frozenset(objetivo_regresado)

    ### End of your code ###



def backwardSearch(problem: Problem) -> list[Action]:
    """
    Backward search (regression search) from the goal.

    Start from the goal description and apply action regressions until
    the resulting goal is satisfied by the initial state.

    Returns a list of Action objects forming a valid plan (in forward order),
    or [] if no plan exists.

    Tip: The "state" in backward search is a frozenset of fluents that must
         be true (a partial goal description). The initial state is reached
         when all fluents in the current goal are satisfied by problem.initial_state.
         Only consider actions whose add_list has at least one unsatisfied goal fluent
         (relevant actions). Use regress() to compute the new subgoal.
         Skip subgoals that contain static predicates (MedicalPost, Adjacent,
         Pickable) that are false in the initial state — these are dead ends.
    """
    ### Your code here ###
    estado_inicial = frozenset(problem.initial_state)
    objetivo = frozenset(problem.goal)

    if objetivo.issubset(estado_inicial):
        return []

    todas_las_acciones = get_all_groundings(problem.domain, problem.objects)

    acciones_por_condicion = {}

    for accion in todas_las_acciones:
        for condicion in accion.add_list:
            acciones_por_condicion.setdefault(condicion, []).append(accion)

    predicados_estaticos = {
        "MedicalPost",
        "Adjacent",
        "Pickable",
        "Free"
    }

    cola = Queue()
    cola.push((objetivo, []))

    visitados = {objetivo}

    while not cola.isEmpty():
        objetivo_actual, plan = cola.pop()
        problem._expanded += 1
        posiciones = {}
        no_se_puede = False

        for condicion in objetivo_actual:
            if condicion[0] == "At":

                objeto = condicion[1]
                posicion = condicion[2]

                if objeto in posiciones and posiciones[objeto] != posicion:

                    no_se_puede = True
                    break

                posiciones[objeto] = posicion

        if no_se_puede:
            continue

        acciones_relevantes = set()

        for condicion in objetivo_actual:
            if condicion in acciones_por_condicion:
                acciones_relevantes.update(
                    acciones_por_condicion[condicion]
                )

        for accion in acciones_relevantes:
            regresion = regress(objetivo_actual, accion)

            if regresion is None:
                continue

            if any(
                f[0] in predicados_estaticos
                and f not in estado_inicial
                for f in regresion
            ):
                continue

            if regresion.issubset(estado_inicial):
                return [accion] + plan

            if regresion not in visitados:
                visitados.add(regresion)
                cola.push((regresion, [accion] + plan))

    return []

    ### End of your code ###
    
# ---------------------------------------------------------------------------
# Punto 4 – A* Planner
# ---------------------------------------------------------------------------

# Heuristic signature:  heuristic(state, goal, domain, objects) -> float
Heuristic = Callable[[State, State, list[ActionSchema], Objects], float]


def aStarPlanner(
    problem: Problem,
    heuristic: Heuristic = nullHeuristic,
) -> list[Action]:
    """
    Forward A* search guided by a heuristic.

    Combines the real accumulated cost g(n) with the heuristic estimate h(n)
    to prioritize which state to expand next: f(n) = g(n) + h(n).

    Returns a list of Action objects forming a valid plan, or [] if no plan exists.

    Tip: The heuristic signature is heuristic(state, goal, domain, objects) → float.
         Use PriorityQueue with priority = g + h(next_state).
         Track the best g-cost seen for each state to avoid stale expansions.
    """
    initial_state = problem.getStartState()
    if problem.isGoalState(initial_state):
        return []

    frontier = PriorityQueue()
    h0 = heuristic(initial_state, problem.goal, problem.domain, problem.objects)
    frontier.push((initial_state, [], 0), h0)

    best_g = {initial_state: 0}

    while not frontier.isEmpty():
        state, plan, g = frontier.pop()

        if problem.isGoalState(state):
            return plan

        if g > best_g.get(state, float('inf')):
            continue

        for next_state, action, cost in problem.getSuccessors(state):
            new_g = g + cost
            if new_g < best_g.get(next_state, float('inf')):
                best_g[next_state] = new_g
                h = heuristic(next_state, problem.goal, problem.domain, problem.objects)
                new_plan = plan + [action]
                frontier.push((next_state, new_plan, new_g), new_g + h)

    return []

# Aliases used by the command-line argument parser
tinyBaseSearch = tinyBaseSearch
forwardBFS = forwardBFS
backwardSearch = backwardSearch
aStarPlanner = aStarPlanner
