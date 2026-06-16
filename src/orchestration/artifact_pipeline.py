"""Deterministic artifact refresh orchestration.

This module owns the fixed-point sequence that makes generated analysis,
manuscript hydration, semantic certificates, and promoted-track audit artifacts
agree. Scripts and tests should call this module instead of copying the sequence.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def refresh_analysis_artifacts(project_root: Path) -> dict[str, Path]:
    """Refresh deterministic analysis, simulation, first-principles, and figure artifacts."""
    root = project_root.resolve()
    paths: dict[str, Path] = {}

    from analysis import run_analysis, write_analysis_statistics
    from firstprinciples import artifacts as firstprinciples_artifacts
    from firstprinciples.classroom import ClassroomConfig, run_classroom, write_classroom_artifact
    from orchestration.coverage_pipeline import ensure_coverage_artifacts
    from simulation.graph_world import write_graph_world_artifacts
    from simulation.si_artifacts import write_policy_comparison, write_policy_posterior_grid
    from simulation.si_runner import pymdp_available, run_and_persist
    from visualizations.animation import write_animation_frame_deltas, write_belief_trajectory_gif
    from visualizations.figures import generate_all_figures

    paths.update(run_analysis(root))
    paths.update(firstprinciples_artifacts.write_all(root))
    if not pymdp_available():
        raise RuntimeError("pymdp is required to refresh gate artifacts")
    run_and_persist(root)
    write_policy_comparison(root)
    write_policy_posterior_grid(root)
    classroom = run_classroom(root, ClassroomConfig())
    paths["firstprinciples_classroom"] = write_classroom_artifact(root, classroom)
    paths.update(write_graph_world_artifacts(root))
    paths["analysis_statistics"] = write_analysis_statistics(root)
    coverage_json, coverage_png, coverage_page = ensure_coverage_artifacts(
        root,
        write_page=True,
        render_heatmap=True,
        force=True,
    )
    paths["coverage_json"] = coverage_json
    if coverage_png is not None:
        paths["coverage_heatmap"] = coverage_png
    if coverage_page is not None:
        paths["coverage_page"] = coverage_page
    for figure_path in generate_all_figures(root):
        paths[f"figure:{figure_path.stem}"] = figure_path
    paths["belief_trajectory_gif"] = write_belief_trajectory_gif(root)
    paths["animation_frame_deltas"] = write_animation_frame_deltas(root)
    return paths


def refresh_promoted_track_artifacts(project_root: Path) -> dict[str, Path]:
    """Refresh validation-spine, roadmap, integration-audit, and canonical sheaf artifacts."""
    root = project_root.resolve()
    paths: dict[str, Path] = {}

    from roadmap_tracks import (
        write_formal_interop_artifacts,
        write_integration_audit_artifacts,
        write_sheaf_track_artifacts,
        write_toy_sweep_artifacts,
    )
    from roadmap_tracks.supplemental import write_supplemental_artifacts
    from validation_spine import write_validation_spine_artifacts

    paths.update(write_validation_spine_artifacts(root))
    paths.update(write_toy_sweep_artifacts(root))
    paths.update(write_formal_interop_artifacts(root))
    paths.update(write_integration_audit_artifacts(root))
    paths.update(write_supplemental_artifacts(root))
    paths.update(write_sheaf_track_artifacts(root))
    return paths


def _write_variables(project_root: Path, *, require_analysis_outputs: bool) -> tuple[dict[str, Any], Path, Path]:
    from manuscript.hydrate import write_resolved_manuscript
    from manuscript.variables import generate_variables

    root = project_root.resolve()
    out = root / "output" / "data" / "manuscript_variables.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    variables = generate_variables(root, require_analysis_outputs=require_analysis_outputs)
    out.write_text(json.dumps(variables, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    resolved_dir = write_resolved_manuscript(root, variables)
    return variables, out, resolved_dir


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_content_signature(root: Path, paths: dict[str, Path]) -> tuple[tuple[str, str], ...]:
    """Return content hashes for the files touched in one fixed-point pass."""
    rows: list[tuple[str, str]] = []
    for path in sorted({path.resolve() for path in paths.values()}, key=str):
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            rel = str(path)
        if path.is_file():
            rows.append((rel, _sha256_file(path)))
        elif not path.exists():
            rows.append((rel, "<missing>"))
    return tuple(rows)


def hydrate_manuscript_fixed_point(
    project_root: Path,
    *,
    require_analysis_outputs: bool = True,
    max_passes: int = 4,
) -> dict[str, Path]:
    """Compose, hydrate, and regenerate semantic artifacts until validators converge."""
    root = project_root.resolve()
    paths: dict[str, Path] = {}
    remaining_issues: dict[str, list[str]] = {}
    previous_issues: dict[str, list[str]] | None = None
    previous_signature: tuple[tuple[str, str], ...] | None = None

    from manuscript.sheaf import compose_all_sections
    from manuscript.sheaf.semantic import validate_semantic_gluing, write_semantic_gluing_outputs
    from roadmap_tracks import (
        validate_integration_audit_artifacts,
        validate_sheaf_track_artifacts,
        write_integration_audit_artifacts,
        write_manuscript_staleness_report,
        write_sheaf_track_artifacts,
    )

    for pass_index in range(max_passes):
        pass_paths: dict[str, Path] = {}
        compose_all_sections(root)
        _, variables_path, resolved_dir = _write_variables(root, require_analysis_outputs=require_analysis_outputs)
        pass_paths["variables"] = variables_path
        pass_paths["resolved_manuscript"] = resolved_dir
        pass_paths["manuscript_staleness"] = write_manuscript_staleness_report(root)
        pass_paths.update(write_integration_audit_artifacts(root))
        pass_paths.update(write_sheaf_track_artifacts(root, refresh_hydration=False))
        pass_paths.update(write_semantic_gluing_outputs(root, refresh_hydration=False))
        pass_paths.update(write_integration_audit_artifacts(root))
        _, variables_path, resolved_dir = _write_variables(root, require_analysis_outputs=require_analysis_outputs)
        pass_paths["variables"] = variables_path
        pass_paths["resolved_manuscript"] = resolved_dir
        pass_paths["manuscript_staleness"] = write_manuscript_staleness_report(root)
        pass_paths.update(write_semantic_gluing_outputs(root, refresh_hydration=False))
        from roadmap_tracks.sheaf_tracks import CANONICAL_ARTIFACTS, _write_json, build_artifact_provenance

        pass_paths["provenance"] = _write_json(
            root / CANONICAL_ARTIFACTS["provenance"],
            build_artifact_provenance(root),
        )
        paths.update(pass_paths)

        remaining_issues = {
            "integration_audit": validate_integration_audit_artifacts(root),
            "sheaf_tracks": validate_sheaf_track_artifacts(root),
            "semantic_gluing": validate_semantic_gluing(root),
        }
        if not any(remaining_issues.values()):
            break
        signature = _artifact_content_signature(root, pass_paths)
        if signature == previous_signature and remaining_issues == previous_issues:
            details = "; ".join(
                f"{name}: {', '.join(issues)}" for name, issues in remaining_issues.items() if issues
            )
            raise RuntimeError(
                f"artifact fixed point stalled after {pass_index + 1} passes with unchanged artifact hashes: {details}"
            )
        previous_signature = signature
        previous_issues = {name: list(issues) for name, issues in remaining_issues.items()}
    else:
        details = "; ".join(
            f"{name}: {', '.join(issues)}" for name, issues in remaining_issues.items() if issues
        )
        raise RuntimeError(f"artifact fixed point did not converge after {max_passes} passes: {details}")
    return paths


def refresh_gate_artifacts(
    project_root: Path,
    *,
    require_analysis_outputs: bool = True,
) -> dict[str, Path]:
    """Refresh the full artifact surface required by output and manuscript gates."""
    root = project_root.resolve()
    paths: dict[str, Path] = {}
    paths.update(refresh_analysis_artifacts(root))
    paths.update(refresh_promoted_track_artifacts(root))
    paths.update(hydrate_manuscript_fixed_point(root, require_analysis_outputs=require_analysis_outputs))
    # Figures consume semantic and promoted-track artifacts, so refresh audits once
    # more after the fixed point has settled.
    from roadmap_tracks import write_integration_audit_artifacts
    from visualizations.figures import generate_all_figures

    for figure_path in generate_all_figures(root):
        paths[f"figure:{figure_path.stem}"] = figure_path
    paths.update(write_integration_audit_artifacts(root))
    paths.update(hydrate_manuscript_fixed_point(root, require_analysis_outputs=require_analysis_outputs))
    return paths


__all__ = [
    "hydrate_manuscript_fixed_point",
    "refresh_analysis_artifacts",
    "refresh_gate_artifacts",
    "refresh_promoted_track_artifacts",
]
