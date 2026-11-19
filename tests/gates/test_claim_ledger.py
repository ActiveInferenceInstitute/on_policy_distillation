"""Claim ledger gate negative controls."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from gates.validation import validate_manuscript


_NONFINITE_NUMERICAL_VALUES = [
    pytest.param(float("nan"), id="native-nan"),
    pytest.param(float("inf"), id="native-positive-infinity"),
    pytest.param(float("-inf"), id="native-negative-infinity"),
    pytest.param("NaN", id="string-nan"),
    pytest.param("Infinity", id="string-positive-infinity"),
    pytest.param("-Infinity", id="string-negative-infinity"),
    pytest.param("1e309", id="string-overflow"),
]


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


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_manuscript_claim_ledger_negative_empirical_locator(project_root: Path, tmp_path: Path) -> None:
    import yaml

    ledger = project_root / "data" / "claim_ledger.yaml"
    backup = tmp_path / "claim_ledger.yaml.bak"
    original_stat = ledger.stat()
    backup.write_text(ledger.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        payload = yaml.safe_load(backup.read_text(encoding="utf-8")) or {}
        for claim in payload.get("claims") or []:
            if claim.get("id") == "fp_empirical_benchmark_table_locator":
                claim["evidence"]["equals"] = "Qwen3 Technical Report"
                break
        else:
            raise AssertionError("missing empirical benchmark locator claim")
        ledger.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
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


def _assert_typed_evidence_admission(
    root: Path,
    document: dict[str, Any],
    evidence: dict[str, Any],
    expected: bool,
    *,
    suffix: str,
    other_document: dict[str, Any] | None = None,
) -> None:
    """Read real structured artifacts and dispatch a standalone typed claim."""
    import yaml

    from gates.claim_ledger import typed_claim_evidence_issues, validate_typed_claim_evidence

    root.mkdir(parents=True, exist_ok=True)
    serialize = json.dumps if suffix == ".json" else yaml.safe_dump
    artifact = root / f"evidence{suffix}"
    artifact.write_text(serialize(document), encoding="utf-8")
    if other_document is not None:
        (root / f"reference{suffix}").write_text(serialize(other_document), encoding="utf-8")
    ledger = root / "data" / "claim_ledger.yaml"
    ledger.parent.mkdir()
    ledger.write_text(
        yaml.safe_dump(
            {
                "claims": [
                    {
                        "id": "finite_evidence",
                        "path": artifact.name,
                        "tracks": ["simulation"],
                        "evidence": evidence,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    expected_issues = [] if expected else [f"finite_evidence: evidence predicate failed for {artifact.name}"]
    assert typed_claim_evidence_issues(root) == expected_issues
    assert validate_typed_claim_evidence(root) is expected


@pytest.mark.parametrize("suffix", [".json", ".yaml"])
@pytest.mark.parametrize("numeric_strings", [False, True], ids=["numbers", "numeric-strings"])
@pytest.mark.parametrize(
    ("operation", "value", "expected"),
    [
        pytest.param("min", 0.75, False, id="min-below"),
        pytest.param("min", 1.0, True, id="min-at"),
        pytest.param("min", 1.25, True, id="min-above"),
        pytest.param("max", 0.75, True, id="max-below"),
        pytest.param("max", 1.0, True, id="max-at"),
        pytest.param("max", 1.25, False, id="max-above"),
        pytest.param("leq_field", 0.75, True, id="reference-below"),
        pytest.param("leq_field", 1.0, True, id="reference-at"),
        pytest.param("leq_field", 1.25, False, id="reference-above"),
        pytest.param("zero", -0.25, False, id="zero-below"),
        pytest.param("zero", 0.0, True, id="zero-at"),
        pytest.param("zero", 0.25, False, id="zero-above"),
        pytest.param("positive", -0.25, False, id="positive-below"),
        pytest.param("positive", 0.0, False, id="positive-at"),
        pytest.param("positive", 0.25, True, id="positive-above"),
    ],
)
def test_typed_claim_evidence_finite_admission_boundaries(
    tmp_path: Path, suffix: str, numeric_strings: bool, operation: str, value: float, expected: bool
) -> None:
    bound = "1.0" if numeric_strings else 1.0
    evidence: dict[str, Any] = {"field": "value"}
    if operation in {"min", "max"}:
        evidence[operation] = bound
    elif operation == "leq_field":
        evidence[operation] = "bound"
    else:
        evidence["predicate"] = operation
    _assert_typed_evidence_admission(
        tmp_path,
        {"value": str(value) if numeric_strings else value, "bound": bound},
        evidence,
        expected,
        suffix=suffix,
    )


@pytest.mark.parametrize("suffix", [".json", ".yaml"])
@pytest.mark.parametrize("operation", ["equals", "approx", "equals_difference", "leq_field"])
@pytest.mark.parametrize("tolerance", [0.125, "0.125"], ids=["number", "numeric-string"])
@pytest.mark.parametrize(
    ("offset", "expected"), [(0.0625, True), (0.125, True), (0.25, False)], ids=["below", "at", "above"]
)
def test_typed_claim_evidence_finite_admission_tolerances(
    tmp_path: Path, suffix: str, operation: str, tolerance: float | str, offset: float, expected: bool
) -> None:
    operand: Any = ["a", "b"] if operation == "equals_difference" else "bound" if operation == "leq_field" else 1.0
    _assert_typed_evidence_admission(
        tmp_path,
        {"value": 1.0 + offset, "bound": 1.0, "a": 2.0, "b": 1.0},
        {"field": "value", operation: operand, "tolerance": tolerance},
        expected,
        suffix=suffix,
    )


@pytest.mark.parametrize("suffix", [".json", ".yaml"])
@pytest.mark.parametrize("operation", ["equals_difference", "leq_field"])
@pytest.mark.parametrize("tolerance", [None, 0.0, "0.0"], ids=["omitted", "zero", "string-zero"])
@pytest.mark.parametrize(
    ("value", "expected"), [(0.5e-9, True), (1e-9, True), (2e-9, False)], ids=["below", "at", "above"]
)
def test_typed_claim_evidence_finite_admission_default_tolerance(
    tmp_path: Path, suffix: str, operation: str, tolerance: float | str | None, value: float, expected: bool
) -> None:
    evidence: dict[str, Any] = {
        "field": "value",
        operation: ["a", "b"] if operation == "equals_difference" else "bound",
    }
    if tolerance is not None:
        evidence["tolerance"] = tolerance
    _assert_typed_evidence_admission(
        tmp_path, {"value": value, "a": 1.0, "b": 1.0, "bound": 0.0}, evidence, expected, suffix=suffix
    )


@pytest.mark.parametrize("suffix", [".json", ".yaml"])
@pytest.mark.parametrize("operation", ["len_equals", "len_min"])
@pytest.mark.parametrize("bound", [2, "2"], ids=["number", "numeric-string"])
@pytest.mark.parametrize("length", [1, 2, 3], ids=["below", "at", "above"])
def test_typed_claim_evidence_finite_admission_lengths(
    tmp_path: Path, suffix: str, operation: str, bound: int | str, length: int
) -> None:
    expected = length == 2 if operation == "len_equals" else length >= 2
    _assert_typed_evidence_admission(
        tmp_path, {"value": [True] * length}, {"field": "value", operation: bound}, expected, suffix=suffix
    )


@pytest.mark.parametrize("suffix", [".json", ".yaml"])
@pytest.mark.parametrize("nonfinite", _NONFINITE_NUMERICAL_VALUES)
@pytest.mark.parametrize(
    "evidence",
    [
        pytest.param({"min": 0.0}, id="min"),
        pytest.param({"max": 2.0}, id="max"),
        pytest.param({"approx": 1.0}, id="approx"),
        pytest.param({"leq_field": "bound"}, id="referenced-bound"),
        pytest.param({"equals_difference": ["a", "b"]}, id="difference"),
        pytest.param({"predicate": "zero"}, id="zero"),
        pytest.param({"predicate": "positive"}, id="positive"),
    ],
)
def test_typed_claim_evidence_finite_admission_rejects_values(
    tmp_path: Path, suffix: str, nonfinite: float | str, evidence: dict[str, Any]
) -> None:
    _assert_typed_evidence_admission(
        tmp_path,
        {"value": nonfinite, "bound": 1.0, "a": 2.0, "b": 1.0},
        {"field": "value", **evidence},
        False,
        suffix=suffix,
    )


@pytest.mark.parametrize("suffix", [".json", ".yaml"])
@pytest.mark.parametrize("nonfinite", _NONFINITE_NUMERICAL_VALUES)
@pytest.mark.parametrize("parameter", ["min", "max", "approx", "tolerance", "len_equals", "len_min"])
def test_typed_claim_evidence_finite_admission_rejects_parameters(
    tmp_path: Path, suffix: str, nonfinite: float | str, parameter: str
) -> None:
    evidence: dict[str, Any] = {"field": "value", parameter: nonfinite}
    if parameter == "tolerance":
        evidence["equals"] = 1.0
    value: Any = [True] if parameter.startswith("len_") else 1.0
    _assert_typed_evidence_admission(tmp_path, {"value": value}, evidence, False, suffix=suffix)


@pytest.mark.parametrize("suffix", [".json", ".yaml"])
@pytest.mark.parametrize("nonfinite", _NONFINITE_NUMERICAL_VALUES)
@pytest.mark.parametrize("field", ["a", "b", "bound"])
def test_typed_claim_evidence_finite_admission_rejects_referenced_operands(
    tmp_path: Path, suffix: str, nonfinite: float | str, field: str
) -> None:
    document = {"value": 1.0, "a": 2.0, "b": 1.0, "bound": 1.0}
    document[field] = nonfinite
    evidence = {"leq_field": "bound"} if field == "bound" else {"equals_difference": ["a", "b"]}
    _assert_typed_evidence_admission(
        tmp_path, document, {"field": "value", **evidence}, False, suffix=suffix
    )


@pytest.mark.parametrize("suffix", [".json", ".yaml"])
@pytest.mark.parametrize("nonfinite", _NONFINITE_NUMERICAL_VALUES[:3])
@pytest.mark.parametrize("shape", ["scalar", "list", "mapping"])
def test_typed_claim_evidence_finite_admission_rejects_cross_artifact_values(
    tmp_path: Path, suffix: str, nonfinite: float, shape: str
) -> None:
    value: Any = nonfinite if shape == "scalar" else [True, nonfinite] if shape == "list" else {"score": nonfinite}
    _assert_typed_evidence_admission(
        tmp_path,
        {"value": value},
        {"field": "value", "matches_artifact_field": {"path": f"reference{suffix}", "field": "value"}},
        False,
        suffix=suffix,
        other_document={"value": value},
    )


@pytest.mark.parametrize("suffix", [".json", ".yaml"])
@pytest.mark.parametrize("nonfinite", _NONFINITE_NUMERICAL_VALUES[:3])
@pytest.mark.parametrize("role", ["value", "expected", "reference"])
def test_typed_claim_evidence_finite_admission_rejects_boolean_coercion(
    tmp_path: Path, suffix: str, nonfinite: float, role: str
) -> None:
    evidence: dict[str, Any] = {"field": "value", "equals": nonfinite if role == "expected" else True}
    if role == "reference":
        evidence["matches_artifact_field"] = {"path": f"reference{suffix}", "field": "value"}
    _assert_typed_evidence_admission(
        tmp_path,
        {"value": nonfinite if role == "value" else True},
        evidence,
        False,
        suffix=suffix,
        other_document={"value": nonfinite} if role == "reference" else None,
    )


@pytest.mark.parametrize("suffix", [".json", ".yaml"])
@pytest.mark.parametrize("nonfinite", _NONFINITE_NUMERICAL_VALUES)
@pytest.mark.parametrize("quantifier", ["all", "any"])
@pytest.mark.parametrize("empty", [False, True], ids=["populated", "empty"])
def test_typed_claim_evidence_finite_admission_rejects_nested_parameters(
    tmp_path: Path, suffix: str, nonfinite: float | str, quantifier: str, empty: bool
) -> None:
    _assert_typed_evidence_admission(
        tmp_path,
        {"rows": [] if empty else [{"score": 1.0}]},
        {"field": "rows", quantifier: {"field": "score", "min": nonfinite}},
        False,
        suffix=suffix,
    )


@pytest.mark.parametrize("nonfinite", _NONFINITE_NUMERICAL_VALUES)
@pytest.mark.parametrize("nested", [False, True], ids=["direct-any", "nested-any"])
@pytest.mark.parametrize(
    ("field", "evidence"),
    [
        pytest.param("score", {"min": 0.0}, id="minimum"),
        pytest.param("score", {"approx": 1.0}, id="approximation"),
        pytest.param("score", {"predicate": "positive"}, id="positive"),
        pytest.param("bound", {"leq_field": "bound"}, id="bound"),
        pytest.param("a", {"equals_difference": ["a", "b"]}, id="minuend"),
        pytest.param("b", {"equals_difference": ["a", "b"]}, id="subtrahend"),
    ],
)
def test_typed_claim_evidence_finite_admission_rejects_hidden_any_operands(
    tmp_path: Path, nonfinite: float | str, nested: bool, field: str, evidence: dict[str, Any]
) -> None:
    finite = {"score": 1.0, "a": 2.0, "b": 1.0, "bound": 1.0}
    nonfinite_row = {**finite, field: nonfinite}
    document: dict[str, Any] = {"rows": [finite, nonfinite_row]}
    spec: dict[str, Any] = {"field": "rows", "any": {"field": "score", **evidence}}
    if nested:
        document = {"groups": [{"rows": [finite]}, document]}
        spec = {"field": "groups", "any": spec}
    _assert_typed_evidence_admission(tmp_path, document, spec, False, suffix=".json")


@pytest.mark.parametrize("suffix", [".json", ".yaml"])
@pytest.mark.parametrize(
    ("value", "evidence"),
    [
        pytest.param("ordinary text", {"equals": "ordinary text"}, id="text-equality"),
        pytest.param("ordinary text", {"approx": "ordinary text"}, id="existing-text-approximation"),
        pytest.param("NaN", {"equals": "NaN"}, id="text-nan"),
        pytest.param("Infinity", {"contains": "fin"}, id="text-infinity"),
        pytest.param("Infinity", {"predicate": "truthy"}, id="text-truthiness"),
        pytest.param(["NaN", "Infinity"], {"set_equals": ["Infinity", "NaN"]}, id="text-set"),
        pytest.param(True, {"equals": True}, id="true"),
        pytest.param(False, {"equals": False}, id="false"),
        pytest.param(True, {"equals": 1}, id="existing-boolean-numeric-equality"),
        pytest.param([True, True], {"predicate": "all_true"}, id="boolean-list"),
        pytest.param({"a": True, "b": True}, {"predicate": "all_true"}, id="boolean-mapping"),
        pytest.param(False, {"predicate": "zero"}, id="existing-boolean-zero"),
        pytest.param(True, {"predicate": "positive"}, id="existing-boolean-positive"),
        pytest.param("1.0", {"approx": "1.0"}, id="existing-numeric-string-equality"),
    ],
)
def test_typed_claim_evidence_finite_admission_preserves_text_and_booleans(
    tmp_path: Path, suffix: str, value: Any, evidence: dict[str, Any]
) -> None:
    _assert_typed_evidence_admission(
        tmp_path,
        {"value": value},
        {
            "field": "value",
            **evidence,
            "matches_artifact_field": {"path": f"reference{suffix}", "field": "value"},
        },
        True,
        suffix=suffix,
        other_document={"value": value},
    )


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


def test_sdpg_claim_evidence_rejects_malformed_artifact(tmp_path: Path) -> None:
    """SDPG claim predicates fail on missing modes, sparse signal, or broken KL rows."""
    from firstprinciples import artifacts
    from gates.claim_ledger import typed_claim_evidence_issues

    data_dir = tmp_path / "output" / "data" / "firstprinciples"
    data_dir.mkdir(parents=True)
    artifact_path = data_dir / "sdpg_demo.json"
    honest = artifacts.sdpg_demo()
    artifact_path.write_text(json.dumps(honest), encoding="utf-8")
    ledger = tmp_path / "claim_ledger.yaml"
    ledger.write_text(
        "\n".join(
            [
                "claims:",
                "  - id: sdpg_modes",
                "    statement: SDPG modes complete",
                "    path: output/data/firstprinciples/sdpg_demo.json",
                "    tracks: [analytical]",
                "    evidence:",
                "      field: mode_keys",
                "      set_equals: [fkl, rkl, ufkl, urkl]",
                "  - id: sdpg_dense_signal",
                "    statement: SDPG dense signal",
                "    path: output/data/firstprinciples/sdpg_demo.json",
                "    tracks: [analytical]",
                "    evidence:",
                "      field: dense_privileged_signal",
                "      predicate: is_true",
                "  - id: sdpg_self_distillation_positive",
                "    statement: SDPG self-distillation KL positive",
                "    path: output/data/firstprinciples/sdpg_demo.json",
                "    tracks: [analytical]",
                "    evidence:",
                "      field: mode_rows",
                "      all:",
                "        field: self_distillation_kl",
                "        predicate: positive",
                "  - id: sdpg_reference_anchor_positive",
                "    statement: SDPG reference anchor KL positive",
                "    path: output/data/firstprinciples/sdpg_demo.json",
                "    tracks: [analytical]",
                "    evidence:",
                "      field: mode_rows",
                "      all:",
                "        field: reference_kl",
                "        predicate: positive",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert typed_claim_evidence_issues(tmp_path, ledger_path=ledger) == []

    doctored = json.loads(json.dumps(honest))
    doctored["mode_keys"] = ["fkl", "rkl", "ufkl"]
    artifact_path.write_text(json.dumps(doctored), encoding="utf-8")
    assert any("sdpg_modes" in issue for issue in typed_claim_evidence_issues(tmp_path, ledger_path=ledger))

    doctored = json.loads(json.dumps(honest))
    doctored["dense_privileged_signal"] = False
    artifact_path.write_text(json.dumps(doctored), encoding="utf-8")
    assert any("sdpg_dense_signal" in issue for issue in typed_claim_evidence_issues(tmp_path, ledger_path=ledger))

    doctored = json.loads(json.dumps(honest))
    doctored["mode_rows"][0]["self_distillation_kl"] = 0.0
    artifact_path.write_text(json.dumps(doctored), encoding="utf-8")
    assert any(
        "sdpg_self_distillation_positive" in issue
        for issue in typed_claim_evidence_issues(tmp_path, ledger_path=ledger)
    )

    doctored = json.loads(json.dumps(honest))
    doctored["mode_rows"][0]["reference_kl"] = 0.0
    artifact_path.write_text(json.dumps(doctored), encoding="utf-8")
    assert any(
        "sdpg_reference_anchor_positive" in issue
        for issue in typed_claim_evidence_issues(tmp_path, ledger_path=ledger)
    )


def test_sdpg_missing_claim_evidence_fails_claim_audit(tmp_path: Path) -> None:
    from roadmap_tracks.integration_audit_builders import build_claim_evidence_audit

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "claim_ledger.yaml").write_text(
        "\n".join(
            [
                "claims:",
                "  - id: fp_sdpg_modes_complete",
                "    statement: SDPG modes complete",
                "    path: output/data/firstprinciples/sdpg_demo.json",
                "    tracks: [analytical]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    audit = build_claim_evidence_audit(tmp_path)
    assert audit["all_claims_typed"] is False
    assert audit["rows"] == [
        {
            "id": "fp_sdpg_modes_complete",
            "path": "output/data/firstprinciples/sdpg_demo.json",
            "has_evidence": False,
            "has_tracks": True,
        }
    ]


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
