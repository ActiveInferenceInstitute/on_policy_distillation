"""Real finite target rejections and explicit per-node receipt recording regressions."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

from orchestration.artifact_lock import artifact_lease
from roadmap_tracks.negative_controls import (
    CASES,
    RECEIPT_DIRECTORY,
    MutationCase,
    canonical_bytes,
    case_inputs,
    counterexample_payload,
    input_binding,
    load_receipts,
    record_negative_controls,
    validate_observation_payload,
)


def _load(root: Path, relative: str) -> dict:
    return json.loads((root / relative).read_bytes())


def _install(root: Path, files: dict[str, bytes]) -> None:
    for relative, raw in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)


def _target(case: MutationCase, root: Path) -> dict:
    """Call the registered real validator, never a substitute or overall red gate."""
    if case.target_gate.startswith("validate_outputs."):
        from gates.output_checks import validate_outputs_selected_strict

        key = case.target_gate.removeprefix("validate_outputs.")
        checks = validate_outputs_selected_strict(root, {key})
        assert set(checks) == {key}
        accepted = checks[key]
    elif case.target_gate.startswith("validate_manuscript."):
        from gates.manuscript_checks import validate_manuscript_selected_strict

        key = case.target_gate.removeprefix("validate_manuscript.")
        checks = validate_manuscript_selected_strict(root, {key})
        assert set(checks) == {key}
        accepted = checks[key]
    elif case.id == "missing_sheaf_track_producer":
        from manuscript.sheaf.semantic import validate_configured_artifact_producers

        accepted = not validate_configured_artifact_producers(root)
    elif case.id == "missing_typed_claim":
        from manuscript.sheaf.semantic import validate_canonical_claim_bindings

        accepted = not validate_canonical_claim_bindings(root)
    elif case.id == "stale_semantic_certificate":
        from manuscript.sheaf.semantic import validate_semantic_snapshot

        accepted = not validate_semantic_snapshot(
            _load(root, "output/data/sheaf_gluing_certificate.json"),
            _load(root, "output/data/live_semantic_snapshot.json"),
        )
    else:
        raise AssertionError(f"unimplemented registered target: {case.target_gate}")
    return {"target_gate": case.target_gate, "accepted": accepted}


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.id)
def test_registered_negative_control(
    project_root: Path, tmp_path: Path, request: pytest.FixtureRequest, record_property, case: MutationCase,
) -> None:
    """One actual node establishes its own baseline acceptance and target rejection."""
    assert request.node.nodeid == case.nodeid
    requested = os.environ.get("OPD_NEGATIVE_CONTROL_CASE")
    assert requested is None or requested == case.id
    baseline, mutated = case_inputs(project_root, case.id)
    root = tmp_path / "finite_case"
    root.mkdir()
    with artifact_lease(root):
        _install(root, baseline)
        actual_baseline = {relative: (root / relative).read_bytes() for relative in baseline}
        assert actual_baseline == baseline
        if case.track == "proof_extraction":
            from roadmap_tracks.formal_interop import build_lean_theorem_inventory, build_proof_extraction_index

            assert build_proof_extraction_index(root) == _load(root, "output/data/proof_extraction_index.json")
            assert build_lean_theorem_inventory(root) == _load(root, "output/reports/lean_theorem_inventory.json")
        before = _target(case, root)
        assert before["accepted"] is True, (case.id, before)
        _install(root, mutated)
        actual_input = {relative: (root / relative).read_bytes() for relative in mutated}
        assert actual_input == mutated and actual_input != actual_baseline
        after = _target(case, root)
        assert after["accepted"] is False, (case.id, after)
    record_property("negative_control_result", {
        "case_id": case.id, "target_gate": case.target_gate,
        "fixture": input_binding(actual_baseline), "input": input_binding(actual_input),
        "baseline_accepted": before["accepted"], "baseline_result": before,
        "mutation_accepted": after["accepted"], "target_rejected": not after["accepted"],
        "rejection": after, "assertion_passed": True,
    })


def test_missing_receipts_are_documented_not_observed(tmp_path: Path) -> None:
    from gates.output_checks import validate_output_payloads
    from roadmap_tracks.sheaf_tracks import build_adversarial_audit, build_counterexample_matrix
    from validation_spine.artifacts import build_counterexample_matrix as spine_counterexample

    counter = build_counterexample_matrix(tmp_path)
    adversarial = build_adversarial_audit(tmp_path)
    assert counter == spine_counterexample(tmp_path)
    assert counter["counterexample_count"] == len(CASES)
    assert counter["observed_count"] == adversarial["observed_count"] == 0
    assert counter["unobserved_count"] == adversarial["unobserved_count"] == len(CASES)
    assert counter["all_expected_failures_documented"] is True
    assert counter["all_expected_failures_observed"] is adversarial["all_expected_failures_observed"] is False
    assert all(row["receipt"] is None and row["observed"] == "unobserved" for row in counter["rows"])
    assert all(row["known_bad_passed"] is None for row in adversarial["rows"])
    assert validate_observation_payload(tmp_path, counter, require_observations=False) == []
    assert validate_observation_payload(tmp_path, counter)
    assert validate_observation_payload(tmp_path, adversarial, adversarial=True, require_observations=False) == []
    checks = validate_output_payloads(tmp_path, {"counterexample": counter, "adversarial_audit": adversarial}, only={
        "counterexample_matrix_schema", "counterexample_receipts_consistent",
        "adversarial_audit_schema", "adversarial_receipts_consistent",
    })
    assert checks == {"counterexample_matrix_schema": False, "counterexample_receipts_consistent": True,
                      "adversarial_audit_schema": False, "adversarial_receipts_consistent": True}
    assert build_counterexample_matrix(tmp_path) == counter


def _copy_authored(project_root: Path, destination: Path) -> Path:
    destination.mkdir()
    for name in ("src", "tests", "scripts", "gnn", "lean", "data", "manuscript"):
        shutil.copytree(project_root / name, destination / name,
                        ignore=shutil.ignore_patterns("__pycache__", ".lake", ".venv", "*.pyc"))
    for path in project_root.iterdir():
        if path.is_file() and (path.suffix in {".yaml", ".toml", ".lock"} or path.name == "conftest.py"):
            shutil.copy2(path, destination / path.name)
    return destination


@pytest.fixture(scope="module")
def recorded_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Genuine recorder runs; no fabricated green receipts or mocked callbacks."""
    source = Path(__file__).resolve().parents[1]
    root = _copy_authored(source, tmp_path_factory.mktemp("receipt_parent") / "source")
    paths = record_negative_controls(root)
    assert set(paths) == {case.id for case in CASES}
    receipts, issues = load_receipts(root)
    assert issues == [] and set(receipts) == set(paths)
    return root


