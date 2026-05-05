import sys
import time
from optparse import OptionParser

import world.rescue_layout as rescue_layout
from planning.pddl import apply_action, is_applicable


def read_command(argv):
    usage = """
    USAGE:    python main.py -p PROBLEM -f PLANNER -l LAYOUT [options]
    EXAMPLE:  python main.py -p SimpleRescueProblem -f tinyBaseSearch -l tinyBase -q
    """
    parser = OptionParser(usage, add_help_option=False)
    parser.add_option("--help", action="help")

    PROBLEMS = ("SimpleRescueProblem", "MultiRescueProblem")
    parser.add_option(
        "-p", "--problem", dest="problem", help="Problem type: %s" % ", ".join(PROBLEMS)
    )
    parser.add_option(
        "-f",
        "--function",
        dest="function",
        help="Planning algorithm: forwardBFS, backwardSearch, aStarPlanner, tinyBaseSearch",
    )
    parser.add_option(
        "-h",
        "--heuristic",
        dest="heuristic",
        default="nullHeuristic",
        help="Heuristic for A* [default: nullHeuristic]: ignorePreconditions, ignoreDeleteLists",
    )
    parser.add_option(
        "-l",
        "--layout",
        dest="layout",
        help="Layout file name (without .lay extension)",
    )
    parser.add_option(
        "-m",
        "--htn",
        action="store_true",
        dest="htn",
        default=False,
        help="Use HTN planning mode",
    )
    parser.add_option(
        "-t",
        "--text",
        action="store_true",
        dest="text",
        default=False,
        help="Text-only display",
    )
    parser.add_option(
        "-q",
        "--quiet",
        action="store_true",
        dest="quiet",
        default=False,
        help="Minimal output, no graphics",
    )
    parser.add_option(
        "-z",
        "--zoom",
        type="float",
        dest="zoom",
        default=1.0,
        help="Graphics window zoom [default: 1.0]",
    )
    parser.add_option(
        "-x",
        "--frame-time",
        type="float",
        dest="frame_time",
        default=0.1,
        help="Delay between frames in seconds [default: 0.1]",
    )

    options, junk = parser.parse_args(argv)
    if junk:
        raise Exception("Unrecognized arguments: " + str(junk))
    if not options.layout:
        parser.error("-l/--layout is required")
    if not options.function and not options.htn:
        parser.error("-f/--function is required")

    return options


def load_problem(problem_name, layout):
    from planning.problems import SimpleRescueProblem, MultiRescueProblem

    problems = {
        "SimpleRescueProblem": SimpleRescueProblem,
        "MultiRescueProblem": MultiRescueProblem,
    }
    cls = problems.get(problem_name)
    if cls is None:
        raise Exception(
            f"Unknown problem: {problem_name}. Choose from: {list(problems)}"
        )
    return cls(layout)


def load_planner(fn_name):
    import planning.planner as planner_module

    fn = getattr(planner_module, fn_name, None)
    if fn is None:
        raise Exception(
            f"Unknown planning function: '{fn_name}'. Check planning/planner.py."
        )
    return fn


def load_heuristic(h_name):
    import planning.heuristics as h_module

    aliases = {
        "ignorePreconditions": "ignorePreconditionsHeuristic",
        "ignoreDeleteLists": "ignoreDeleteListsHeuristic",
        "null": "nullHeuristic",
    }
    real_name = aliases.get(h_name, h_name)
    h = getattr(h_module, real_name, None)
    if h is None:
        raise Exception(f"Unknown heuristic: '{h_name}'")
    return h


def execute_plan(plan, initial_state, display, frame_time):
    """Simulate plan execution step by step."""
    state = initial_state
    for action in plan:
        if not is_applicable(state, action):
            print(f"  [ERROR] Action not applicable: {action.name}")
            print(f"  Missing preconditions: {action.precond_pos - state}")
            return state, False
        state = apply_action(state, action)
        display.update(state, action)
    return state, True


def run(options):
    # Load layout
    layout = rescue_layout.get_layout(options.layout)
    if layout is None:
        raise Exception(f"Layout '{options.layout}' not found in layouts/ directory.")

    print(f"\n{'=' * 60}")
    print("  Operación Fénix - ISIS-1611 Inteligencia Artificial")
    print(f"{'=' * 60}")
    print(f"  Layout:   {options.layout}  ({layout.width}×{layout.height})")
    print(f"  Problema: {options.problem}")

    # Build problem
    problem = load_problem(options.problem, layout)
    initial_state = problem.initial_state
    objects = problem.objects

    print(f"  Pacientes: {objects['patients']}")
    print(f"  Suministros: {objects['supplies']}")
    print(f"  Puestos médicos: {objects['medical_posts']}")
    print(f"{'=' * 60}")

    # Build display
    if options.quiet:
        from view.text_display import NullGraphics

        display = NullGraphics()
    elif options.text:
        from view.text_display import TextDisplay

        display = TextDisplay()
    else:
        from view.graphics_display import GraphicsDisplay

        display = GraphicsDisplay(
            layout, zoom=options.zoom, frame_time=options.frame_time
        )

    display.initialize(layout, initial_state)

    # HTN mode
    if options.htn:
        from planning.htn import build_htn_hierarchy, hierarchicalSearch

        print("  Modo: HTN (Hierarchical Task Network)")
        hlas = build_htn_hierarchy(problem)
        if not hlas:
            print("  No se encontraron HLAs para este layout.")
            return
        print(f"  HLA raíz: {hlas[0].name}")
        t0 = time.time()
        plan = hierarchicalSearch(problem, hlas)
        elapsed = time.time() - t0
    else:
        # Classical planning
        fn_name = options.function
        print(f"  Planificador: {fn_name}")
        planner = load_planner(fn_name)
        t0 = time.time()
        if fn_name == "aStarPlanner":
            heuristic = load_heuristic(options.heuristic)
            print(f"  Heurística: {options.heuristic}")
            plan = planner(problem, heuristic)
        else:
            plan = planner(problem)
        elapsed = time.time() - t0

    print(f"\n  Tiempo de planificación: {elapsed:.3f}s")
    print(f"  Estados expandidos: {problem._expanded}")

    if not plan:
        print("  [FALLA] No se encontró un plan.")
        display.finish()
        return

    print(f"  Longitud del plan: {len(plan)} acciones")
    print("\n  Plan:")
    for i, action in enumerate(plan, 1):
        print(f"    {i:2d}. {action.name}")

    print("\n  Ejecutando plan...")
    final_state, success = execute_plan(
        plan, initial_state, display, options.frame_time
    )

    if success and problem.isGoalState(final_state):
        print("\n  ¡Misión completada exitosamente!")
    elif success:
        print("\n  [ADVERTENCIA] Plan ejecutado pero objetivo no alcanzado.")
    else:
        print("\n  [ERROR] Plan inválido — acción no aplicable durante ejecución.")

    display.finish()


if __name__ == "__main__":
    options = read_command(sys.argv[1:])
    run(options)
