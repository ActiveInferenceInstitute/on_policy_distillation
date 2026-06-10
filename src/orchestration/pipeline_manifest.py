"""Pipeline manifest for template_active_inference."""

from __future__ import annotations

from pathlib import Path

from artifact_contracts import DEFAULT_ANALYSIS_SCRIPTS, ScriptStep


def analysis_scripts(project_root: Path | None = None) -> list[Path]:
    root = (project_root or Path(".")).resolve()
    scripts_dir = root / "scripts"
    return [scripts_dir / step.script for step in DEFAULT_ANALYSIS_SCRIPTS if (scripts_dir / step.script).exists()]


__all__ = ["DEFAULT_ANALYSIS_SCRIPTS", "ScriptStep", "analysis_scripts"]
