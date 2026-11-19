"""Real-file negative controls for canonical, occurrence-bound hydration."""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest

from manuscript.hydrate import write_resolved_manuscript
from manuscript.variables import generate_variables
from roadmap_tracks.integration_audit import (
    build_manuscript_staleness_report,
    validate_integration_audit_artifacts,
    validate_manuscript_staleness_report,
    write_manuscript_staleness_report,
)
from roadmap_tracks.integration_audit_builders import TOKEN_MATCH_RE


def _project(tmp_path: Path, text: str) -> Path:
    source = Path(__file__).resolve().parents[1]
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    shutil.copytree(source / "manuscript" / "sheaf", manuscript / "sheaf")
    for rel in ("tracks.yaml", "pymdp.yaml", "figures.yaml", "manuscript/config.yaml"):
        shutil.copyfile(source / rel, tmp_path / rel)
    (manuscript / "00_abstract.md").write_text(text, encoding="utf-8")
    return tmp_path


def _hydrate(root: Path) -> dict:
    variables = generate_variables(root, require_analysis_outputs=False)
    write_resolved_manuscript(root, variables)
    return build_manuscript_staleness_report(root)


def _replace_occurrence(root: Path, row: dict, replacement: str) -> None:
    path = root / row["resolved_path"]
    text = path.read_text(encoding="utf-8")
    path.write_text(text[: row["resolved_start"]] + replacement + text[row["resolved_end"] :], encoding="utf-8")


def test_second_occurrence_cannot_borrow_first_correct_value(tmp_path: Path) -> None:
    root = _project(tmp_path, "Left {{pipeline_track_count}}; right {{pipeline_track_count}}.\n")
    original = _hydrate(root)
    assert original["all_fresh"] is True
    assert original["row_count"] == 2
    assert [row["occurrence"] for row in original["rows"]] == [1, 2]
    assert len({row["occurrence_id"] for row in original["rows"]}) == 2
    _replace_occurrence(root, original["rows"][1], "!" * len(original["rows"][1]["expected"]))

    live = build_manuscript_staleness_report(root)
    assert live["rows"][0]["fresh"] is True
    assert live["rows"][1]["fresh"] is False
    assert live["all_fresh"] is False
    assert live["sections"][0]["canonical_hydration_matches"] is False


def test_expected_value_in_unrelated_prose_cannot_mask_corruption(tmp_path: Path) -> None:
    root = _project(tmp_path, "Left {{pipeline_track_count}}; right {{pipeline_track_count}}.\n")
    original = _hydrate(root)
    row = original["rows"][1]
    _replace_occurrence(root, row, "wrong")
    path = root / row["resolved_path"]
    path.write_text(path.read_text(encoding="utf-8") + f"Unrelated value: {row['expected']}.\n", encoding="utf-8")

    live = build_manuscript_staleness_report(root)
    assert live["rows"][1]["fresh"] is False
    assert live["all_fresh"] is False


@pytest.mark.parametrize("spec", ["", ":.2f", ":+.3f", ":.1e", ":+.2e", ":.2g", ":+.2g"])
def test_repeated_formatted_occurrences_use_the_actual_renderer(tmp_path: Path, spec: str) -> None:
    placeholder = "{{lambda_max" + spec + "}}"
    root = _project(tmp_path, f"Left {placeholder}; right {placeholder}.\n")
    original = _hydrate(root)
    assert original["all_fresh"] is True
    assert len(original["rows"]) == 2
    assert all(row["format_spec"] == spec for row in original["rows"])
    assert all(row["actual"] == row["expected"] for row in original["rows"])
    if "+" in spec:
        assert original["rows"][0]["expected"].startswith("+")
    if "e" in spec:
        assert "e+" in original["rows"][0]["expected"]
    row = original["rows"][1]
    _replace_occurrence(root, row, "!" * len(row["expected"]))
    live = build_manuscript_staleness_report(root)
    assert live["rows"][0]["fresh"] is True
    assert live["rows"][1]["fresh"] is False
    assert live["all_fresh"] is False


