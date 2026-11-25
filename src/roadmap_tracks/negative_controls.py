"""Registered finite negative controls and explicitly recorded, byte-bound evidence.

Artifact builders only read receipts. Only ``record_negative_controls`` invokes
pytest, once per registered parametrized node, under inherited artifact custody.
A documented mutation is not an observation and a passing combined test is not a
receipt for its constituent cases.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import sysconfig
import tempfile
from copy import deepcopy
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

RECEIPT_SCHEMA = "template_active_inference.negative_control_receipt.v1"
RECEIPT_DIRECTORY = "output/reports/negative_control_receipts"
OBSERVATION_RESTRICTIONS = frozenset(
    {
        "counterexamples_fail_as_expected",
        "adversarial_expected_failures",
        "promotion_controls_observed",
        "adversarial_expected_failures_observed",
    }
)
_RUN_REPORT_ENV = "OPD_NEGATIVE_CONTROL_RUN_REPORT"
_RUN_CASE_ENV = "OPD_NEGATIVE_CONTROL_CASE"
_CASE_NODE = "tests/test_negative_control_receipts.py::test_registered_negative_control"


@dataclass(frozen=True)
class MutationCase:
    id: str
    track: str
    target_gate: str
    mutation: str

    @property
    def nodeid(self) -> str:
        return f"{_CASE_NODE}[{self.id}]"


CASES = (
    MutationCase(
        "missing_sheaf_track_producer",
        "provenance",
        "manuscript.sheaf.semantic.validate_configured_artifact_producers",
        "remove generate_sheaf_tracks.py from the configured producer list",
    ),
    MutationCase(
        "missing_manuscript_binding",
        "sensitivity",
        "validate_manuscript.promoted_sheaf_tracks_bound",
        "remove every sensitivity manuscript binding",
    ),
    MutationCase(
        "missing_typed_claim",
        "evidence_fields",
        "manuscript.sheaf.semantic.validate_canonical_claim_bindings",
        "remove the typed evidence specification from one required canonical artifact claim",
    ),
    MutationCase(
        "stale_semantic_certificate",
        "semantic",
        "manuscript.sheaf.semantic.validate_semantic_snapshot",
        "change a saved artifact producer without changing the live graph",
    ),
    MutationCase(
        "dependency_edge_loss",
        "dependency",
        "validate_outputs.validation_dependency_graph_schema",
        "remove one required dependency edge kind while retaining its green summary",
    ),
    MutationCase(
        "release_bundle_parity_failure",
        "release_bundle",
        "validate_outputs.release_bundle_manifest_schema",
        "change a copied-output parity row while retaining its green summary",
    ),
    MutationCase(
        "replay_mismatch",
        "replay_matrix",
        "validate_outputs.replay_matrix_schema",
        "mark an individual replay comparison unmatched",
    ),
    MutationCase(
        "missing_sensitivity_cell",
        "sensitivity",
        "validate_outputs.sensitivity_sweep_schema",
        "remove a finite grid cell without changing the required grid size",
    ),
    MutationCase(
        "unnormalized_uncertainty_row",
        "uncertainty",
        "validate_outputs.uncertainty_summary_schema",
        "replace a normalized posterior by [0.75, 0.75]",
    ),
    MutationCase(
        "known_bad_counterexample_passed",
        "counterexample",
        "validate_outputs.counterexample_receipts_consistent",
        "claim an unrecorded mutation was observed",
    ),
    MutationCase(
        "missed_model_checking_counterexample",
        "model_checking",
        "validate_outputs.model_checking_witnesses_schema",
        "insert an enumerated finite counterexample while retaining the green summary",
    ),
    MutationCase(
        "interop_shape_loss",
        "interop",
        "validate_outputs.interop_roundtrip_schema",
        "insert a shape difference while retaining the lossless summary",
    ),
    MutationCase(
        "adversarial_known_bad_passes",
        "adversarial_audit",
        "validate_outputs.adversarial_receipts_consistent",
        "claim an unrecorded known-bad mutation passed",
    ),
    MutationCase(
        "theorem_traceability_unlinked",
        "theorem_traceability",
        "validate_outputs.theorem_traceability_matrix_schema",
        "unlink one theorem while retaining the green summary",
    ),
    MutationCase(
        "gate_ergonomics_unindexed",
        "gate_ergonomics",
        "validate_outputs.validation_gate_index_schema",
        "unindex one actual gate while retaining the green summary",
    ),
    MutationCase(
        "artifact_diffoscope_missed_hash_drift",
        "artifact_diffoscope",
        "validate_outputs.artifact_diffoscope_schema",
        "change a live field hash without changing its saved hash",
    ),
    MutationCase(
        "missing_scholarship_source_binding",
        "scholarship",
        "validate_outputs.scholarship_source_matrix_schema",
        "remove a source locator while retaining the connected summary",
    ),
    MutationCase(
        "proof_extraction_missing_statement",
        "proof_extraction",
        "validate_outputs.proof_extraction_index_schema",
        "remove an extracted theorem statement while retaining the inventory",
    ),
    MutationCase(
        "state_space_catalog_missing_finite_space",
        "state_space_catalog",
        "validate_outputs.state_space_catalog_schema",
        "remove finite status from an enumerated state space",
    ),
    MutationCase(
        "causal_ablation_missing_cell",
        "causal_ablation",
        "validate_outputs.causal_ablation_matrix_schema",
        "remove a finite ablation cell without changing the required grid size",
    ),
    MutationCase(
        "artifact_license_unsafe_artifact",
        "artifact_license",
        "validate_outputs.artifact_license_audit_schema",
        "mark an artifact unsafe while retaining the safe summary",
    ),
    MutationCase(
        "release_notes_claim_failed_gate_passed",
        "release_notes",
        "validate_outputs.release_notes_evidence_schema",
        "mark a source-backed release note failed while retaining the green summary",
    ),
    MutationCase(
        "empirical_adapter_live",
        "empirical_adapter",
        "validate_manuscript.blocked_empirical_adapter",
        "add empirical_adapter to the live fragment registry",
    ),
)
_CASES = {case.id: case for case in CASES}


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_object(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_bytes(), object_pairs_hook=_unique_object)
    if not isinstance(result, dict):
        raise ValueError("receipt must be an object")
    return result


def _fixture_payloads() -> dict[str, dict[str, Any]]:
    """Finite validator inputs, not measurements or release certificates."""
    from .sheaf_track_contracts import REQUIRED_EDGE_TYPES

    witnesses = [
        {
            "id": f"double_{n}",
            "model": "finite_nat",
            "exhaustive": True,
            "passed": n + n == 2 * n,
            "counterexamples": [],
        }
        for n in (0, 1)
    ]
    source = "output/data/finite_input.json"
    digest = _digest(canonical_bytes({"states": [0, 1]}))
    return {
        "dependency": {
            "schema": "template_active_inference.validation_dependency_graph.v1",
            "edges": [
                {"source": "finite_input", "target": "finite_consumer", "kind": kind}
                for kind in sorted(REQUIRED_EDGE_TYPES)
            ],
            "required_edge_types": sorted(REQUIRED_EDGE_TYPES),
            "all_required_edge_types_present": True,
        },
        "release_bundle": {
            "schema": "template_active_inference.release_bundle_manifest.v1",
            "rows": [{"artifact": source, "source_exists": True, "deferred_until_render": False}],
            "all_required_sources_present": True,
            "all_copied_outputs_match_or_deferred": True,
            "copied_output_parity": {"rows": [{"artifact": source, "matches_when_copied": True}]},
        },
        "replay_matrix": {
            "schema": "template_active_inference.replay_matrix.v1",
            "configured_scripts": ["finite_enumeration"],
            "rows": [{"producer_script": "finite_enumeration", "matched": [0, 1] == list(range(2))}],
            "all_replay_rows_matched": True,
            "all_configured_producers_represented": True,
        },
        "sensitivity": {
            "schema": "template_active_inference.sensitivity_sweep.v1",
            "rows": [{"lambda": n, "finite_bound_ok": 0 <= n <= 1} for n in (0, 1)],
            "row_count": 2,
            "expected_cells": 2,
            "complete_grid": True,
            "all_finite_bounds_ok": True,
        },
        "uncertainty": {
            "schema": "template_active_inference.uncertainty_summary.v1",
            "rows": [
                {
                    "posterior": [0.5, 0.5],
                    "distribution": [0.5, 0.5],
                    "distribution_sum": 1.0,
                    "normalized": True,
                    "bin": "finite",
                }
            ],
            "bins": {"finite": {}},
            "all_normalized": True,
            "all_bins_valid": True,
        },
        "model_checking": {
            "schema": "template_active_inference.model_checking_witnesses.v1",
            "rows": witnesses,
            "all_exhaustive": True,
            "all_passed": True,
        },
        "interop": {
            "schema": "template_active_inference.interop_roundtrip_report.v1",
            "rows": [{"id": "finite_json", "lossless": json.loads("[0,1]") == [0, 1], "shape_diff": []}],
            "all_lossless": True,
            "all_shape_diffs_empty": True,
        },
        "theorem_traceability": {
            "schema": "template_active_inference.theorem_traceability_matrix.v1",
            "rows": [{"theorem": "double_zero", "linked": True}],
            "all_theorems_linked": True,
        },
        "gate_ergonomics": {
            "schema": "template_active_inference.validation_gate_index.v1",
            "rows": [
                {
                    "gate": "validate_outputs.replay_matrix_schema",
                    "indexed": True,
                    "command": "python scripts/gate.py validate_outputs",
                    "output": source,
                    "failure_modes": ["replay mismatch"],
                    "negative_controls": ["replay_mismatch"],
                    "negative_control": "replay_mismatch",
                }
            ],
            "all_indexed": True,
            "all_rows_fully_specified": True,
        },
        "artifact_diffoscope": {
            "schema": "template_active_inference.artifact_diffoscope.v1",
            "rows": [{"artifact": source, "saved_sha256": digest, "live_sha256": digest, "equal": True}],
            "all_equal": True,
        },
        "scholarship": {
            "schema": "template_active_inference.scholarship_source_matrix.v1",
            "rows": [
                {
                    "source": source,
                    "bib_has_entry": True,
                    "bib_has_locator": True,
                    "cited_in_manuscript": True,
                    "artifact_exists": True,
                    "tracks_registered": True,
                    "sections_bound": True,
                    "claim_boundary": "finite fixture only",
                    "connected": True,
                }
            ],
            "all_sources_connected": True,
            "all_expected_sources_present": True,
        },
        "state_space_catalog": {
            "schema": "template_active_inference.state_space_catalog.v1",
            "rows": [
                {
                    "model": "finite_binary",
                    "finite": True,
                    "state_count": len({0, 1}),
                    "policy_count": len({(0,), (1,)}),
                }
            ],
            "all_finite": True,
            "all_counts_positive": True,
        },
        "causal_ablation": {
            "schema": "template_active_inference.causal_ablation_matrix.v1",
            "rows": [{"input": n, "effect": (1 - n) - n, "deterministic": True} for n in (0, 1)],
            "row_count": 2,
            "expected_cells": 2,
            "complete_grid": True,
            "all_deterministic": True,
        },
        "artifact_license": {
            "schema": "template_active_inference.artifact_license_audit.v1",
            "rows": [{"artifact": source, "license": "CC0-1.0", "license_safe": True}],
            "all_license_safe": True,
        },
        "release_notes": {
            "schema": "template_active_inference.release_notes_evidence.v1",
            "rows": [{"source": source, "passed": [0, 1] == list(range(2))}],
            "all_notes_source_backed": True,
        },
    }


def case_inputs(project_root: Path, case_id: str) -> tuple[dict[str, bytes], dict[str, bytes]]:
    """Return the exact baseline and mutated bytes consumed by a registered node.

    No gate, simulation, pytest run, or receipt recorder is invoked here.
    Observation-consistency cases intentionally start without receipts; this
    avoids making the recorder depend on its own final observation certificate.
    """
    from .sheaf_track_contracts import CANONICAL_ARTIFACTS

    root = project_root.resolve()
    case = _CASES[case_id]
    baseline: dict[str, bytes] = {"output/data/finite_input.json": canonical_bytes({"states": [0, 1]})}
    if case_id in {"missing_sheaf_track_producer", "missing_manuscript_binding", "empirical_adapter_live"}:
        import yaml

        for rel in ("manuscript/config.yaml", "manuscript/sheaf/manifest.yaml", "manuscript/sheaf/tracks.yaml"):
            baseline[rel] = (root / rel).read_bytes()
        mutated = dict(baseline)
        rel = {
            "missing_sheaf_track_producer": "manuscript/config.yaml",
            "missing_manuscript_binding": "manuscript/sheaf/manifest.yaml",
            "empirical_adapter_live": "manuscript/sheaf/tracks.yaml",
        }[case_id]
        payload = yaml.safe_load(baseline[rel])
        if case_id == "missing_sheaf_track_producer":
            payload["analysis"]["scripts"].remove("generate_sheaf_tracks.py")
        elif case_id == "missing_manuscript_binding":
            for section in payload["sections"]:
                (section.get("tracks") or {}).pop("sensitivity", None)
        else:
            payload["tracks"]["empirical_adapter"] = {"order": 999, "renderer": "markdown", "label": "Empirical"}
        mutated[rel] = yaml.safe_dump(payload, sort_keys=True).encode("utf-8")
        return baseline, mutated
    if case_id == "missing_typed_claim":
        import yaml

        rel = "data/claim_ledger.yaml"
        claims = []
        for key, artifact in CANONICAL_ARTIFACTS.items():
            baseline[artifact] = canonical_bytes({"states": [0, 1]})
            claims.append(
                {
                    "id": f"finite_{key}",
                    "statement": "This finite fixture has two states.",
                    "path": artifact,
                    "tracks": [key],
                    "evidence": {"field": "states", "len_equals": 2},
                }
            )
        baseline[rel] = yaml.safe_dump({"claims": claims}).encode("utf-8")
        del claims[0]["evidence"]
        return baseline, {**baseline, rel: yaml.safe_dump({"claims": claims}).encode("utf-8")}
    if case_id == "stale_semantic_certificate":
        import yaml
        from artifact_contracts import ARTIFACT_CONSUMERS, ARTIFACT_GATES, ARTIFACT_PRODUCERS, SEMANTIC_SCHEMA

        baseline["manuscript/config.yaml"] = (root / "manuscript/config.yaml").read_bytes()
        configured = yaml.safe_load(baseline["manuscript/config.yaml"])["analysis"]["scripts"]
        graph = {
            rel: {
                "producer": producer,
                "produced_by_configured_analysis": producer in configured,
                "consumers": list(ARTIFACT_CONSUMERS.get(rel, ())),
                "validation_gates": list(ARTIFACT_GATES.get(rel, ("validate_outputs",))),
                "claim_ids": [],
            }
            for rel, producer in sorted(ARTIFACT_PRODUCERS.items())
        }
        snapshot = {"schema": SEMANTIC_SCHEMA, "artifact_graph": graph}
        baseline["output/data/live_semantic_snapshot.json"] = canonical_bytes(snapshot)
        rel = "output/data/sheaf_gluing_certificate.json"
        baseline[rel] = canonical_bytes(snapshot)
        changed = deepcopy(snapshot)
        first = next(iter(changed["artifact_graph"]))
        changed["artifact_graph"][first]["producer"] = "unconfigured_mutation.py"
        return baseline, {**baseline, rel: canonical_bytes(changed)}
    if case.track in {"counterexample", "adversarial_audit"}:
        # A tiny source fixture with no authored tree needs no runtime snapshot:
        # absent receipts are explicitly unobserved, never green evidence.
        payload = _matrix_from_receipts({}, [])
        if case.track == "adversarial_audit":
            payload = adversarial_payload(payload)
        rel = CANONICAL_ARTIFACTS[case.track]
        baseline[rel] = canonical_bytes(payload)
        changed = deepcopy(payload)
        if case.track == "counterexample":
            changed["rows"][0]["observed"] = "expected_failure"
            changed["rows"][0]["fixture_replay_status"] = "expected_failure_observed"
        else:
            changed["rows"][0]["known_bad_passed"] = True
        return baseline, {**baseline, rel: canonical_bytes(changed)}
    payloads = _fixture_payloads()
    if case.track == "proof_extraction":
        # Literal finite parser fixture: the node independently parses these
        # declarations with the real producer before testing the gate.
        lean_rel = "lean/OnPolicyDistillation/ReceiptFixture.lean"
        baseline[lean_rel] = b"theorem double_zero : (0 : Nat) + 0 = 0 := by\n  rfl\n"
        inventory = {
            "schema": "template_active_inference.lean_theorem_inventory.v1",
            "rows": [{"name": "double_zero", "status": "proved"}],
            "theorem_count": 1,
            "forbidden_tokens": [],
            "all_proved": True,
        }
        payload = {
            "schema": "template_active_inference.proof_extraction_index.v1",
            "rows": [
                {
                    "theorem": "double_zero",
                    "statement": "(0 : Nat) + 0 = 0",
                    "leading_tactic": "rfl",
                    "source": lean_rel,
                    "extracted": True,
                    "forbidden_tokens": [],
                }
            ],
            "theorem_count": 1,
            "inventory_theorem_count": 1,
            "all_inventory_theorems_extracted": True,
            "missing_inventory_theorems": [],
            "extra_extracted_theorems": [],
            "all_extracted": True,
            "all_constructive": True,
        }
        baseline["output/reports/lean_theorem_inventory.json"] = canonical_bytes(inventory)
    else:
        payload = payloads[case.track]
    rel = CANONICAL_ARTIFACTS[case.track]
    baseline[rel] = canonical_bytes(payload)
    changed = deepcopy(payload)
    row = (changed.get("rows") or [{}])[0]
    if case.track == "dependency":
        kind = changed["edges"][0]["kind"]
        changed["edges"] = [edge for edge in changed["edges"] if edge["kind"] != kind]
    elif case.track == "release_bundle":
        changed["copied_output_parity"]["rows"][0]["matches_when_copied"] = False
    elif case.track == "replay_matrix":
        row["matched"] = False
    elif case.track in {"sensitivity", "causal_ablation"}:
        changed["rows"].pop()
        changed["row_count"] = len(changed["rows"])
    elif case.track == "uncertainty":
        row.update({"posterior": [0.75, 0.75], "distribution": [0.75, 0.75], "distribution_sum": 1.5})
    elif case.track == "model_checking":
        row["counterexamples"] = [{"input": 1, "claimed": 3, "actual": 1 + 1}]
    elif case.track == "interop":
        row["shape_diff"] = ["finite vector length changed"]
    elif case.track == "theorem_traceability":
        row["linked"] = False
    elif case.track == "gate_ergonomics":
        row["indexed"] = False
    elif case.track == "artifact_diffoscope":
        row["live_sha256"] = _digest(b"changed finite input")
    elif case.track == "scholarship":
        row["bib_has_locator"] = False
    elif case.track == "proof_extraction":
        row["statement"] = ""
    elif case.track == "state_space_catalog":
        row["finite"] = False
    elif case.track == "artifact_license":
        row["license_safe"] = False
    elif case.track == "release_notes":
        row["passed"] = False
    return baseline, {**baseline, rel: canonical_bytes(changed)}


def input_binding(files: dict[str, bytes]) -> dict[str, str]:
    return {path: _digest(raw) for path, raw in sorted(files.items())}


def case_definition(case: MutationCase) -> dict[str, Any]:
    return {**asdict(case), "nodeid": case.nodeid}


def authored_binding(project_root: Path) -> dict[str, str]:
    root = project_root.resolve()
    paths: set[Path] = set()
    for directory in ("src", "tests", "scripts", "gnn", "lean", "data", "manuscript/sheaf", "manuscript/sections"):
        paths.update(
            path
            for path in (root / directory).rglob("*")
            if path.is_file()
            and not {"__pycache__", ".lake", ".venv"}.intersection(path.parts)
            and path.suffix not in {".pyc", ".png", ".gif"}
        )
    paths.update(
        path
        for path in root.iterdir()
        if path.is_file() and (path.suffix in {".yaml", ".toml", ".lock"} or path.name == "conftest.py")
    )
    if not paths:
        raise ValueError("negative-control evidence requires the authored source/test/config tree")
    paths.add(root / "manuscript" / "config.yaml")
    return {path.relative_to(root).as_posix(): _file_digest(path) for path in sorted(paths)}


def runtime_binding() -> dict[str, Any]:
    """Bind executable, standard-library and installed dependency bytes, not versions alone."""
    files: set[Path] = {Path(sys.executable).resolve(strict=True)}
    library_directory = sysconfig.get_config_var("LIBDIR")
    library_name = sysconfig.get_config_var("LDLIBRARY")
    if library_directory and library_name:
        library = Path(library_directory) / library_name
        if library.is_file():
            files.add(library.resolve())
    stdlib = Path(sysconfig.get_path("stdlib"))
    files.update(
        path
        for path in stdlib.rglob("*")
        if path.is_file()
        and not {"site-packages", "__pycache__", "test", "tests"}.intersection(path.parts)
        and path.suffix != ".pyc"
    )
    distributions = []
    for distribution in importlib.metadata.distributions():
        distributions.append((distribution.metadata["Name"], distribution.version))
        for entry in distribution.files or []:
            path = Path(distribution.locate_file(entry))
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                files.add(path.resolve())
    hashes = {str(path): _file_digest(path) for path in sorted(files)}
    return {
        "executable": str(Path(sys.executable).absolute()),
        "version": sys.version,
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "prefix": sys.prefix,
        "base_prefix": sys.base_prefix,
        "distributions": sorted(distributions),
        "files": hashes,
    }


def evidence_binding(project_root: Path) -> dict[str, Any]:
    authored = authored_binding(project_root)
    source = {
        path: digest for path, digest in authored.items() if path.startswith(("src/", "scripts/", "gnn/", "lean/"))
    }
    tests = {path: digest for path, digest in authored.items() if path.startswith("tests/") or path == "conftest.py"}
    config = {path: digest for path, digest in authored.items() if path not in source and path not in tests}
    return {
        "authored_sha256": _digest(canonical_bytes(authored)),
        "source_sha256": _digest(canonical_bytes(source)),
        "test_sha256": _digest(canonical_bytes(tests)),
        "config_sha256": _digest(canonical_bytes(config)),
        "runtime_sha256": _digest(canonical_bytes(runtime_binding())),
    }


def _receipt_issues(
    case: MutationCase,
    receipt: dict[str, Any],
    binding: dict[str, Any],
    baseline: dict[str, str],
    mutated: dict[str, str],
) -> list[str]:
    expected = {
        "schema": RECEIPT_SCHEMA,
        "case": case_definition(case),
        "binding": binding,
        "fixture": baseline,
        "input": mutated,
    }
    issues = [
        f"{case.id}: stale or forged {key}"
        for key, value in expected.items()
        if canonical_bytes(receipt.get(key)) != canonical_bytes(value)
    ]
    run = receipt.get("run")
    result = receipt.get("result")
    if not isinstance(run, dict) or not isinstance(result, dict):
        return issues + [f"{case.id}: missing process or assertion result object"]
    reports = run.get("reports")
    if not isinstance(reports, list) or any(not isinstance(row, dict) for row in reports):
        return issues + [f"{case.id}: malformed pytest phase reports"]
    if (
        type(run.get("returncode")) is not int
        or run["returncode"] != 0
        or type(run.get("exitstatus")) is not int
        or run["exitstatus"] != 0
        or run.get("collected") != [case.nodeid]
        or len(reports) != 3
        or {(row.get("nodeid"), row.get("when"), row.get("outcome")) for row in reports}
        != {(case.nodeid, phase, "passed") for phase in ("setup", "call", "teardown")}
    ):
        issues.append(f"{case.id}: no successful exclusive per-case pytest run")
    if (
        result.get("case_id") != case.id
        or result.get("target_gate") != case.target_gate
        or result.get("fixture") != baseline
        or result.get("input") != mutated
        or result.get("baseline_accepted") is not True
        or result.get("target_rejected") is not True
        or result.get("mutation_accepted") is not False
        or result.get("assertion_passed") is not True
        or not result.get("rejection")
    ):
        issues.append(f"{case.id}: missing successful target-specific acceptance/rejection assertions")
    if result.get("baseline_result") != {"target_gate": case.target_gate, "accepted": True}:
        issues.append(f"{case.id}: baseline target did not accept")
    if result.get("rejection") != {"target_gate": case.target_gate, "accepted": False}:
        issues.append(f"{case.id}: wrong target rejection")
    for field in ("stdout", "stderr"):
        raw = run.get(field)
        if not isinstance(raw, str) or run.get(f"{field}_sha256") != _digest(raw.encode("utf-8")):
            issues.append(f"{case.id}: missing or forged actual process {field}")
    return issues


def load_receipts(project_root: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    root = project_root.resolve()
    receipts: dict[str, dict[str, Any]] = {}
    issues: list[str] = []
    paths = sorted((root / RECEIPT_DIRECTORY).glob("*.json"))
    if not paths:
        return receipts, issues
    try:
        binding = evidence_binding(root)
    except (OSError, ValueError, TypeError) as exc:
        return {}, [f"negative-control current source/runtime binding unavailable: {exc}"]
    seen: set[str] = set()
    for path in paths:
        try:
            receipt = _read_object(path)
            definition = receipt.get("case")
            if not isinstance(definition, dict):
                raise ValueError("missing registered case definition")
            case_id = definition.get("id")
            if case_id not in _CASES:
                raise ValueError("unknown negative-control case")
            if case_id in seen:
                receipts.pop(case_id, None)
                raise ValueError(f"duplicate receipt for {case_id}")
            seen.add(case_id)
            if path.name != f"{case_id}.json":
                raise ValueError(f"receipt filename does not bind {case_id}")
            before, after = case_inputs(root, case_id)
            case_issues = _receipt_issues(
                _CASES[case_id], receipt, binding, input_binding(before), input_binding(after)
            )
            if case_issues:
                issues.extend(case_issues)
            else:
                receipts[case_id] = receipt
        except (OSError, ValueError, KeyError, TypeError) as exc:
            issues.append(f"{path.name}: invalid negative-control receipt: {exc}")
    return receipts, issues


def counterexample_payload(project_root: Path) -> dict[str, Any]:
    """Read existing evidence; never launch a test or infer an observation."""
    return _matrix_from_receipts(*load_receipts(project_root.resolve()))


def _matrix_from_receipts(current: dict[str, dict[str, Any]], issues: list[str]) -> dict[str, Any]:
    from .sheaf_track_contracts import CANONICAL_TRACKS

    rows = []
    for case in CASES:
        receipt = current.get(case.id)
        rows.append(
            {
                "id": case.id,
                "promoted_track": case.track,
                "gate": case.target_gate,
                "target_gate": case.target_gate,
                "mutation": case.mutation,
                "case": case_definition(case),
                "expected_failure": True,
                "test": case.nodeid,
                "observed": "expected_failure" if receipt else "unobserved",
                "fixture_replay_status": "expected_failure_observed" if receipt else "unobserved",
                "receipt": receipt,
                "receipt_sha256": _digest(canonical_bytes(receipt)) if receipt else "",
            }
        )
    observed = sum(row["receipt"] is not None for row in rows)
    return {
        "schema": "template_active_inference.counterexample_matrix.v1",
        "schema_version": "template_active_inference.canonical_sheaf_tracks.v1",
        "rows": rows,
        "counterexample_count": len(rows),
        "observed_count": observed,
        "unobserved_count": len(rows) - observed,
        "receipt_issues": issues,
        "covered_tracks": sorted({case.track for case in CASES} & set(CANONICAL_TRACKS)),
        "all_expected_failures_documented": bool(rows),
        "all_expected_failures_observed": bool(rows) and observed == len(rows) and not issues,
    }


def adversarial_payload(counter: dict[str, Any]) -> dict[str, Any]:
    rows = [
        {
            "id": row["id"],
            "track": row["promoted_track"],
            "target_gate": row["target_gate"],
            "gate": row["gate"],
            "test": row["test"],
            "known_bad_should_fail": True,
            "known_bad_passed": row["receipt"]["result"]["mutation_accepted"] if row["receipt"] else None,
            "expected_failure": True,
            "observed": row["observed"],
            "receipt_sha256": row["receipt_sha256"],
        }
        for row in counter["rows"]
    ]
    return {
        "schema": "template_active_inference.adversarial_audit.v1",
        "schema_version": counter["schema_version"],
        "rows": rows,
        "audit_count": len(rows),
        "probe_count": len(rows),
        "observed_count": counter["observed_count"],
        "unobserved_count": counter["unobserved_count"],
        "receipt_issues": counter["receipt_issues"],
        "known_bad_rows_passed": sum(row["known_bad_passed"] is True for row in rows),
        "all_expected_failures_documented": counter["all_expected_failures_documented"],
        "all_expected_failures_observed": counter["all_expected_failures_observed"],
    }


def validate_observation_payload(
    project_root: Path, payload: dict[str, Any], *, adversarial: bool = False, require_observations: bool = True
) -> list[str]:
    expected = counterexample_payload(project_root)
    if adversarial:
        expected = adversarial_payload(expected)
    name = "adversarial_audit.json" if adversarial else "counterexample_matrix.json"
    issues = list(expected["receipt_issues"])
    if isinstance(payload, dict) and payload.get("all_expected_failures_documented") is not True:
        issues.append(f"{name} has undocumented expected failures")
    if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        for row in payload["rows"]:
            if isinstance(row, dict) and row.get("expected_failure") is not True:
                issues.append(f"{row.get('id', '<unknown>')}: expected_failure must be true")
    try:
        if canonical_bytes(payload) != canonical_bytes(expected):
            issues.append(f"{name} is inconsistent with the registered cases and current receipts")
    except (ValueError, TypeError):
        issues.append(f"{name} has malformed receipt data")
    if require_observations and expected["all_expected_failures_observed"] is not True:
        issues.append(f"{name} requires successful current per-case observations")
    return issues


# Pytest loads this module as an explicit plugin only in recorder subprocesses.
_RUN_REPORTS: list[dict[str, Any]] = []
_RUN_RESULTS: list[Any] = []


def pytest_runtest_logreport(report: Any) -> None:
    if not os.environ.get(_RUN_REPORT_ENV):
        return
    _RUN_REPORTS.append({"nodeid": report.nodeid, "when": report.when, "outcome": report.outcome})
    if report.when == "call":
        _RUN_RESULTS.extend(value for key, value in report.user_properties if key == "negative_control_result")


def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    destination = os.environ.get(_RUN_REPORT_ENV)
    if destination:
        Path(destination).write_bytes(
            canonical_bytes(
                {
                    "exitstatus": int(exitstatus),
                    "collected": [item.nodeid for item in session.items],
                    "reports": _RUN_REPORTS,
                    "results": _RUN_RESULTS,
                }
            )
        )


def record_negative_controls(
    project_root: Path, *, case_ids: tuple[str, ...] | None = None, inherited: str | None = None
) -> dict[str, Path]:
    """Execute isolated nodes; nonpassing attempts can never leave a prior green receipt current."""
    from orchestration.artifact_lock import artifact_lease

    root = project_root.resolve()
    selected = tuple(_CASES) if case_ids is None else case_ids
    if not selected or len(selected) != len(set(selected)) or any(case_id not in _CASES for case_id in selected):
        raise ValueError("recording requires unique registered case IDs")
    written: dict[str, Path] = {}
    with artifact_lease(root, inherited=inherited) as lease:
        before_binding = evidence_binding(root)
        pending: dict[str, dict[str, Any]] = {}
        with tempfile.TemporaryDirectory(prefix="opd-negative-controls-") as directory:
            for case_id in selected:
                case = _CASES[case_id]
                baseline, mutated = case_inputs(root, case_id)
                report_path = Path(directory) / f"{case_id}.json"
                handoff = lease.handoff()
                environment = dict(handoff.env)
                environment.pop("PYTEST_ADDOPTS", None)
                environment.update(
                    {
                        _RUN_REPORT_ENV: str(report_path),
                        _RUN_CASE_ENV: case_id,
                        "PYTHONPATH": os.pathsep.join((str(root / "src"), str(root / "tests"))),
                        "PYTHONDONTWRITEBYTECODE": "1",
                        # Execute the hashed Python sources, not a
                        # pre-existing unbound bytecode cache.
                        "PYTHONPYCACHEPREFIX": str(Path(directory) / "pycache"),
                    }
                )
                process = subprocess.run(
                    [
                        sys.executable,
                        "-B",
                        "-m",
                        "pytest",
                        "-q",
                        "-p",
                        "roadmap_tracks.negative_controls",
                        "-p",
                        "no:cacheprovider",
                        "--no-cov",
                        case.nodeid,
                    ],
                    cwd=root,
                    env=environment,
                    pass_fds=handoff.pass_fds,
                    capture_output=True,
                    check=False,
                )
                try:
                    run = _read_object(report_path)
                except (OSError, ValueError) as exc:
                    run = {"report_error": str(exc)}
                results = run.pop("results", [])
                result = results[0] if isinstance(results, list) and len(results) == 1 else None
                stdout = process.stdout.decode("utf-8", errors="replace")
                stderr = process.stderr.decode("utf-8", errors="replace")
                run.update(
                    {
                        "returncode": process.returncode,
                        "stdout": stdout,
                        "stderr": stderr,
                        "stdout_sha256": _digest(stdout.encode("utf-8")),
                        "stderr_sha256": _digest(stderr.encode("utf-8")),
                    }
                )
                receipt = {
                    "schema": RECEIPT_SCHEMA,
                    "case": case_definition(case),
                    "binding": before_binding,
                    "fixture": input_binding(baseline),
                    "input": input_binding(mutated),
                    "run": run,
                    "result": result,
                }
                problems = _receipt_issues(
                    case, receipt, before_binding, input_binding(baseline), input_binding(mutated)
                )
                if problems:
                    # Persist the actual nonpassing attempt, not a success
                    # certificate. It supersedes any old success for this case;
                    # otherwise a failed rerun could silently leave a green row.
                    destination = root / RECEIPT_DIRECTORY / f"{case_id}.json"
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(canonical_bytes(receipt))
                    raise RuntimeError(f"negative-control node did not pass: {case.nodeid}; " + "; ".join(problems))
                pending[case_id] = receipt
        if evidence_binding(root) != before_binding:
            raise RuntimeError("authored or runtime bytes changed during recording; no current receipt published")
        for case_id, receipt in pending.items():
            destination = root / RECEIPT_DIRECTORY / f"{case_id}.json"
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(canonical_bytes(receipt))
            written[case_id] = destination
    return written
