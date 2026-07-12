"""
Seed script: Python Debugging learning plan.
Run from the project root:  python seed_debugging_plan.py
"""

import sys
from app.database import SessionLocal
from app.services import topic as topic_svc, plan as plan_svc

TOPICS = [
    # (name, description, difficulty, tags, parent_name)
    # Phase 1 — Foundations
    ("pdb basics",
     "Breakpoints, stepping commands (n/s/c/l/p), and post-mortem debugging with pdb.pm().",
     "beginner", "stdlib,debugger", None),

    ("breakpoint()",
     "The modern built-in entry point for debugging. Controlling it via the PYTHONBREAKPOINT env var.",
     "beginner", "stdlib,debugger", None),

    ("Reading tracebacks",
     "Anatomy of a traceback, chained exceptions, __cause__ vs __context__, and ExceptionGroup (3.11+).",
     "beginner", "exceptions", None),

    ("Logging vs print debugging",
     "The logging module: levels, handlers, formatters, and when to reach for it over print().",
     "beginner", "stdlib,logging", None),

    # Phase 2 — Tools
    ("pdb++ and ipdb",
     "Drop-in pdb replacements with syntax highlighting, tab completion, and sticky mode.",
     "intermediate", "debugger,tools", None),

    ("VS Code debugger",
     "Launch configs, conditional breakpoints, logpoints, watch expressions, and the debug console.",
     "intermediate", "tools,ide", None),

    ("traceback module",
     "Capturing, formatting, and re-raising exceptions programmatically with the traceback module.",
     "intermediate", "stdlib,exceptions", None),

    ("warnings module",
     "Issuing, filtering, and turning warnings into errors. The -W flag and PYTHONWARNINGS.",
     "intermediate", "stdlib", None),

    # Phase 3 — Intermediate Techniques
    ("Debugging with pytest",
     "Using --pdb, -s, pytest.set_trace(), and the pytest-xdist interaction with debugging.",
     "intermediate", "testing,debugger", None),

    ("sys.settrace and sys.setprofile",
     "How debuggers are implemented. Writing a minimal tracer to understand the trace event model.",
     "advanced", "internals,stdlib", None),

    ("Inspecting objects",
     "dir(), vars(), inspect module, __dict__, __slots__, and repr vs str for debugging.",
     "intermediate", "stdlib,introspection", None),

    ("Debugging segfaults and C extensions",
     "faulthandler for segfaults, gdb with python-gdb.py, and debugging Cython/ctypes code.",
     "advanced", "c-extensions,tools", None),

    # Phase 4 — Advanced
    ("Remote debugging with debugpy",
     "Attaching VS Code or any DAP client to a running process, including Docker containers.",
     "advanced", "debugger,tools", None),

    ("Debugging async code",
     "asyncio debug mode (PYTHONASYNCIODEBUG), aiomonitor, and diagnosing coroutine lifecycle issues.",
     "advanced", "async,debugger", None),

    ("Memory debugging",
     "tracemalloc for allocation tracing, objgraph for reference cycles, and weakref patterns.",
     "advanced", "memory,profiling", None),

    ("Performance debugging",
     "cProfile, profile, py-spy for sampling profiling, and reading flame graphs.",
     "advanced", "profiling,performance", None),
]


def main() -> None:
    db = SessionLocal()
    try:
        print("Creating topics...")
        created: dict[str, object] = {}
        for name, desc, difficulty, tags, parent_name in TOPICS:
            parent_id = created[parent_name].id if parent_name else None
            topic = topic_svc.create_topic(
                db,
                name=name,
                description=desc,
                difficulty=difficulty,
                tags=tags,
                parent_id=parent_id,
            )
            created[name] = topic
            print(f"  ✓ {name}")

        print("\nCreating learning plan...")
        plan = plan_svc.create_plan(
            db,
            name="Python Debugging",
            description=(
                "A structured path from pdb basics through advanced memory and "
                "performance debugging. Four phases: Foundations → Tools → "
                "Intermediate Techniques → Advanced."
            ),
        )
        print(f"  ✓ Plan '{plan.name}' (id={plan.id})")

        print("\nAdding topics to plan...")
        # Add in curriculum order (same as TOPICS list)
        for name, *_ in TOPICS:
            topic = created[name]
            plan_svc.add_topic_to_plan(db, plan_id=plan.id, topic_id=topic.id)
            print(f"  ✓ {name}")

        print(f"\nDone! Visit http://localhost:8000/plans/{plan.id} to see your plan.")

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
