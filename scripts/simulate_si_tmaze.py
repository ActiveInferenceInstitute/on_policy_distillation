#!/usr/bin/env python3
"""Run pymdp sophisticated-inference T-maze simulation."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from orchestration.artifact_lock import ARTIFACT_LEASE_ENV, ArtifactLeaseError, artifact_lease
from simulation.pymdp_config import apply_pymdp_overrides, load_pymdp_config
from simulation.si_artifacts import write_policy_comparison
from simulation.si_runner import pymdp_available, run_and_persist


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the canonical pymdp full-TMaze sophisticated-inference rollout.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to pymdp.yaml (default: project-root pymdp.yaml)",
    )
    parser.add_argument("--steps", type=int, default=None, help="Rollout length (overrides config)")
    parser.add_argument(
        "--horizon",
        type=int,
        default=None,
        help="Agent policy_len / planning horizon (overrides config)",
    )
    parser.add_argument("--seed", type=int, default=None, help="Random seed (overrides config)")
    parser.add_argument(
        "--comparison",
        dest="comparison",
        action="store_true",
        default=None,
        help="Write SI-vs-vanilla validation-comparison artifacts.",
    )
    parser.add_argument(
        "--no-comparison",
        dest="comparison",
        action="store_false",
        help="Skip validation-comparison artifacts.",
    )
    parser.add_argument(
        "--log-disabled",
        action="store_true",
        help="Disable JSONL logging even when enabled in config",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        with artifact_lease(PROJECT_ROOT, inherited=os.environ.get(ARTIFACT_LEASE_ENV)):
            if not pymdp_available():
                print(
                    "pymdp not installed; simulate_si_tmaze.py requires inferactively-pymdp "
                    "(see pyproject.toml). Install deps with `uv sync` in the project root.",
                    file=sys.stderr,
                )
                return 1

            config = load_pymdp_config(PROJECT_ROOT, config_path=args.config)
            config = apply_pymdp_overrides(
                config,
                steps=args.steps,
                horizon=args.horizon,
                seed=args.seed,
                logging_enabled=False if args.log_disabled else None,
                comparison_enabled=args.comparison,
            )
            result = run_and_persist(PROJECT_ROOT, config=config)
            for name, path in result["paths"].items():
                print(f"{name}: {path}")
            if config.validation_comparison.enabled:
                comparison_path = write_policy_comparison(PROJECT_ROOT, config=config)
                print(f"policy_comparison: {comparison_path}")
                print(f"policy_posterior_grid: {comparison_path.with_name('pymdp_policy_posterior_grid.json')}")
            log_path = PROJECT_ROOT / config.logging.path
            if config.logging.enabled:
                print(f"log: {log_path}")
    except ArtifactLeaseError as exc:
        print(f"cannot run SI artifacts without artifact custody: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