def test_adjacent_occurrences_keep_independent_positions(tmp_path: Path) -> None:
    root = _project(tmp_path, "{{pipeline_track_count}}{{pipeline_track_count}}\n")
    original = _hydrate(root)
    first, second = original["rows"]
    assert first["resolved_end"] == second["resolved_start"]
    _replace_occurrence(root, second, "!" * len(second["expected"]))
    live = build_manuscript_staleness_report(root)
    assert [row["fresh"] for row in live["rows"]] == [True, False]
    assert live["all_fresh"] is False


def test_missing_hydrated_file_and_unmapped_occurrence_fail_closed(tmp_path: Path) -> None:
    root = _project(tmp_path, "Value {{pipeline_track_count}}.\n")
    original = _hydrate(root)
    (root / original["rows"][0]["resolved_path"]).unlink()
    missing = build_manuscript_staleness_report(root)
    assert missing["all_fresh"] is False
    assert missing["rows"][0]["fresh"] is False

    (root / "manuscript" / "00_abstract.md").write_text("Value {{unmapped_variable}}.\n", encoding="utf-8")
    (root / "output" / "manuscript" / "00_abstract.md").write_text("Value .\n", encoding="utf-8")
    unmapped = build_manuscript_staleness_report(root)
    assert unmapped["rows"][0]["mapped"] is False
    assert unmapped["rows"][0]["fresh"] is False
    assert unmapped["all_fresh"] is False


@pytest.mark.parametrize("mutation", ["drop_repeat", "duplicate_identity", "format_spec", "source_offset", "section_hash", "row_count"])
def test_saved_occurrence_identity_and_content_are_rederived(tmp_path: Path, mutation: str) -> None:
    root = _project(tmp_path, "Left {{pipeline_track_count}}; right {{pipeline_track_count}}.\n")
    assert _hydrate(root)["all_fresh"] is True
    report_path = write_manuscript_staleness_report(root)
    original = json.loads(report_path.read_text(encoding="utf-8"))
    assert validate_manuscript_staleness_report(root) == []
    changed = copy.deepcopy(original)
    if mutation == "drop_repeat":
        changed["rows"].pop()
        changed["row_count"] = len(changed["rows"])
    elif mutation == "duplicate_identity":
        changed["rows"][1]["occurrence_id"] = changed["rows"][0]["occurrence_id"]
    elif mutation == "format_spec":
        changed["rows"][1]["format_spec"] = ":.2f"
    elif mutation == "source_offset":
        changed["rows"][1]["source_start"] += 1
    elif mutation == "section_hash":
        changed["sections"][0]["source_sha256"] = "0" * 64
    else:
        changed["row_count"] += 1
    assert changed["all_fresh"] is True
    report_path.write_text(json.dumps(changed), encoding="utf-8")
    assert any("stale relative to live" in issue for issue in validate_manuscript_staleness_report(root))
    assert any("stale relative to live" in issue for issue in validate_manuscript_staleness_report(root, changed))


def test_saved_green_report_does_not_hide_live_second_occurrence_corruption(tmp_path: Path) -> None:
    root = _project(tmp_path, "Left {{pipeline_track_count}}; right {{pipeline_track_count}}.\n")
    report = _hydrate(root)
    report_path = write_manuscript_staleness_report(root)
    saved_bytes = report_path.read_bytes()
    _replace_occurrence(root, report["rows"][1], "!" * len(report["rows"][1]["expected"]))
    issues = validate_manuscript_staleness_report(root)
    assert any("records stale manuscript tokens" in issue for issue in issues)
    assert any("stale relative to live" in issue for issue in issues)
    assert any(
        "manuscript_staleness_report.json is stale relative to live" in issue
        for issue in validate_integration_audit_artifacts(root)
    )
    assert report_path.read_bytes() == saved_bytes


def test_source_occurrence_movement_invalidates_same_count_saved_report(tmp_path: Path) -> None:
    root = _project(tmp_path, "Left {{pipeline_track_count}}; right {{pipeline_track_count}}.\n")
    assert _hydrate(root)["all_fresh"] is True
    saved_path = write_manuscript_staleness_report(root)
    saved = json.loads(saved_path.read_text(encoding="utf-8"))
    source_path = root / "manuscript" / "00_abstract.md"
    source_path.write_text(source_path.read_text(encoding="utf-8").replace("right", "later right"), encoding="utf-8")
    live = _hydrate(root)
    assert live["all_fresh"] is True
    assert live["row_count"] == saved["row_count"]
    assert live["rows"][1]["occurrence_id"] != saved["rows"][1]["occurrence_id"]
    assert any("stale relative to live" in issue for issue in validate_manuscript_staleness_report(root))


