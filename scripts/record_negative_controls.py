"""Explicitly record registered per-case pytest evidence; never run during generation."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from orchestration.artifact_lock import ARTIFACT_LEASE_ENV  # noqa: E402
from roadmap_tracks.negative_controls import CASES, record_negative_controls  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", choices=[case.id for case in CASES], dest="cases")
    args = parser.parse_args()
    paths = record_negative_controls(
        ROOT,
        case_ids=tuple(args.cases) if args.cases is not None else None,
        inherited=os.environ.get(ARTIFACT_LEASE_ENV),
    )
    for path in paths.values():
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
