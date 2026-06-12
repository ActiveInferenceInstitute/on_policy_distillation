"""Focused tests for the artifact refresh orchestrator."""

from __future__ import annotations

from pathlib import Path

import pytest

from orchestration import artifact_pipeline
from orchestration.artifact_pipeline import hydrate_manuscript_fixed_point


def test_hydrate_manuscript_fixed_point_clears_stale_figure_source_map(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from manuscript import hydrate, variables
    from manuscript import sheaf
    from manuscript.sheaf import semantic
    import roadmap_tracks

    state = {"audit_writes": 0, "semantic_writes": 0, "sheaf_writes": 0}

    def fake_compose(root: Path) -> None:
        (root / "manuscript").mkdir(parents=True, exist_ok=True)

    def fake_generate(root: Path, *, require_analysis_outputs: bool) -> dict[str, object]:
        assert require_analysis_outputs is False
        return {"pipeline_track_count": 1}

    def fake_resolve(root: Path, data: dict[str, object]) -> Path:
        out = root / "output" / "manuscript"
        out.mkdir(parents=True, exist_ok=True)
        return out

    def fake_staleness(root: Path) -> Path:
        path = root / "output" / "reports" / "manuscript_staleness_report.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
        return path

    def fake_audit(root: Path) -> dict[str, Path]:
        state["audit_writes"] += 1
        path = root / "output" / "data" / "figure_source_map.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
        return {"figure_source_map": path}

    def fake_sheaf_tracks(root: Path, **_: object) -> dict[str, Path]:
        state["sheaf_writes"] += 1
        path = root / "output" / "data" / "sheaf_gluing_certificate.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
        return {"semantic": path}

    def fake_semantic(root: Path, **_: object) -> dict[str, Path]:
        state["semantic_writes"] += 1
        path = root / "output" / "data" / "validation_dependency_graph.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
        return {"dependency_graph": path}

    def validate_audit(root: Path) -> list[str]:
        if state["audit_writes"] < 2 or state["semantic_writes"] < 1:
            return ["figure_source_map stale"]
        return []

    monkeypatch.setattr(sheaf, "compose_all_sections", fake_compose)
    monkeypatch.setattr(variables, "generate_variables", fake_generate)
    monkeypatch.setattr(hydrate, "write_resolved_manuscript", fake_resolve)
    monkeypatch.setattr(roadmap_tracks, "write_manuscript_staleness_report", fake_staleness)
    monkeypatch.setattr(roadmap_tracks, "write_integration_audit_artifacts", fake_audit)
    monkeypatch.setattr(roadmap_tracks, "write_sheaf_track_artifacts", fake_sheaf_tracks)
    monkeypatch.setattr(semantic, "write_semantic_gluing_outputs", fake_semantic)
    import roadmap_tracks.sheaf_tracks as sheaf_tracks

    monkeypatch.setattr(sheaf_tracks, "build_artifact_provenance", lambda root: {"schema": "test"})
    monkeypatch.setattr(roadmap_tracks, "validate_integration_audit_artifacts", validate_audit)
    monkeypatch.setattr(roadmap_tracks, "validate_sheaf_track_artifacts", lambda root: [])
    monkeypatch.setattr(semantic, "validate_semantic_gluing", lambda root: [])

    paths = hydrate_manuscript_fixed_point(tmp_path, require_analysis_outputs=False, max_passes=2)

    assert state == {"audit_writes": 2, "semantic_writes": 2, "sheaf_writes": 2}
    assert paths["variables"] == tmp_path / "output" / "data" / "manuscript_variables.json"
    assert paths["resolved_manuscript"] == tmp_path / "output" / "manuscript"
    assert paths["figure_source_map"] == tmp_path / "output" / "data" / "figure_source_map.json"


def test_hydrate_manuscript_fixed_point_fails_closed_when_still_stale(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from manuscript import hydrate, variables
    from manuscript import sheaf
    from manuscript.sheaf import semantic
    import roadmap_tracks

    monkeypatch.setattr(sheaf, "compose_all_sections", lambda root: None)
    monkeypatch.setattr(
        variables,
        "generate_variables",
        lambda root, *, require_analysis_outputs: {"pipeline_track_count": 1},
    )
    monkeypatch.setattr(hydrate, "write_resolved_manuscript", lambda root, data: root / "output" / "manuscript")
    monkeypatch.setattr(
        roadmap_tracks,
        "write_manuscript_staleness_report",
        lambda root: root / "output" / "reports" / "manuscript_staleness_report.json",
    )
    monkeypatch.setattr(roadmap_tracks, "write_integration_audit_artifacts", lambda root: {})
    monkeypatch.setattr(roadmap_tracks, "write_sheaf_track_artifacts", lambda root, **_: {})
    monkeypatch.setattr(semantic, "write_semantic_gluing_outputs", lambda root, **_: {})
    import roadmap_tracks.sheaf_tracks as sheaf_tracks

    monkeypatch.setattr(sheaf_tracks, "build_artifact_provenance", lambda root: {"schema": "test"})
    monkeypatch.setattr(
        roadmap_tracks,
        "validate_integration_audit_artifacts",
        lambda root: ["figure_source_map stale"],
    )
    monkeypatch.setattr(roadmap_tracks, "validate_sheaf_track_artifacts", lambda root: [])
    monkeypatch.setattr(semantic, "validate_semantic_gluing", lambda root: [])

    with pytest.raises(RuntimeError, match="artifact fixed point did not converge"):
        hydrate_manuscript_fixed_point(tmp_path, require_analysis_outputs=False, max_passes=1)


def test_refresh_promoted_track_artifacts_runs_canonical_order(monkeypatch, tmp_path: Path) -> None:
    import roadmap_tracks
    import roadmap_tracks.supplemental as supplemental
    import validation_spine

    calls: list[str] = []

    def writer(name: str):
        def _write(root: Path) -> dict[str, Path]:
            calls.append(name)
            path = root / "output" / "data" / f"{name}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n", encoding="utf-8")
            return {name: path}

        return _write

    monkeypatch.setattr(validation_spine, "write_validation_spine_artifacts", writer("validation"))
    monkeypatch.setattr(roadmap_tracks, "write_toy_sweep_artifacts", writer("toy"))
    monkeypatch.setattr(roadmap_tracks, "write_formal_interop_artifacts", writer("formal"))
    monkeypatch.setattr(roadmap_tracks, "write_integration_audit_artifacts", writer("audit"))
    monkeypatch.setattr(supplemental, "write_supplemental_artifacts", writer("supplemental"))
    monkeypatch.setattr(roadmap_tracks, "write_sheaf_track_artifacts", writer("sheaf"))

    paths = artifact_pipeline.refresh_promoted_track_artifacts(tmp_path)

    assert calls == ["validation", "toy", "formal", "audit", "supplemental", "sheaf"]
    assert set(paths) == set(calls)


def test_refresh_gate_artifacts_refreshes_figures_after_fixed_point(monkeypatch, tmp_path: Path) -> None:
    import roadmap_tracks
    from visualizations import figures

    calls: list[str] = []

    def phase(name: str):
        def _run(root: Path, **kwargs: object) -> dict[str, Path]:
            calls.append(name)
            return {name: root / f"{name}.json"}

        return _run

    figure_path = tmp_path / "output" / "figures" / "semantic_gluing_graph.png"
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    figure_path.write_text("png placeholder\n", encoding="utf-8")

    monkeypatch.setattr(artifact_pipeline, "refresh_analysis_artifacts", phase("analysis"))
    monkeypatch.setattr(artifact_pipeline, "refresh_promoted_track_artifacts", phase("promoted"))
    monkeypatch.setattr(artifact_pipeline, "hydrate_manuscript_fixed_point", phase("fixed_point"))
    monkeypatch.setattr(figures, "generate_all_figures", lambda root: [figure_path])
    monkeypatch.setattr(roadmap_tracks, "write_integration_audit_artifacts", phase("audit"))

    paths = artifact_pipeline.refresh_gate_artifacts(tmp_path, require_analysis_outputs=False)

    assert calls == ["analysis", "promoted", "fixed_point", "audit", "fixed_point"]
    assert paths["figure:semantic_gluing_graph"] == figure_path
    assert paths["audit"] == tmp_path / "audit.json"
