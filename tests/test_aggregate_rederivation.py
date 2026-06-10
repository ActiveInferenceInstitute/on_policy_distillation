"""Read-time aggregate re-derivation: rules bind, live tree passes, lying flags die.

Negative controls follow the Run-2 doctrine: they test the LYING case (row data
mutated while the stored ``all_*`` flag stays ``True``), not the honest-red case.
Controls run on isolated copies under ``tmp_path`` so no shared artifact is
mutated and no ``mutates_artifacts`` marker is needed.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from gates.aggregate_rederivation import (
    ARTIFACT_AGGREGATE_RULES,
    aggregate_rederivation_rows,
    aggregates_consistent,
    rederive_aggregate,
    rule_count,
)


def _spec_fields(spec: tuple) -> set[str]:
    kind = spec[0]
    if kind in {"true", "nonempty", "empty", "positive"}:
        return {spec[1]}
    if kind == "equals":
        return {spec[1]}
    if kind == "fields_equal":
        return {spec[1], spec[2]}
    if kind in {"all", "any"}:
        return set().union(*(_spec_fields(sub) for sub in spec[1:]))
    if kind == "implies":
        return _spec_fields(spec[1]) | _spec_fields(spec[2])
    raise AssertionError(f"unknown spec kind {kind!r}")


def test_rules_match_live_payloads(project_root: Path) -> None:
    """Meta-test: every rule references a real artifact, aggregate, and row fields.

    A rule whose rows-field or aggregate name drifts from the artifact schema
    would re-derive vacuously; this test makes such drift loud.
    """
    assert rule_count() >= 25
    for rel, rules in ARTIFACT_AGGREGATE_RULES.items():
        path = project_root / rel
        assert path.is_file(), f"rule artifact missing: {rel}"
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("rows")
        assert isinstance(rows, list) and rows, f"{rel} has no rows for re-derivation"
        row_fields = set().union(*(set(row) for row in rows if isinstance(row, dict)))
        for aggregate_field, spec in rules:
            assert aggregate_field in payload, f"{rel} lacks aggregate {aggregate_field}"
            assert isinstance(payload[aggregate_field], bool)
            missing = _spec_fields(spec) - row_fields
            assert not missing, f"{rel}:{aggregate_field} predicate fields absent from rows: {missing}"


def test_live_tree_aggregates_consistent(project_root: Path) -> None:
    rows = aggregate_rederivation_rows(project_root)
    bad = [row for row in rows if not row["consistent"]]
    assert not bad, f"live aggregates disagree with rows: {bad}"
    assert aggregates_consistent(project_root) is True


def test_validate_outputs_exposes_rederivation_check(project_root: Path) -> None:
    from gates.validation import validate_outputs

    checks = validate_outputs(project_root, only={"aggregate_rederivation"})
    assert checks.get("aggregate_rederivation") is True


def test_empty_rows_with_true_flag_rederive_false() -> None:
    """Vacuous truth over [] is exactly the green-wash this layer exists to stop."""
    assert rederive_aggregate({"rows": [], "all_fresh": True}, ("true", "fresh")) is False
    assert rederive_aggregate({"all_fresh": True}, ("true", "fresh")) is False
    assert rederive_aggregate({"rows": "not-a-list", "all_fresh": True}, ("true", "fresh")) is False


def test_predicate_mini_language() -> None:
    spec_any = ("any", ("true", "a"), ("true", "b"))
    assert rederive_aggregate({"rows": [{"a": True, "b": False}]}, spec_any) is True
    assert rederive_aggregate({"rows": [{"a": False, "b": False}]}, spec_any) is False
    spec_impl = ("implies", ("true", "cond"), ("nonempty", "why"))
    assert rederive_aggregate({"rows": [{"cond": False}]}, spec_impl) is True
    assert rederive_aggregate({"rows": [{"cond": True, "why": ""}]}, spec_impl) is False
    spec_pos = ("positive", "n")
    assert rederive_aggregate({"rows": [{"n": 1}]}, spec_pos) is True
    assert rederive_aggregate({"rows": [{"n": 0}]}, spec_pos) is False
    assert rederive_aggregate({"rows": [{"n": True}]}, spec_pos) is False
    spec_eq = ("equals", "status", "proved")
    assert rederive_aggregate({"rows": [{"status": "proved"}]}, spec_eq) is True
    assert rederive_aggregate({"rows": [{"status": "sorry"}]}, spec_eq) is False
    spec_fe = ("fields_equal", "x", "y")
    assert rederive_aggregate({"rows": [{"x": "v", "y": "v"}]}, spec_fe) is True
    assert rederive_aggregate({"rows": [{"x": "", "y": ""}]}, spec_fe) is False


def _isolated_copy(project_root: Path, tmp_path: Path, rels: list[str]) -> Path:
    """Copy selected artifacts into a tmp project skeleton for lying-case mutation."""
    for rel in rels:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(project_root / rel, target)
    return tmp_path


def _mutate_row_keep_flag(root: Path, rel: str, mutate) -> None:
    path = root / rel
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutate(payload["rows"][0])
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_lying_flag_caught_stale_report(project_root: Path, tmp_path: Path) -> None:
    rel = "output/reports/stale_artifact_report.json"
    root = _isolated_copy(project_root, tmp_path, [rel])
    rows = aggregate_rederivation_rows(root)
    target = [r for r in rows if r["artifact"] == rel]
    assert all(r["consistent"] for r in target)
    _mutate_row_keep_flag(root, rel, lambda row: row.__setitem__("fresh", False))
    rows = aggregate_rederivation_rows(root)
    lying = [r for r in rows if r["artifact"] == rel and r["aggregate"] == "all_fresh"]
    assert lying and not lying[0]["consistent"], "mutated row with stale True flag must be caught"


def test_lying_flag_caught_lean_inventory(project_root: Path, tmp_path: Path) -> None:
    rel = "output/reports/lean_theorem_inventory.json"
    root = _isolated_copy(project_root, tmp_path, [rel])
    _mutate_row_keep_flag(root, rel, lambda row: row.__setitem__("status", "sorry"))
    rows = aggregate_rederivation_rows(root)
    lying = [r for r in rows if r["artifact"] == rel and r["aggregate"] == "all_proved"]
    assert lying and not lying[0]["consistent"], "sorry theorem under all_proved=True must be caught"


def test_lying_flag_caught_diffoscope(project_root: Path, tmp_path: Path) -> None:
    rel = "output/reports/artifact_diffoscope.json"
    root = _isolated_copy(project_root, tmp_path, [rel])
    _mutate_row_keep_flag(root, rel, lambda row: row.__setitem__("equal", False))
    rows = aggregate_rederivation_rows(root)
    lying = [r for r in rows if r["artifact"] == rel and r["aggregate"] == "all_equal"]
    assert lying and not lying[0]["consistent"], "unequal hash row under all_equal=True must be caught"


def test_lying_flag_caught_conditional_posterior_grid(project_root: Path, tmp_path: Path) -> None:
    """Conditional predicate: available-but-unnormalized posterior must be caught."""
    rel = "output/data/pymdp_policy_posterior_grid.json"
    root = _isolated_copy(project_root, tmp_path, [rel])

    def mutate(row: dict) -> None:
        row["posterior_available"] = True
        row["normalized"] = False

    _mutate_row_keep_flag(root, rel, mutate)
    rows = aggregate_rederivation_rows(root)
    lying = [
        r
        for r in rows
        if r["artifact"] == rel and r["aggregate"] == "all_available_posteriors_normalized"
    ]
    assert lying and not lying[0]["consistent"]


def test_false_flag_over_passing_rows_is_inconsistent(project_root: Path, tmp_path: Path) -> None:
    """Inverse lying case: a False flag over all-passing rows is broken bookkeeping."""
    rel = "output/reports/stale_artifact_report.json"
    root = _isolated_copy(project_root, tmp_path, [rel])
    path = root / rel
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["all_fresh"] = False  # rows untouched (all genuinely fresh)
    path.write_text(json.dumps(payload), encoding="utf-8")
    rows = aggregate_rederivation_rows(root)
    target = [r for r in rows if r["artifact"] == rel and r["aggregate"] == "all_fresh"]
    assert target and not target[0]["consistent"]


def test_empty_rows_with_false_flag_is_consistent() -> None:
    """A legitimately-empty table honestly flagged False must NOT false-positive."""
    payload = {"rows": [], "all_fresh": False}
    rederived = rederive_aggregate(payload, ("true", "fresh"))
    assert rederived is False
    # stored False == re-derived False -> consistent under the strict-equality rule
    assert payload["all_fresh"] == rederived


def test_missing_artifact_fails_closed(tmp_path: Path) -> None:
    rows = aggregate_rederivation_rows(tmp_path)
    assert rows and all(not row["consistent"] for row in rows)
    assert aggregates_consistent(tmp_path) is False


def test_rederivation_logic_single_definition(project_root: Path) -> None:
    """Anti copy-drift: the evaluator and table exist only in gates.aggregate_rederivation."""
    hits = []
    for path in (project_root / "src").rglob("*.py"):
        if path.name == "aggregate_rederivation.py":
            continue
        text = path.read_text(encoding="utf-8")
        if "ARTIFACT_AGGREGATE_RULES" in text and "import" not in text.split("ARTIFACT_AGGREGATE_RULES")[0].rsplit("\n", 2)[-1]:
            hits.append(str(path))
        if "def rederive_aggregate" in text or "def _eval_spec" in text:
            hits.append(str(path))
    assert not hits, f"re-derivation logic duplicated outside canonical module: {hits}"
