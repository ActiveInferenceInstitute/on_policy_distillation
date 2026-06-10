#!/usr/bin/env python3
"""Write manuscript_variables.json and resolve {{token}} placeholders for PDF."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from orchestration.artifact_pipeline import hydrate_manuscript_fixed_point


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-draft",
        action="store_true",
        help="Allow missing analysis outputs (non-pipeline draft mode)",
    )
    args = parser.parse_args(argv)

    paths = hydrate_manuscript_fixed_point(
        PROJECT_ROOT,
        require_analysis_outputs=not args.allow_draft,
    )
    for key in (
        "variables",
        "certificate",
        "crosswalk",
        "dependency_graph",
        "resolved_manuscript",
        "manuscript_staleness",
    ):
        path = paths.get(key)
        if path is not None:
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
