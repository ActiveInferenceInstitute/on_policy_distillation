"""Real source staging for cold artifact API and CLI regressions."""

from __future__ import annotations

import shutil
from pathlib import Path


def stage_source_project(source_root: Path, destination: Path) -> Path:
    """Copy authored project inputs without repository or runtime output state."""
    shutil.copytree(
        source_root,
        destination,
        ignore=shutil.ignore_patterns(
            ".git", ".venv", "output", "__pycache__", ".pytest_cache",
            ".mypy_cache", ".ruff_cache", ".coverage*", "htmlcov",
        ),
    )
    return destination
