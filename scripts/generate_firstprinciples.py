#!/usr/bin/env python3
"""Emit first-principles OPD<->active-inference artifacts (thin orchestrator).

Writes the deterministic correspondence map, taxonomy, and divergence /
reward-tilting / exposure-bias / SDPG demonstrations, and (by default) runs the
two-agent pymdp distillation classroom so ``output/data/firstprinciples/
classroom.json`` exists for manuscript hydration. Pass ``--no-classroom`` to
skip the pymdp rollout (faster; leaves classroom tokens at their defaults).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from firstprinciples import artifacts
from firstprinciples.classroom import ClassroomConfig, run_classroom, write_classroom_artifact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-classroom",
        dest="classroom",
        action="store_false",
        help="skip the pymdp two-agent classroom rollout (leaves classroom tokens at defaults)",
    )
    parser.set_defaults(classroom=True)
    args = parser.parse_args(argv)

    paths = artifacts.write_all(PROJECT_ROOT)
    for name, path in paths.items():
        print(f"{name}: {path}")

    if args.classroom:
        result = run_classroom(PROJECT_ROOT, ClassroomConfig())
        path = write_classroom_artifact(PROJECT_ROOT, result)
        print(f"classroom.json: {path}")
        print(f"classroom mean reverse-KL (distillation signal): {result.mean_reverse_kl:.4f} nats")
        stats_path = artifacts.write_statistics_artifact(
            PROJECT_ROOT,
            result.teacher_belief_entropies,
            result.student_belief_entropies,
        )
        print(f"statistics_demo.json: {stats_path} (from measured classroom entropies)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
