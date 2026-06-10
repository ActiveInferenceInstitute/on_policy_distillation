"""Negative controls for the copied-output release parity check.

AI-RELEASE-PARITY-1: before Run-6 the parity builder reclassified an existing
root copy whose hash did not match as "deferred", so copied-output drift could
never fail (`matches_when_copied` was always true). These tests pin the honest
semantics on a synthetic tree: drift fails, pre-copy defers, parity passes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from roadmap_tracks.sheaf_tracks_support import _copied_parity, _root_output_dir


def _make_template_root(tmp_path: Path) -> tuple[Path, Path]:
    """Build a fake template root (run.sh + projects/) with one project inside."""
    template_root = tmp_path / "template"
    (template_root / "projects").mkdir(parents=True)
    (template_root / "run.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    project_root = template_root / "projects" / "proj"
    (project_root / "output" / "data").mkdir(parents=True)
    return template_root, project_root


def test_root_output_dir_resolves_inside_template_root(tmp_path: Path) -> None:
    template_root, project_root = _make_template_root(tmp_path)
    assert _root_output_dir(project_root) == template_root / "output" / "templates" / "proj"


def test_copied_output_drift_fails_parity(tmp_path: Path) -> None:
    """An existing root copy with different bytes is drift, never 'deferred'."""
    template_root, project_root = _make_template_root(tmp_path)
    rel = "output/data/x.json"
    (project_root / rel).write_text('{"v": 1}', encoding="utf-8")
    copied = template_root / "output" / "templates" / "proj" / "data" / "x.json"
    copied.parent.mkdir(parents=True)
    copied.write_text('{"v": 2}', encoding="utf-8")

    parity = _copied_parity(project_root, [rel])
    row = parity["rows"][0]
    assert row["copied_exists"] is True
    assert row["hash_matches"] is False
    assert row["comparison_deferred_until_copy"] is False
    assert row["matches_when_copied"] is False
    assert parity["all_copied_outputs_match"] is False
    assert parity["all_copied_outputs_match_or_deferred"] is False


def test_matching_copied_output_passes_parity(tmp_path: Path) -> None:
    template_root, project_root = _make_template_root(tmp_path)
    rel = "output/data/x.json"
    (project_root / rel).write_text('{"v": 1}', encoding="utf-8")
    copied = template_root / "output" / "templates" / "proj" / "data" / "x.json"
    copied.parent.mkdir(parents=True)
    copied.write_text('{"v": 1}', encoding="utf-8")

    parity = _copied_parity(project_root, [rel])
    row = parity["rows"][0]
    assert row["hash_matches"] is True
    assert row["matches_when_copied"] is True
    assert parity["all_copied_outputs_match_or_deferred"] is True


def test_missing_copy_is_deferred_not_failed(tmp_path: Path) -> None:
    """Pre-copy stage (no root copy yet) defers the comparison honestly."""
    _, project_root = _make_template_root(tmp_path)
    rel = "output/data/x.json"
    (project_root / rel).write_text('{"v": 1}', encoding="utf-8")

    parity = _copied_parity(project_root, [rel])
    row = parity["rows"][0]
    assert row["copied_exists"] is False
    assert row["comparison_deferred_until_copy"] is True
    assert row["matches_when_copied"] is True
    assert parity["all_copied_outputs_match_or_deferred"] is True
    assert parity["pre_copy_stage"] is True


def test_missing_render_source_with_copy_absent_is_deferred(tmp_path: Path) -> None:
    """A render-stage deliverable (pdf/web) with no source and no copy defers."""
    _, project_root = _make_template_root(tmp_path)
    parity = _copied_parity(project_root, ["output/pdf/paper.pdf"])
    row = parity["rows"][0]
    assert row["source_exists"] is False
    assert row["comparison_deferred_until_copy"] is True
    assert row["matches_when_copied"] is True


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_gate_rederives_parity_from_nested_rows(tmp_path: Path) -> None:
    """Lying stored parity flag over a drifted nested row fails the REAL bundle gate at read time.

    Drives `validate_outputs(only={"release_bundle_manifest_schema"})` against a
    mutate-then-restore of the live artifact — not a re-statement of the gate
    expression (that would be the tautology class this project forbids).
    """
    import json

    import pytest as _pytest

    from gates.output_checks import validate_outputs

    project_root = Path(__file__).resolve().parent.parent
    path = project_root / "output" / "reports" / "release_bundle_manifest.json"
    if not path.is_file():
        _pytest.skip("release_bundle_manifest.json not generated yet (run the full chain)")
    backup = tmp_path / "release_bundle_manifest.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    parity_rows = (payload.get("copied_output_parity") or {}).get("rows") or []
    assert parity_rows, "live manifest should carry parity rows"
    # Drift one nested row while leaving every stored aggregate flag true.
    parity_rows[0]["matches_when_copied"] = False
    try:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"release_bundle_manifest_schema"})
        assert checks["release_bundle_manifest_schema"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
    checks = validate_outputs(project_root, only={"release_bundle_manifest_schema"})
    assert checks["release_bundle_manifest_schema"] is True
