"""Documentation contract checks for reproducibility-facing references."""

from __future__ import annotations

from pathlib import Path

from visualizations.figure_registry import load_figure_registry


def test_rendering_reproducibility_reference_is_signposted(project_root: Path) -> None:
    docs_readme = (project_root / "docs" / "README.md").read_text(encoding="utf-8")
    project_readme = (project_root / "README.md").read_text(encoding="utf-8")
    reference = project_root / "docs" / "reference" / "rendering-reproducibility.md"

    assert "rendering-reproducibility.md" in docs_readme
    assert "rendering-reproducibility.md" in project_readme
    assert reference.is_file()

    text = reference.read_text(encoding="utf-8")
    for phrase in (
        "single hydration boundary",
        "Generated artifacts",
        "Authored surfaces",
        "Root output parity",
        "Figure rendering contract",
    ):
        assert phrase in text


def test_public_docs_list_every_registered_current_figure(project_root: Path) -> None:
    registry = load_figure_registry(project_root)
    surfaces = {
        "README.md": (project_root / "README.md").read_text(encoding="utf-8"),
        "AGENTS.md": (project_root / "AGENTS.md").read_text(encoding="utf-8"),
        "manuscript/SYNTAX.md": (project_root / "manuscript" / "SYNTAX.md").read_text(encoding="utf-8"),
    }
    for surface, text in surfaces.items():
        for figure_id in registry:
            assert figure_id in text, f"{surface} does not mention registered figure {figure_id}"


def test_public_docs_pin_canonical_si_artifacts_without_legacy_modes(project_root: Path) -> None:
    surfaces = [
        (project_root / "README.md").read_text(encoding="utf-8"),
        (project_root / "AGENTS.md").read_text(encoding="utf-8"),
        (project_root / "docs" / "AGENTS.md").read_text(encoding="utf-8"),
    ]
    combined = "\n".join(surfaces)
    for phrase in (
        "full_tmaze_sophisticated_inference",
        "sophisticated_inference",
        "si_tmaze_summary.json",
        "si_tmaze_model_matrices.json",
        "pymdp_policy_posterior_grid.json",
        "pymdp_runtime_diagnostics.json",
        "vanilla planning is comparison-only",
    ):
        assert phrase in combined
    for stale in ("--mode", "state_inference", "policy_inference", "pymdp_mode"):
        assert stale not in combined