@pytest.mark.artifact_slow
def test_recorder_certifies_each_actual_parametrized_node(recorded_root: Path) -> None:
    counter = counterexample_payload(recorded_root)
    assert counter["observed_count"] == len(CASES)
    assert counter["all_expected_failures_observed"] is True
    assert validate_observation_payload(recorded_root, counter) == []
    for case, row in zip(CASES, counter["rows"], strict=True):
        receipt = row["receipt"]
        assert receipt["run"]["collected"] == [case.nodeid]
        assert all(report["nodeid"] == case.nodeid and report["outcome"] == "passed"
                   for report in receipt["run"]["reports"])
        assert receipt["result"]["baseline_result"] == {"target_gate": case.target_gate, "accepted": True}
        assert receipt["result"]["rejection"] == {"target_gate": case.target_gate, "accepted": False}


_RECEIPT_FORGERIES = (
    "source", "test", "config", "runtime", "fixture", "input", "mutation", "nodeid", "wronggate",
    "rejection", "assertion", "baseline", "test_result", "failed_process", "failed_session",
    "failed_phase", "skipped_phase", "missing_phase", "combined_test", "stdout",
)


@pytest.mark.artifact_slow
@pytest.mark.parametrize("forgery", _RECEIPT_FORGERIES)
def test_forged_or_failed_receipt_never_certifies_a_case(
    recorded_root: Path, tmp_path: Path, forgery: str,
) -> None:
    root = tmp_path / "source"
    shutil.copytree(recorded_root, root)
    case = CASES[0]
    path = root / RECEIPT_DIRECTORY / f"{case.id}.json"
    receipt = json.loads(path.read_bytes())
    if forgery in {"source", "test", "config", "runtime"}:
        receipt["binding"][f"{forgery}_sha256"] = "0" * 64
    elif forgery in {"fixture", "input"}:
        receipt[forgery][next(iter(receipt[forgery]))] = "0" * 64
    elif forgery in {"mutation", "nodeid"}:
        receipt["case"][forgery] = "changed mutation or unrelated test"
    elif forgery == "wronggate":
        receipt["case"]["target_gate"] = "validate_outputs.unrelated_gate"
        receipt["result"]["target_gate"] = "validate_outputs.unrelated_gate"
    elif forgery == "rejection":
        receipt["result"]["rejection"] = {"target_gate": "unrelated_gate", "accepted": False}
    elif forgery == "assertion":
        receipt["result"]["assertion_passed"] = False
    elif forgery == "baseline":
        receipt["result"]["baseline_accepted"] = False
    elif forgery == "test_result":
        receipt["result"]["mutation_accepted"] = True
    elif forgery == "failed_process":
        receipt["run"]["returncode"] = 1
    elif forgery == "failed_session":
        receipt["run"]["exitstatus"] = 1
    elif forgery in {"failed_phase", "skipped_phase"}:
        receipt["run"]["reports"][1]["outcome"] = "failed" if forgery == "failed_phase" else "skipped"
    elif forgery == "missing_phase":
        receipt["run"]["reports"].pop()
    elif forgery == "combined_test":
        receipt["run"]["collected"] = ["tests/test_track_consolidation.py::test_canonical_sheaf_negative_controls"]
    else:
        receipt["run"]["stdout"] += "forged output"
    path.write_bytes(canonical_bytes(receipt))
    counter = counterexample_payload(root)
    row = next(row for row in counter["rows"] if row["id"] == case.id)
    assert row["receipt"] is None and row["observed"] == "unobserved"
    assert counter["all_expected_failures_observed"] is False
    assert counter["receipt_issues"]
    assert validate_observation_payload(root, counter)


