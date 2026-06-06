"""pymdp simulation harness.

The package exports the runtime helpers lazily so render-time metadata imports
can read ``simulation.pymdp_config`` without importing the JAX/pymdp stack.
"""

from typing import Any

__all__ = [
    "RunLogger",
    "TMazeSpec",
    "build_tmaze_generative_model",
    "pymdp_available",
    "run_and_persist",
    "run_si_tmaze",
]


def __getattr__(name: str) -> Any:
    if name == "RunLogger":
        from simulation.logging_utils import RunLogger

        return RunLogger
    if name in {"pymdp_available", "run_and_persist", "run_si_tmaze"}:
        from simulation import si_runner

        return getattr(si_runner, name)
    if name in {"TMazeSpec", "build_tmaze_generative_model"}:
        from simulation import tmaze_model

        return getattr(tmaze_model, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
