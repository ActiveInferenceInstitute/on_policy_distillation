"""Claim ledger gate negative controls."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from gates.validation import validate_manuscript


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_manuscript_claim_ledger_missing_file_negative(project_root: Path, tmp_path: Path) -> None:
    ledger = project_root / "data" / "claim_ledger.yaml"
    backup = tmp_path / "claim_ledger.yaml.bak"
    original_stat = ledger.stat()
    backup.write_text(ledger.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        ledger.unlink()
        checks = validate_manuscript(project_root, only={"claim_ledger_valid"})
        assert checks["claim_ledger_valid"] is False
    finally:
        ledger.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
        os.utime(ledger, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_manuscript_claim_ledger_negative(project_root: Path, tmp_path: Path) -> None:
    ledger = project_root / "data" / "claim_ledger.yaml"
    backup = tmp_path / "claim_ledger.yaml.bak"
    original_stat = ledger.stat()
    backup.write_text(ledger.read_text(encoding="utf-8"), encoding="utf-8")
    broken_claim = """
- id: deliberately_missing_claim_evidence
  statement: Negative control claim points at a missing artifact.
  path: output/figures/not_a_real_claim_figure.png
  section: methods_sheaf
  tracks:
  - visualization
  evidence:
    predicate: file_exists
"""
    try:
        ledger.write_text(backup.read_text(encoding="utf-8") + broken_claim, encoding="utf-8")
        checks = validate_manuscript(project_root, only={"claim_ledger_valid"})
        assert checks["claim_ledger_valid"] is False
    finally:
        ledger.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
        os.utime(ledger, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))


def test_typed_claim_evidence_exercises_success_predicates(tmp_path: Path) -> None:
    from gates.claim_ledger import typed_claim_evidence_issues

    data_dir = tmp_path / "output" / "data"
    data_dir.mkdir(parents=True)
    payload = data_dir / "predicate_payload.json"
    payload.write_text(
        json.dumps(
            {
                "exists_value": "present",
                "truthy_value": 1,
                "zero_value": 0,
                "positive_value": 2,
                "flags": [True, True],
                "flag_map": {"a": True, "b": True},
                "rows": [{"ok": False}, {"ok": True}],
                "score": 1.01,
                "text": "needle in haystack",
                "items": ["a", "b", "c"],
            }
        ),
        encoding="utf-8",
    )
    yaml_payload = data_dir / "predicate_payload.yaml"
    yaml_payload.write_text("values:\n  - alpha\n  - beta\n", encoding="utf-8")
    text_payload = data_dir / "predicate_payload.txt"
    text_payload.write_text("plain evidence text", encoding="utf-8")
    ledger = tmp_path / "claim_ledger.yaml"
    ledger.write_text(
        "\n".join(
            [
                "claims:",
                "  - id: file_exists",
                "    statement: file exists",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      predicate: file_exists",
                "    waiver: synthetic fixture exercises bare file_exists; fieldless path-only presence is acceptable here",
                "  - id: exists_predicate",
                "    statement: value exists",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: exists_value",
                "      predicate: exists",
                "  - id: truthy_predicate",
                "    statement: value truthy",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: truthy_value",
                "      predicate: truthy",
                "  - id: zero_predicate",
                "    statement: value zero",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: zero_value",
                "      predicate: zero",
                "  - id: positive_predicate",
                "    statement: value positive",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: positive_value",
                "      predicate: positive",
                "  - id: all_true_list",
                "    statement: all flags true",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: flags",
                "      predicate: all_true",
                "  - id: all_true_map",
                "    statement: all map flags true",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: flag_map",
                "      predicate: all_true",
                "  - id: any_ok",
                "    statement: at least one row ok",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: rows",
                "      any:",
                "        field: ok",
                "        equals: true",
                "  - id: numeric_bounds",
                "    statement: score bounded",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: score",
                "      min: 1",
                "      max: 2",
                "  - id: text_contains",
                "    statement: text contains needle",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: text",
                "      contains: needle",
                "  - id: list_len_min",
                "    statement: list has enough items",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: items",
                "      len_min: 3",
                "  - id: yaml_load",
                "    statement: yaml can be inspected",
                "    path: output/data/predicate_payload.yaml",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: values",
                "      set_equals: [beta, alpha]",
                "  - id: text_load",
                "    statement: text can be inspected",
                "    path: output/data/predicate_payload.txt",
                "    tracks: [sheaf]",
                "    evidence:",
                "      contains: plain",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert typed_claim_evidence_issues(tmp_path, ledger_path=ledger) == []


def test_typed_claim_evidence_reports_structured_failures(tmp_path: Path) -> None:
    from gates.claim_ledger import typed_claim_evidence_issues

    data_dir = tmp_path / "output" / "data"
    data_dir.mkdir(parents=True)
    payload = data_dir / "predicate_payload.json"
    payload.write_text(json.dumps({"items": ["a"], "rows": [{"ok": False}], "value": 1}), encoding="utf-8")
    invalid = data_dir / "invalid.json"
    invalid.write_text("{", encoding="utf-8")
    ledger = tmp_path / "claim_ledger.yaml"
    ledger.write_text(
        "\n".join(
            [
                "claims:",
                "  - id: missing_path",
                "    statement: no path",
                "    tracks: [sheaf]",
                "  - id: missing_artifact",
                "    statement: missing artifact",
                "    path: output/data/missing.json",
                "    tracks: [sheaf]",
                "  - id: unreadable_json",
                "    statement: invalid json",
                "    path: output/data/invalid.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: value",
                "      equals: 1",
                "  - id: field_missing",
                "    statement: field missing",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: absent",
                "      equals: 1",
                "  - id: set_wrong_type",
                "    statement: set_equals needs a list",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: value",
                "      set_equals: [1]",
                "  - id: len_min_fails",
                "    statement: len_min fails",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: items",
                "      len_min: 2",
                "  - id: all_wrong_shape",
                "    statement: all requires list",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: value",
                "      all:",
                "        equals: 1",
                "  - id: any_fails",
                "    statement: any nested predicate fails",
                "    path: output/data/predicate_payload.json",
                "    tracks: [sheaf]",
                "    evidence:",
                "      field: rows",
                "      any:",
                "        field: ok",
                "        equals: true",
                "  - id: tracks_empty",
                "    statement: tracks empty",
                "    path: output/data/predicate_payload.json",
                "    tracks: []",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    issues = typed_claim_evidence_issues(tmp_path, ledger_path=ledger)

    assert len(issues) == 9
    assert any("missing path" in issue for issue in issues)
    assert any("cannot load evidence" in issue for issue in issues)
    assert any("tracks must not be empty" in issue for issue in issues)


def test_rederivation_evidence_forms_bite(tmp_path: Path) -> None:
    """equals_difference / leq_field / matches_artifact_field catch doctored artifacts."""
    from gates.claim_ledger import typed_claim_evidence_issues

    data_dir = tmp_path / "output" / "data"
    data_dir.mkdir(parents=True)
    honest = {
        "gap": {"terminal_gap": 0.75, "on_policy_final": 0.85, "off_policy_final": 0.10},
        "teacher_mean": 0.2,
        "student_mean": 0.3,
        "series": [0.1, 0.2, 0.3],
    }
    other = {"series": [0.1, 0.2, 0.3]}
    (data_dir / "demo.json").write_text(json.dumps(honest), encoding="utf-8")
    (data_dir / "other.json").write_text(json.dumps(other), encoding="utf-8")
    ledger = tmp_path / "ledger.yaml"
    ledger.write_text(
        "\n".join(
            [
                "claims:",
                "  - id: gap_rederives",
                "    statement: gap re-derives",
                "    path: output/data/demo.json",
                "    tracks: [simulation]",
                "    evidence:",
                "      field: gap.terminal_gap",
                "      equals_difference: [gap.on_policy_final, gap.off_policy_final]",
                "      tolerance: 1.0e-09",
                "  - id: means_ordered",
                "    statement: ordering re-derived",
                "    path: output/data/demo.json",
                "    tracks: [simulation]",
                "    evidence:",
                "      field: teacher_mean",
                "      leq_field: student_mean",
                "  - id: cross_artifact",
                "    statement: series identical across artifacts",
                "    path: output/data/demo.json",
                "    tracks: [simulation]",
                "    evidence:",
                "      field: series",
                "      matches_artifact_field:",
                "        path: output/data/other.json",
                "        field: series",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert typed_claim_evidence_issues(tmp_path, ledger_path=ledger) == []

    # Negative control 1: stored gap disagrees with its operands (curve swap).
    doctored = json.loads(json.dumps(honest))
    doctored["gap"]["on_policy_final"], doctored["gap"]["off_policy_final"] = 0.10, 0.85
    (data_dir / "demo.json").write_text(json.dumps(doctored), encoding="utf-8")
    issues = typed_claim_evidence_issues(tmp_path, ledger_path=ledger)
    assert any("gap_rederives" in issue for issue in issues)

    # Negative control 2: ordering flipped.
    doctored = json.loads(json.dumps(honest))
    doctored["teacher_mean"] = 0.9
    (data_dir / "demo.json").write_text(json.dumps(doctored), encoding="utf-8")
    issues = typed_claim_evidence_issues(tmp_path, ledger_path=ledger)
    assert any("means_ordered" in issue for issue in issues)

    # Negative control 3: cross-artifact series diverges by one element.
    (data_dir / "demo.json").write_text(json.dumps(honest), encoding="utf-8")
    (data_dir / "other.json").write_text(json.dumps({"series": [0.1, 0.2, 0.30000001]}), encoding="utf-8")
    issues = typed_claim_evidence_issues(tmp_path, ledger_path=ledger)
    assert any("cross_artifact" in issue for issue in issues)

    # Negative control 4: referenced cross-artifact missing entirely.
    (data_dir / "other.json").unlink()
    issues = typed_claim_evidence_issues(tmp_path, ledger_path=ledger)
    assert any("cross_artifact" in issue for issue in issues)


def test_claim_ledger_private_predicates_and_lookup_edges() -> None:
    from gates.claim_ledger import _lookup_field, _numbers_equal, _predicate_holds, _set_equals

    assert _lookup_field({"rows": [{"ok": True}]}, "rows.0.ok") is True
    with pytest.raises(KeyError):
        _lookup_field("not-structured", "rows")

    assert _numbers_equal(True, 1, 0.0) is True
    assert _numbers_equal(1.0, 1.0000001, 1e-5) is True
    assert _numbers_equal("alpha", "alpha", 0.0) is True

    assert _predicate_holds("x", "exists") is True
    assert _predicate_holds(True, "file_exists") is True
    assert _predicate_holds([1], "non_empty") is True
    assert _predicate_holds(0, "zero") is True
    assert _predicate_holds(2, "positive") is True
    assert _predicate_holds({"a": True}, "all_true") is True
    assert _predicate_holds([True], "all_true") is True
    assert _predicate_holds(True, "is_true") is True
    assert _predicate_holds("x", "unknown_predicate") is False
    assert _predicate_holds("x", "all_true") is False

    assert _set_equals(["b", "a"], ["a", "b"]) is True
    assert _set_equals("not-list", ["a"]) is False


def test_evidence_spec_holds_direct_guard_branches(tmp_path: Path) -> None:
    from gates.claim_ledger import _evidence_spec_holds

    root = tmp_path
    data_dir = root / "output" / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "other.json").write_text(json.dumps({"scalar": 1.0, "items": [1, 2]}), encoding="utf-8")
    document = {
        "a": 3.0,
        "b": 1.0,
        "gap": 2.0,
        "limit": 4.0,
        "text": "alpha beta",
        "items": [1, 2],
        "rows": [{"ok": False}, {"ok": True}],
        "nested": [{"value": 1}, {"value": 1}],
    }

    assert _evidence_spec_holds(document, {"field": "gap", "equals_difference": ["a", "b"]})
    assert not _evidence_spec_holds(document, {"field": "missing", "equals": 1})
    assert not _evidence_spec_holds(document, {"field": "gap", "equals_difference": ["a", "missing"]})
    assert not _evidence_spec_holds(document, {"field": "gap", "equals_difference": ["b", "a"]})
    assert _evidence_spec_holds(document, {"field": "gap", "leq_field": "limit"})
    assert not _evidence_spec_holds(document, {"field": "a", "leq_field": "missing"})
    assert not _evidence_spec_holds(document, {"field": "text", "leq_field": "limit"})
    assert not _evidence_spec_holds(document, {"field": "limit", "leq_field": "gap"})
    assert _evidence_spec_holds(
        document,
        {"field": "items", "matches_artifact_field": {"path": "output/data/other.json", "field": "items"}},
        root=root,
    )
    assert _evidence_spec_holds(
        document,
        {"field": "b", "matches_artifact_field": {"path": "output/data/other.json", "field": "scalar"}},
        root=root,
    )
    assert not _evidence_spec_holds(
        document,
        {"field": "items", "matches_artifact_field": {"path": "output/data/other.json", "field": "missing"}},
        root=root,
    )
    assert not _evidence_spec_holds(
        document,
        {"field": "items", "matches_artifact_field": {"path": "output/data/other.json", "field": "items"}},
    )
    assert not _evidence_spec_holds(document, {"field": "items", "matches_artifact_field": "bad"}, root=root)
    assert not _evidence_spec_holds(
        document,
        {"field": "b", "matches_artifact_field": {"path": "output/data/other.json", "field": "items"}},
        root=root,
    )
    assert not _evidence_spec_holds(document, {"field": "gap", "equals": 3})
    assert not _evidence_spec_holds(document, {"field": "gap", "approx": 3, "tolerance": 0.1})
    assert not _evidence_spec_holds(document, {"field": "gap", "min": 3})
    assert not _evidence_spec_holds(document, {"field": "gap", "max": 1})
    assert not _evidence_spec_holds(document, {"field": "text", "contains": "gamma"})
    assert not _evidence_spec_holds(document, {"field": "items", "set_equals": [1, 3]})
    assert not _evidence_spec_holds(document, {"field": "items", "len_equals": 3})
    assert not _evidence_spec_holds(document, {"field": "items", "len_min": 3})
    assert _evidence_spec_holds(document, {"field": "nested", "all": {"field": "value", "equals": 1}})
    assert not _evidence_spec_holds(document, {"field": "text", "all": {"equals": 1}})
    assert not _evidence_spec_holds(document, {"field": "nested", "all": "bad"})
    assert not _evidence_spec_holds(document, {"field": "nested", "all": {"field": "value", "equals": 2}})
    assert _evidence_spec_holds(document, {"field": "rows", "any": {"field": "ok", "equals": True}})
    assert not _evidence_spec_holds(document, {"field": "text", "any": {"equals": 1}})
    assert not _evidence_spec_holds(document, {"field": "rows", "any": "bad"})
    assert not _evidence_spec_holds(document, {"field": "rows", "any": {"field": "missing", "equals": True}})
    assert not _evidence_spec_holds(document, {"field": "text", "predicate": "zero"})


def test_validate_claim_ledger_branch_edges(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import gates.claim_ledger as claim_ledger
    import manuscript.sheaf as sheaf

    assert claim_ledger.validate_claim_ledger(tmp_path) is False

    data_dir = tmp_path / "output" / "data"
    data_dir.mkdir(parents=True)
    artifact = data_dir / "present.json"
    artifact.write_text(json.dumps({"ok": True}), encoding="utf-8")
    (data_dir / "sheaf_coverage_matrix.json").write_text(json.dumps({"cells": []}), encoding="utf-8")
    ledger = tmp_path / "data" / "claim_ledger.yaml"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(
        "claims:\n"
        "  - id: missing_artifact\n"
        "    path: output/data/missing.json\n"
        "    tracks: [sheaf]\n",
        encoding="utf-8",
    )
    assert claim_ledger.validate_claim_ledger(tmp_path) is False

    manifest_dir = tmp_path / "manuscript" / "sheaf"
    manifest_dir.mkdir(parents=True)
    (manifest_dir / "manifest.yaml").write_text("registry_path: manuscript/sheaf/tracks.yaml\n", encoding="utf-8")
    (manifest_dir / "tracks.yaml").write_text("tracks: []\n", encoding="utf-8")
    ledger.write_text(
        "claims:\n"
        "  - id: coverage_no_gray\n"
        "    path: output/data/present.json\n"
        "    tracks: [coverage]\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sheaf,
        "load_manifest",
        lambda *args, **kwargs: type("Manifest", (), {"registry_path": "manuscript/sheaf/tracks.yaml"})(),
    )
    monkeypatch.setattr(sheaf, "load_track_registry", lambda *args, **kwargs: object())
    monkeypatch.setattr(sheaf, "load_coverage_json", lambda *args, **kwargs: {"cells": []})
    monkeypatch.setattr(sheaf, "gray_cell_count_from_json", lambda *_args: 1)
    monkeypatch.setattr(sheaf, "validate_coverage_json_data", lambda *_args: [])
    monkeypatch.setattr(claim_ledger, "validate_typed_claim_evidence", lambda *args, **kwargs: True)
    assert claim_ledger.validate_claim_ledger(tmp_path) is False

    monkeypatch.setattr(sheaf, "gray_cell_count_from_json", lambda *_args: 0)
    monkeypatch.setattr(
        sheaf,
        "validate_coverage_json_data",
        lambda *_args: [type("Issue", (), {"level": "error"})()],
    )
    assert claim_ledger.validate_claim_ledger(tmp_path) is False

    monkeypatch.setattr(sheaf, "validate_coverage_json_data", lambda *_args: [])
    assert claim_ledger.validate_claim_ledger(tmp_path) is True