@pytest.mark.artifact_slow
@pytest.mark.parametrize("relative", ["src/roadmap_tracks/negative_controls.py",
                                      "tests/test_negative_control_receipts.py", "manuscript/config.yaml"])
def test_changed_authored_bytes_require_new_evidence(recorded_root: Path, tmp_path: Path, relative: str) -> None:
    root = tmp_path / "source"
    shutil.copytree(recorded_root, root)
    path = root / relative
    path.write_bytes(path.read_bytes() + b"\n# changed authored mutation/test/config bytes\n")
    payload = counterexample_payload(root)
    assert payload["observed_count"] == 0
    assert payload["receipt_issues"] and payload["all_expected_failures_observed"] is False


@pytest.mark.artifact_slow
@pytest.mark.parametrize("problem", ["unknown", "duplicate", "missing", "duplicate_json_key"])
def test_receipt_domain_is_exact(recorded_root: Path, tmp_path: Path, problem: str) -> None:
    root = tmp_path / "source"
    shutil.copytree(recorded_root, root)
    case = CASES[0]
    path = root / RECEIPT_DIRECTORY / f"{case.id}.json"
    if problem == "missing":
        path.unlink()
    elif problem == "duplicate_json_key":
        raw = path.read_text()
        path.write_text('{"schema":"forged",' + raw[1:], encoding="utf-8")
    else:
        payload = json.loads(path.read_bytes())
        if problem == "unknown":
            payload["case"]["id"] = "unregistered"
        (path.parent / f"{problem}.json").write_bytes(canonical_bytes(payload))
    payload = counterexample_payload(root)
    assert payload["all_expected_failures_observed"] is False
    if problem != "missing":
        assert payload["receipt_issues"]
    if problem != "unknown":
        assert next(row for row in payload["rows"] if row["id"] == case.id)["receipt"] is None


@pytest.mark.artifact_slow
@pytest.mark.parametrize("outcome", ["failed", "skipped"])
def test_actual_nonpassing_rerun_cannot_leave_prior_success_current(
    project_root: Path, tmp_path: Path, outcome: str,
) -> None:
    root = _copy_authored(project_root, tmp_path / "source")
    test_file = root / "tests/test_negative_control_receipts.py"
    test_file.write_text(test_file.read_text() + (
        "\n\n@pytest.fixture(autouse=True)\ndef force_nonpassing_receipt_run():\n"
        "    outcome = os.environ.get('OPD_RECEIPT_NONPASSING')\n"
        "    if outcome == 'failed':\n        assert False, 'intentional recorder failure'\n"
        "    if outcome == 'skipped':\n        pytest.skip('intentional recorder skip')\n"
    ), encoding="utf-8")
    previous = os.environ.pop("OPD_RECEIPT_NONPASSING", None)
    try:
        record_negative_controls(root, case_ids=(CASES[0].id,))
        assert set(load_receipts(root)[0]) == {CASES[0].id}
        os.environ["OPD_RECEIPT_NONPASSING"] = outcome
        with pytest.raises(RuntimeError, match="did not pass"):
            record_negative_controls(root, case_ids=(CASES[0].id,))
    finally:
        if previous is None:
            os.environ.pop("OPD_RECEIPT_NONPASSING", None)
        else:
            os.environ["OPD_RECEIPT_NONPASSING"] = previous
    successful, issues = load_receipts(root)
    assert successful == {} and issues
    assert counterexample_payload(root)["observed_count"] == 0


@pytest.mark.artifact_slow
@pytest.mark.timeout(600)
def test_strict_integration_audit_rejects_removed_current_observation(
    recorded_root: Path, tmp_path: Path,
) -> None:
    from gate_support import ensure_gate_artifacts
    from gates.output_checks import validate_outputs_selected_strict
    from orchestration.artifact_pipeline import hydrate_manuscript_fixed_point
    from roadmap_tracks.integration_audit import validate_integration_audit_artifacts

    root = tmp_path / "source"
    shutil.copytree(recorded_root, root)
    ensure_gate_artifacts(root)
    observation_issue = "adversarial_audit.json requires successful current per-case observations"
    assert counterexample_payload(root)["observed_count"] == len(CASES)
    assert observation_issue not in validate_integration_audit_artifacts(root)
    assert validate_integration_audit_artifacts(root, require_release_evidence=False) == []

    (root / RECEIPT_DIRECTORY / f"{CASES[0].id}.json").unlink()
    hydrate_manuscript_fixed_point(root, require_analysis_outputs=False)

    assert counterexample_payload(root)["observed_count"] == len(CASES) - 1
    assert observation_issue in validate_integration_audit_artifacts(root)
    assert validate_integration_audit_artifacts(root, require_release_evidence=False) == []
    key = "integration_audit_track_schemas"
    assert validate_outputs_selected_strict(root, {key}) == {key: False}
    assert validate_outputs_selected_strict(root, {key}, require_observations=False) == {key: True}
