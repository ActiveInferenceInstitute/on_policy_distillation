"""Semantic extension artifact tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image, ImageChops, ImageSequence


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_all_gnn_ontology_covers_si_tmaze(project_root: Path) -> None:
    from ontology.bindings import validate_all_gnn_ontology

    assert validate_all_gnn_ontology(project_root) == []

    gnn_path = project_root / "gnn" / "si_tmaze.gnn.md"
    original = gnn_path.read_text(encoding="utf-8")
    try:
        gnn_path.write_text(original.replace("q_pi=PolicyPosterior", "q_pi=HiddenState"), encoding="utf-8")
        gaps = validate_all_gnn_ontology(project_root)
        assert any("si_tmaze" in gap and "PolicyPosterior" in gap for gap in gaps)
    finally:
        gnn_path.write_text(original, encoding="utf-8")


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_all_gnn_ontology_rejects_extra_section_alias(project_root: Path) -> None:
    from ontology.bindings import validate_all_gnn_ontology

    ontology_path = project_root / "manuscript" / "sections" / "imrad" / "methods_pymdp" / "ontology.yaml"
    original = ontology_path.read_text(encoding="utf-8")
    try:
        ontology_path.write_text(original + "\nalien_alias: HiddenState\n", encoding="utf-8")
        gaps = validate_all_gnn_ontology(project_root)
    finally:
        ontology_path.write_text(original, encoding="utf-8")

    assert any("alien_alias" in gap for gap in gaps)


@pytest.mark.requires_pymdp
@pytest.mark.render_slow
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_policy_comparison_artifact_records_comparison_only_planners(project_root: Path) -> None:
    from simulation.si_runner import pymdp_available
    from simulation.si_artifacts import write_policy_comparison
    from simulation.pymdp_config import load_pymdp_config

    if not pymdp_available():
        pytest.skip("pymdp not installed")

    path = write_policy_comparison(project_root, seeds=(0,))
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert path.relative_to(project_root).as_posix() == "output/data/si_policy_comparison.json"
    assert payload["scope"] == "comparison_only"
    assert payload["canonical_planner"] == "sophisticated_inference"
    assert {row["planner"] for row in payload["runs"]} == {"sophisticated_inference", "vanilla"}
    assert {row["horizon"] for row in payload["runs"]} == {load_pymdp_config(project_root).planning_horizon}
    assert all("goal_reached" in row and "mean_belief_entropy" in row for row in payload["runs"])
    assert all(row["role"] == "validation_comparison" for row in payload["runs"])
    assert payload["summary"]["run_count"] == 2
    assert payload["summary"]["vanilla_role"] == "comparison_only"


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_graph_world_extension_writes_real_summary_and_trace(project_root: Path) -> None:
    from simulation.graph_world import write_graph_world_artifacts

    paths = write_graph_world_artifacts(project_root)
    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    trace = json.loads(paths["trace"].read_text(encoding="utf-8"))

    assert summary["status"] == "ok"
    assert summary["node_count"] >= 4
    assert summary["goal_reached"] is True
    assert trace["steps"]
    assert "not_implemented" not in json.dumps(summary)


@pytest.mark.render_slow
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_animation_extension_renders_distinct_trace_frames(project_root: Path) -> None:
    from simulation.graph_world import write_graph_world_artifacts
    from visualizations.animation import (
        validate_animation_frame_deltas,
        write_animation_frame_deltas,
        write_belief_trajectory_gif,
    )

    write_graph_world_artifacts(project_root)
    gif_path = write_belief_trajectory_gif(project_root)
    deltas_path = write_animation_frame_deltas(project_root)
    deltas = json.loads(deltas_path.read_text(encoding="utf-8"))

    with Image.open(gif_path) as image:
        frames = [frame.convert("RGB") for frame in ImageSequence.Iterator(image)]

    assert len(frames) >= 3
    assert any(ImageChops.difference(frames[0], frame).getbbox() is not None for frame in frames[1:])
    assert deltas["all_nonzero"] is True
    assert validate_animation_frame_deltas(project_root) == []


@pytest.mark.render_slow
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_animation_frame_delta_manifest_rejects_static_manifest(project_root: Path) -> None:
    from simulation.graph_world import write_graph_world_artifacts
    from visualizations.animation import (
        validate_animation_frame_deltas,
        write_animation_frame_deltas,
        write_belief_trajectory_gif,
    )

    write_graph_world_artifacts(project_root)
    write_belief_trajectory_gif(project_root)
    path = write_animation_frame_deltas(project_root)
    original = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        payload["rows"][0]["nonzero"] = False
        payload["all_nonzero"] = False
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        issues = validate_animation_frame_deltas(project_root)
    finally:
        path.write_text(original, encoding="utf-8")

    assert any("static adjacent frames" in issue or "stale" in issue for issue in issues)


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_rejects_graph_world_summary_trace_mismatch(project_root: Path) -> None:
    from gates.validation import validate_outputs
    from simulation.graph_world import write_graph_world_artifacts

    paths = write_graph_world_artifacts(project_root)
    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    original = paths["summary"].read_text(encoding="utf-8")
    try:
        summary["steps"] = 999
        paths["summary"].write_text(json.dumps(summary, indent=2), encoding="utf-8")
        checks = validate_outputs(project_root)
    finally:
        paths["summary"].write_text(original, encoding="utf-8")

    assert checks["si_graph_world_schema"] is False


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_pymdp_runtime_diagnostics_captures_known_warning_and_rejects_unexpected(
    project_root: Path,
) -> None:
    from simulation.pymdp_config import load_pymdp_config
    from simulation.pymdp_runtime import (
        construct_agent_with_diagnostics,
        validate_runtime_diagnostics,
        write_runtime_diagnostics,
    )
    from simulation.tmaze_model import build_tmaze_generative_model, spec_from_config

    cfg = load_pymdp_config(project_root)
    model = build_tmaze_generative_model(cfg)
    spec = spec_from_config(cfg)
    diagnostics_path = project_root / "output" / "reports" / "pymdp_runtime_diagnostics.json"
    original = diagnostics_path.read_text(encoding="utf-8") if diagnostics_path.is_file() else None

    def noisy_factory(**kwargs):
        import warnings
        from pymdp.agent import Agent

        warnings.warn("unexpected agent construction warning", UserWarning, stacklevel=2)
        return Agent(**kwargs)

    try:
        _, record = construct_agent_with_diagnostics(
            project_root,
            config=cfg,
            model=model,
            policy_len=spec.policy_len,
            context="negative_control",
            agent_factory=noisy_factory,
        )
        path = write_runtime_diagnostics(project_root, [record])
        payload = json.loads(path.read_text(encoding="utf-8"))

        assert payload["known_warning_count"] >= 1
        assert payload["unexpected_warning_count"] == 1
        assert any("unexpected warning" in issue for issue in validate_runtime_diagnostics(project_root))
    finally:
        if original is None:
            diagnostics_path.unlink(missing_ok=True)
        else:
            diagnostics_path.write_text(original, encoding="utf-8")


@pytest.mark.render_slow
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_policy_comparison_uses_configured_grid_and_writes_posterior_rows(project_root: Path) -> None:
    from simulation.pymdp_config import load_pymdp_config
    from simulation.si_artifacts import write_policy_comparison, write_policy_posterior_grid

    cfg = load_pymdp_config(project_root)
    path = write_policy_comparison(project_root)
    grid_path = write_policy_posterior_grid(project_root)
    payload = json.loads(path.read_text(encoding="utf-8"))
    posterior = json.loads(grid_path.read_text(encoding="utf-8"))

    assert payload["summary"]["planners"] == sorted(cfg.validation_comparison.planners)
    assert payload["summary"]["horizons"] == [cfg.planning_horizon]
    assert payload["summary"]["seeds"] == sorted(cfg.validation_comparison.seeds)
    assert payload["summary"]["run_count"] == (
        len(cfg.validation_comparison.planners) * len(cfg.validation_comparison.seeds)
    )
    assert posterior["schema"] == "template_active_inference.pymdp_policy_posterior_grid.v1"
    assert posterior["row_count"] >= 1
    assert posterior["all_available_posteriors_normalized"] is True
    assert {row["planner"] for row in posterior["rows"]} == {"sophisticated_inference", "vanilla"}


@pytest.mark.render_slow
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_rejects_unnormalized_policy_posterior(project_root: Path) -> None:
    from gates.validation import validate_outputs
    from simulation.si_artifacts import write_policy_comparison, write_policy_posterior_grid

    write_policy_comparison(project_root)
    path = write_policy_posterior_grid(project_root)
    original = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        row = next(row for row in payload["rows"] if row["posterior_available"])
        row["q_pi"] = [0.8, 0.8]
        row["q_pi_sum"] = 1.6
        row["normalized"] = False
        payload["all_available_posteriors_normalized"] = False
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root)
    finally:
        path.write_text(original, encoding="utf-8")

    assert checks["pymdp_policy_posterior_grid_schema"] is False


@pytest.mark.render_slow
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_rejects_missing_grid_cell(project_root: Path) -> None:
    from gates.validation import validate_outputs
    from simulation.si_artifacts import write_policy_comparison, write_policy_posterior_grid

    write_policy_comparison(project_root)
    path = write_policy_posterior_grid(project_root)
    # Exercise the PRODUCTION full path (validate_outputs with no `only=`), not the
    # lazy selected path — a prior fix lived only in the selected path and the
    # production gate stayed weak (cross-vendor caught the green-wash).
    baseline = validate_outputs(project_root)
    assert baseline["pymdp_policy_posterior_grid_schema"] is True
    original = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        payload["rows"] = [row for row in payload["rows"] if row["planner"] != "vanilla"]
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root)
    finally:
        path.write_text(original, encoding="utf-8")

    assert checks["pymdp_policy_posterior_grid_schema"] is False


# --- AI-ANIMATION-HASH-2: per-frame hash + duplicate-frame guard ---------------


def test_animation_frame_deltas_carries_per_frame_hash_and_metadata(project_root: Path) -> None:
    """Write-path: the builder emits a passing artifact with per-frame hash + metadata."""
    from visualizations.animation import build_animation_frame_deltas, validate_animation_frame_deltas

    payload = build_animation_frame_deltas(project_root)
    assert payload["frame_count"] >= 2
    assert payload["all_nonzero"] is True
    assert payload["all_hashes_distinct"] is True
    for frame in payload["frames"]:
        assert {"index", "width", "height", "sha256"} <= set(frame)
        assert len(frame["sha256"]) == 64
    for row in payload["rows"]:
        assert row["hashes_differ"] is True
        assert row["from_hash"] != row["to_hash"]
    # The honest live artifact passes the strengthened validator.
    assert validate_animation_frame_deltas(project_root) == []


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_rejects_duplicate_animation_frame_hash(project_root: Path) -> None:
    """NC (production path): two consecutive identical frame hashes must fail the gate."""
    from gates.validation import validate_outputs

    path = project_root / "output" / "data" / "animation_frame_deltas.json"
    baseline = validate_outputs(project_root)
    assert baseline["animation_frame_deltas_schema"] is True
    original = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        # Inject a static/duplicate adjacent frame: copy the first frame's hash
        # onto the second frame so a consecutive pair becomes identical.
        dup = payload["frames"][0]["sha256"]
        payload["frames"][1]["sha256"] = dup
        payload["rows"][0]["to_hash"] = dup
        payload["rows"][0]["hashes_differ"] = payload["rows"][0]["from_hash"] != dup
        if len(payload["rows"]) > 1:
            payload["rows"][1]["from_hash"] = dup
            payload["rows"][1]["hashes_differ"] = dup != payload["rows"][1]["to_hash"]
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root)
    finally:
        path.write_text(original, encoding="utf-8")

    assert checks["animation_frame_deltas_schema"] is False


# --- AI-PYMDP-RUNTIME-3: categorized inference/fallback rows --------------------


def test_runtime_diagnostics_emit_categorized_inference_rows(project_root: Path) -> None:
    """Write-path: build_runtime_diagnostics fans records into explained categorized rows."""
    import json as _json

    from simulation.pymdp_runtime import (
        RUNTIME_ROW_CATEGORIES,
        _runtime_rows_explained,
        build_runtime_diagnostics,
    )

    live = project_root / "output" / "reports" / "pymdp_runtime_diagnostics.json"
    records = _json.loads(live.read_text(encoding="utf-8")).get("records") or []
    payload = build_runtime_diagnostics(records)
    categories = {row["category"] for row in payload["rows"]}
    assert {"construction", "inference", "backend"} <= categories
    assert categories <= RUNTIME_ROW_CATEGORIES
    for row in payload["rows"]:
        if row["category"] in {"inference", "fallback"}:
            assert row["reason"].strip()
    assert payload["all_rows_explained"] is True
    assert _runtime_rows_explained(payload["rows"]) is True

    # A fabricated backend error fans out a reasoned fallback row.
    faulted = [dict(records[0], backend_flags={"jax_backend_error": "RuntimeError"})] if records else []
    fb = build_runtime_diagnostics(faulted)
    if faulted:
        fallback_rows = [r for r in fb["rows"] if r["category"] == "fallback"]
        assert fallback_rows and all(r["reason"].strip() for r in fallback_rows)


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_rejects_unexplained_inference_row(project_root: Path) -> None:
    """NC (production path): an inference row with a blank reason must fail the gate."""
    from gates.validation import validate_outputs

    path = project_root / "output" / "reports" / "pymdp_runtime_diagnostics.json"
    baseline = validate_outputs(project_root)
    assert baseline["pymdp_runtime_diagnostics_schema"] is True
    original = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        inference_row = next(row for row in payload["rows"] if row["category"] == "inference")
        inference_row["reason"] = ""
        # Leave the stored aggregate True to prove the gate re-derives from rows.
        payload["all_rows_explained"] = True
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root)
    finally:
        path.write_text(original, encoding="utf-8")

    assert checks["pymdp_runtime_diagnostics_schema"] is False


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_rejects_unknown_runtime_category(project_root: Path) -> None:
    """NC (production path): an unknown diagnostic category must fail the gate."""
    from gates.validation import validate_outputs

    path = project_root / "output" / "reports" / "pymdp_runtime_diagnostics.json"
    original = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        payload["rows"][0]["category"] = "totally_unknown_category"
        payload["all_rows_explained"] = True
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root)
    finally:
        path.write_text(original, encoding="utf-8")

    assert checks["pymdp_runtime_diagnostics_schema"] is False


# --- AI-GNN-SHAPE-3: per-variable round-trip check -----------------------------


def test_gnn_lint_report_carries_round_trip_field(project_root: Path) -> None:
    """Write-path: build_gnn_lint_report emits a passing per-variable round-trip field."""
    from roadmap_tracks.formal_interop import (
        build_gnn_lint_report,
        roundtrip_payload_lossless,
        validate_formal_interop_artifacts,
    )

    payload = build_gnn_lint_report(project_root)
    assert payload["rows"]
    assert payload["all_round_trip_ok"] is True
    for row in payload["rows"]:
        assert row["round_trip_ok"] is True
    assert validate_formal_interop_artifacts(project_root) == []

    # The round-trip field is a real parse->write->parse check: empty dims break it.
    broken = {
        "section": "S",
        "version": "1",
        "name": "N",
        "variables": {"x": {"dims": [], "dtype": "float", "ontology": "HiddenState"}},
        "connections": [],
    }
    assert roundtrip_payload_lossless(broken) is False


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_rejects_gnn_round_trip_break(project_root: Path) -> None:
    """NC (production path): a variable that fails the round-trip must fail the gate."""
    from gates.validation import validate_outputs

    path = project_root / "output" / "reports" / "gnn_lint_report.json"
    baseline = validate_outputs(project_root)
    assert baseline["gnn_lint_schema"] is True
    original = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        # Break a single variable's round-trip while leaving the stored aggregate
        # True — the gate must re-derive the per-row contract.
        payload["rows"][0]["round_trip_ok"] = False
        payload["all_round_trip_ok"] = True
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root)
    finally:
        path.write_text(original, encoding="utf-8")

    assert checks["gnn_lint_schema"] is False
