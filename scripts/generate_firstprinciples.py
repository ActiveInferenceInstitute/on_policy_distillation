#!/usr/bin/env python3
"""Emit first-principles OPD<->active-inference artifacts (thin orchestrator).

Consumes the current SI trace/summary and analytical observable sweep. The shared
producer writes deterministic witnesses, the SI bridge, measured classroom
statistics, the privilege sweep, and the final precision ledger. Pass
``--no-classroom`` to skip classroom rollouts and remove their stale derived
artifacts rather than retain measurements from a previous invocation.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from firstprinciples import artifacts
from orchestration.artifact_lock import ARTIFACT_LEASE_ENV, ArtifactLeaseError, artifact_lease


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-classroom",
        dest="classroom",
        action="store_false",
        help="skip classroom rollouts and remove stale classroom/statistics/privilege artifacts",
    )
    parser.set_defaults(classroom=True)
    args = parser.parse_args(argv)

    try:
        with artifact_lease(PROJECT_ROOT, inherited=os.environ.get(ARTIFACT_LEASE_ENV)):
            paths = artifacts.write_complete(PROJECT_ROOT, classroom=args.classroom)
    except ArtifactLeaseError as exc:
        print(f"artifact custody: {exc}", file=sys.stderr)
        return 1
    for name, path in paths.items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
