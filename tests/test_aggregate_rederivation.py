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
    if kind == "manuscript_fresh":
        return {"fresh"}
    if kind == "figure_hash_current":
        return {"path", "exists", "sha256", "size_bytes", "fresh", "deferred"}
    if kind == "observations_current":
        return {"observed", "receipt_sha256"}
    if kind in {"true", "nonempty", "empty", "positive", "unique"}:
        return {spec[1]}
    if kind == "equals":
        return {spec[1]}
    if kind == "fields_equal":
        return {spec[1], spec[2]}
    if kind == "recompute_ok":
        return {spec[1], "has_forbidden_wording", "is_negated", "allowed"}
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
    spec_unique = ("unique", "key")
    assert rederive_aggregate({"rows": [{"key": "a"}, {"key": "b"}]}, spec_unique) is True
    assert rederive_aggregate({"rows": [{"key": "a"}, {"key": "a"}]}, spec_unique) is False
    assert rederive_aggregate({"rows": [{"key": "a"}, {"key": ""}]}, spec_unique) is False


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


def test_scope_boundary_wording_mutation_caught(project_root: Path, tmp_path: Path) -> None:
    rel = "output/reports/scope_boundary_audit.json"
    scope_spec = ARTIFACT_AGGREGATE_RULES[rel][0][1]
    live_payload = json.loads((project_root / rel).read_text(encoding="utf-8"))
    assert rederive_aggregate(live_payload, scope_spec) is True

    payload = json.loads(json.dumps(live_payload))
    payload["all_current_claims_toy"] = True
    payload["rows"][0] = {
        **payload["rows"][0],
        "has_forbidden_wording": True,
        "is_negated": False,
        "allowed": False,
        "ok": True,
    }

    assert rederive_aggregate(payload, scope_spec) is False

    root = _isolated_copy(project_root, tmp_path, [rel])
    (root / rel).write_text(json.dumps(payload), encoding="utf-8")
    rows = aggregate_rederivation_rows(root)
    lying = [row for row in rows if row["artifact"] == rel and row["aggregate"] == "all_current_claims_toy"]
    assert lying and not lying[0]["consistent"]


def test_scope_boundary_audit_rejects_overbroad_manuscript_claims(tmp_path: Path) -> None:
    from roadmap_tracks.integration_audit_artifacts import build_scope_boundary_audit

    manuscript = tmp_path / "docs" / "manuscript"
    manuscript.mkdir(parents=True)
    overclaims = [
        "OPD = Active Inference.",
        "This paper proves a universal theorem about OPD.",
        "We reproduce Qwen results on production LLMs.",
        "The Markov blanket result proves a biological boundary.",
    ]
    (manuscript / "00_abstract.md").write_text("\n".join(overclaims), encoding="utf-8")

    payload = build_scope_boundary_audit(tmp_path)

    assert payload["scope_boundary_status"] == "scope_leak"
    assert payload["all_current_claims_toy"] is False
    assert len(payload["violations"]) == len(overclaims)
    assert payload["rows"][0]["has_forbidden_wording"] is True


def test_scope_boundary_audit_allows_negated_scope_guardrails(tmp_path: Path) -> None:
    from roadmap_tracks.integration_audit_artifacts import build_scope_boundary_audit

    manuscript = tmp_path / "docs" / "manuscript"
    manuscript.mkdir(parents=True)
    guardrails = [
        "The result is not a universal theorem about OPD.",
        "Qwen and Thinking Machines are external context, not reproduced results.",
        "No biological Markov blanket boundary claim is made.",
    ]
    (manuscript / "00_abstract.md").write_text("\n".join(guardrails), encoding="utf-8")

    payload = build_scope_boundary_audit(tmp_path)

    assert payload["scope_boundary_status"] == "toy_only_pass"
    assert payload["all_current_claims_toy"] is True
    assert payload["violations"] == []
    assert payload["rows"][0]["negated_hits"]


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


def test_manuscript_aggregate_authenticates_honest_red_and_rejects_forgery(tmp_path: Path) -> None:
    from copy import deepcopy
    from gates.output_checks import validate_outputs_selected_strict
    from manuscript.hydrate import write_resolved_manuscript
    from manuscript.variables import generate_variables
    from roadmap_tracks.integration_audit import build_manuscript_staleness_report, validate_manuscript_staleness_report
    from test_manuscript_staleness_regressions import _project

    root = _project(tmp_path, "Count {{pipeline_track_count}}.\n")
    (root / "docs/manuscript/01_plain.md").write_text("An authored token-free section.\n", encoding="utf-8")
    write_resolved_manuscript(root, generate_variables(root, require_analysis_outputs=False))
    path = root / "output/reports/manuscript_staleness_report.json"
    path.parent.mkdir(parents=True)

    def save(payload: dict) -> dict:
        path.write_text(json.dumps(payload), encoding="utf-8")
        return next(row for row in aggregate_rederivation_rows(root) if row["artifact"] == path.relative_to(root).as_posix())

    green = build_manuscript_staleness_report(root)
    assert green["all_fresh"] is True
    assert save(green)["consistent"] is True
    assert validate_outputs_selected_strict(root, {"manuscript_staleness_report_schema"}) == {
        "manuscript_staleness_report_schema": True,
    }
    hydrated = root / "output/manuscript/01_plain.md"
    hydrated.write_text("An unauthorized token-free edit.\n", encoding="utf-8")
    red = build_manuscript_staleness_report(root)
    assert red["rows"] and all(row["fresh"] for row in red["rows"])
    assert any(not section["canonical_hydration_matches"] for section in red["sections"])
    assert red["all_fresh"] is False
    spec = ARTIFACT_AGGREGATE_RULES["output/reports/manuscript_staleness_report.json"][0][1]
    assert rederive_aggregate(red, spec, project_root=root) is False
    row = save(red)
    assert row["consistent"] is True and row["rederived"] is False
    assert validate_manuscript_staleness_report(root, red, require_fresh=False) == []
    assert validate_outputs_selected_strict(root, {"manuscript_staleness_report_schema"}) == {
        "manuscript_staleness_report_schema": False,
    }
    for forge_sections in (False, True):
        forged = deepcopy(red)
        forged["all_fresh"] = True
        if forge_sections:
            for section in forged["sections"]:
                section["canonical_hydration_matches"] = True
        assert save(forged)["consistent"] is False
        assert validate_manuscript_staleness_report(root, forged, require_fresh=False)


def test_unobserved_aggregate_consistency_is_not_release_acceptance(tmp_path: Path) -> None:
    from roadmap_tracks.negative_controls import adversarial_payload, counterexample_payload
    from gates.output_checks import validate_output_payloads

    counter = counterexample_payload(tmp_path)
    adversarial = adversarial_payload(counter)
    for relative, payload in (
        ("output/reports/counterexample_matrix.json", counter),
        ("output/reports/adversarial_audit.json", adversarial),
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
    rows = [row for row in aggregate_rederivation_rows(tmp_path)
            if row["aggregate"] == "all_expected_failures_observed"]
    assert len(rows) == 2 and all(row["consistent"] and row["rederived"] is False for row in rows)
    assert validate_output_payloads(tmp_path, only={"counterexample_matrix_schema", "adversarial_audit_schema"}) == {
        "counterexample_matrix_schema": False, "adversarial_audit_schema": False,
    }