@pytest.mark.parametrize("token", ["manuscript_staleness_row_count", "manuscript_staleness_all_fresh"])
def test_self_referential_counts_and_freshness_converge_without_masking_repeats(tmp_path: Path, token: str) -> None:
    text = (
        "Count {{manuscript_staleness_row_count}}; again {{manuscript_staleness_row_count:+.1e}}.\n"
        "Fresh {{manuscript_staleness_all_fresh}}; again {{manuscript_staleness_all_fresh}}.\n"
        "Tracks {{pipeline_track_count}}.\n"
    )
    root = _project(tmp_path, text)
    reports = []
    for _ in range(4):
        _hydrate(root)
        report_path = write_manuscript_staleness_report(root)
        reports.append(json.loads(report_path.read_text(encoding="utf-8")))
    assert reports[0]["all_fresh"] is False
    assert reports[-1] == reports[-2]
    report = reports[-1]
    assert report["all_fresh"] is True
    assert report["row_count"] == len(list(TOKEN_MATCH_RE.finditer(text)))
    assert validate_manuscript_staleness_report(root) == []
    target_rows = [row for row in report["rows"] if row["token"] == token]
    assert len(target_rows) == 2
    _replace_occurrence(root, target_rows[1], "!" * len(target_rows[1]["expected"]))
    live = build_manuscript_staleness_report(root)
    live_targets = [row for row in live["rows"] if row["token"] == token]
    assert live_targets[0]["fresh"] is True
    assert live_targets[1]["fresh"] is False
    assert live["all_fresh"] is False
    assert validate_manuscript_staleness_report(root)


def test_extra_literal_at_token_boundary_cannot_pass_as_matching_prefix(tmp_path: Path) -> None:
    root = _project(tmp_path, "Left {{pipeline_track_count}}; right {{pipeline_track_count}}.\n")
    report = _hydrate(root)
    second = report["rows"][1]
    _replace_occurrence(root, second, second["expected"] + "wrong")
    live = build_manuscript_staleness_report(root)
    assert live["sections"][0]["canonical_hydration_matches"] is False
    assert live["all_fresh"] is False


def test_token_free_markdown_drift_breaks_canonical_hydration(tmp_path: Path) -> None:
    root = _project(tmp_path, "Tracks {{pipeline_track_count}}.\n")
    (root / "manuscript" / "17_conclusion.md").write_text("Finite scope.\n", encoding="utf-8")
    assert _hydrate(root)["all_fresh"] is True
    report_path = write_manuscript_staleness_report(root)
    (root / "output" / "manuscript" / "17_conclusion.md").write_text("Different scope.\n", encoding="utf-8")
    live = build_manuscript_staleness_report(root)
    assert all(row["fresh"] for row in live["rows"])
    conclusion = next(section for section in live["sections"] if section["section"] == "manuscript/17_conclusion.md")
    assert conclusion["token_occurrence_count"] == 0
    assert conclusion["canonical_hydration_matches"] is False
    assert live["all_fresh"] is False
    saved = json.loads(report_path.read_text(encoding="utf-8"))
    assert validate_manuscript_staleness_report(root, saved)


def test_resolved_newline_byte_drift_is_not_canonical_hydration(tmp_path: Path) -> None:
    root = _project(tmp_path, "Tracks {{pipeline_track_count}}.\n")
    report = _hydrate(root)
    assert report["all_fresh"] is True
    path = root / report["rows"][0]["resolved_path"]
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    live = build_manuscript_staleness_report(root)
    assert live["sections"][0]["resolved_sha256"] != report["sections"][0]["resolved_sha256"]
    assert live["sections"][0]["canonical_hydration_matches"] is False
    assert live["all_fresh"] is False
