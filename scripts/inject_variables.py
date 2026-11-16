#!/usr/bin/env python3
"""Forward to z_generate_manuscript_variables (single hydration entry point)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from orchestration.artifact_lock import ARTIFACT_LEASE_ENV, ArtifactLeaseError, artifact_lease


def main(argv: list[str] | None = None) -> int:
    script = Path(__file__).resolve().parent / "z_generate_manuscript_variables.py"
    try:
        with artifact_lease(PROJECT_ROOT, inherited=os.environ.get(ARTIFACT_LEASE_ENV)) as lease:
            handoff = lease.handoff()
            result = subprocess.run(
                [sys.executable, str(script), *(argv or [])],
                env=handoff.env,
                pass_fds=handoff.pass_fds,
                check=False,
            )
    except ArtifactLeaseError as exc:
        print(f"artifact custody: {exc}", file=sys.stderr)
        return 1
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
