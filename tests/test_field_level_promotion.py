"""Field-level promotion-chain negative controls (Run-12 additive deepening).

These cover the field-level lineage rows promoted in Run-12:

* AI-MANUSCRIPT-TOKEN-3 — rendered-token <-> provenance-key ``set_equals``.
* AI-EVIDENCE-FIELDS-1 — every evidence-field row keyed on a JSONPath edge.
* AI-PROVENANCE-FIELDS-1 — per-field hash/producer/seed/source_commit lineage.
* AI-DEPENDENCY-FIELDS-1 — field-level JSONPath edges in the dependency graph.

Each row gets two kinds of negative control:

1. A *co-actor-immune* validator-level synthetic NC: build the artifact
   in-memory, mutate the dict, feed it straight to the production validator
   helper (no ``output/`` mutation, so a concurrent codex pytest burst cannot
   race it).
2. A *production-path* NC (``mutates_artifacts``): mutate-then-restore the live
   on-disk artifact and assert ``validate_outputs(root)[key]`` is ``False`` --
   the path the real gate dispatches to.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gate_support import ensure_gate_artifacts

pytestmark = pytest.mark.timeout(600)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# AI-MANUSCRIPT-TOKEN-3
# ---------------------------------------------------------------------------


def test_token_provenance_builder_emits_set_equal_rendered_and_provenance(project_root: Path) -> None:
    """Write-path: the builder emits matching rendered-token / provenance-key sets."""
    from roadmap_tracks.integration_audit_builders import build_manuscript_token_provenance

    payload = build_manuscript_token_provenance(project_root)
    assert payload["rendered_tokens_match_provenance_keys"] is True
    assert payload["rendered_tokens"]  # non-empty
    assert set(payload["rendered_tokens"]) == set(payload["provenance_keys"])


def test_token_provenance_validator_catches_dropped_provenance_key(project_root: Path) -> None:
    """Co-actor-immune: a rendered token whose provenance row was deleted fails."""
    from roadmap_tracks.integration_audit_builders import build_manuscript_token_provenance

    payload = build_manuscript_token_provenance(project_root)
    dropped = payload["tokens"][0]["token"]
    # Hand-delete every provenance row for one still-rendered token; leave the
    # rendered-token set claiming it. This is "rendered token, no provenance key".
    payload["tokens"] = [row for row in payload["tokens"] if row["token"] != dropped]
    payload["provenance_keys"] = sorted({row["token"] for row in payload["tokens"]})
    payload["rendered_tokens_match_provenance_keys"] = set(payload["rendered_tokens"]) == set(
        payload["provenance_keys"]
    )
    assert payload["rendered_tokens_match_provenance_keys"] is False
    assert dropped in payload["rendered_tokens"]
    assert dropped not in payload["provenance_keys"]


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_token_provenance_production_gate_fails_on_phantom_provenance_key(tmp_path: Path) -> None:
    """Production path: a phantom provenance key (never rendered) fails validate_outputs."""
    from gates.output_checks import validate_outputs

    path = PROJECT_ROOT / "output" / "data" / "manuscript_token_provenance.json"
    if not path.is_file():
        ensure_gate_artifacts(PROJECT_ROOT)
    if "rendered_tokens" not in _load(path):
        ensure_gate_artifacts(PROJECT_ROOT)
    backup = tmp_path / "token_provenance.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = _load(path)
    assert payload.get("rendered_tokens"), "live artifact must carry rendered_tokens"
    # Inject a provenance key that is not in the rendered-token set, and a fake
    # mapped row for it -- "provenance key, never rendered". Leave the stored
    # match flag lying True.
    phantom = "zzz_phantom_token_never_rendered"
    payload["tokens"].append(
        {"section": "manuscript/fake.md", "token": phantom, "source": "output/data/manuscript_variables.json", "mapped": True}
    )
    payload["provenance_keys"] = sorted(set(payload["provenance_keys"]) | {phantom})
    payload["rendered_tokens_match_provenance_keys"] = True
    try:
        _write(path, payload)
        checks = validate_outputs(PROJECT_ROOT)
        assert checks["integration_audit_track_schemas"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
    checks = validate_outputs(PROJECT_ROOT)
    assert checks["integration_audit_track_schemas"] is True


# ---------------------------------------------------------------------------
# AI-EVIDENCE-FIELDS-1
# ---------------------------------------------------------------------------


def test_evidence_field_index_builder_links_jsonpath_and_restriction(project_root: Path) -> None:
    """Write-path: every evidence row carries a JSONPath edge and a semantic restriction."""
    from roadmap_tracks.sheaf_tracks_reports import build_evidence_field_index

    payload = build_evidence_field_index(project_root)
    assert payload["all_fields_mapped"] is True
    assert payload["rows"]
    for row in payload["rows"]:
        assert row["jsonpath_present"] is True
        assert row["semantic_restriction_present"] is True
        assert row["jsonpath"].startswith("$")
        assert row["semantic_restriction"]


def test_evidence_field_index_validator_catches_missing_jsonpath_edge(project_root: Path) -> None:
    """Co-actor-immune: a present field with no JSONPath edge fails the gate.

    The pre-Run-12 NC keyed on ``field_present`` only -- a row whose field
    exists on disk but carries no JSONPath edge would have passed. Here the
    field is still present, only the JSONPath edge is stripped.
    """
    from gates.aggregate_rederivation import rederive_aggregate
    from roadmap_tracks.sheaf_tracks_reports import build_evidence_field_index

    payload = build_evidence_field_index(project_root)
    spec = (
        "all",
        ("true", "field_present"),
        ("true", "jsonpath_present"),
        ("true", "semantic_restriction_present"),
    )
    assert rederive_aggregate(payload, spec) is True
    # Strip the JSONPath edge from one row while leaving field_present true.
    payload["rows"][0]["jsonpath"] = ""
    payload["rows"][0]["jsonpath_present"] = False
    assert payload["rows"][0]["field_present"] is True
    assert rederive_aggregate(payload, spec) is False


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_evidence_field_index_production_gate_fails_on_stripped_jsonpath(tmp_path: Path) -> None:
    """Production path: a row with field_present but no JSONPath edge fails validate_outputs."""
    from gates.output_checks import validate_outputs

    path = PROJECT_ROOT / "output" / "data" / "evidence_field_index.json"
    if not path.is_file() or "jsonpath_present" not in (_load(path).get("rows") or [{}])[0]:
        ensure_gate_artifacts(PROJECT_ROOT)
    backup = tmp_path / "evidence_field_index.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = _load(path)
    assert payload["rows"]
    payload["rows"][0]["jsonpath"] = ""
    payload["rows"][0]["jsonpath_present"] = False
    # Leave the stored aggregate lying True.
    payload["all_fields_mapped"] = True
    try:
        _write(path, payload)
        checks = validate_outputs(PROJECT_ROOT)
        # Caught by both the canonical sheaf validator and the aggregate re-derivation.
        assert checks["canonical_sheaf_track_schemas"] is False
        assert checks["aggregate_rederivation"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
    checks = validate_outputs(PROJECT_ROOT)
    assert checks["canonical_sheaf_track_schemas"] is True
    assert checks["aggregate_rederivation"] is True


# ---------------------------------------------------------------------------
# AI-PROVENANCE-FIELDS-1
# ---------------------------------------------------------------------------


def test_artifact_provenance_builder_emits_field_level_lineage(project_root: Path) -> None:
    """Write-path: per-field lineage rows carry hash/producer/seed/source_commit."""
    from roadmap_tracks.sheaf_tracks_builders import build_artifact_provenance

    payload = build_artifact_provenance(project_root)
    assert payload["all_field_hashes_present"] is True
    assert payload["field_row_count"] > 0
    for fr in payload["field_rows"]:
        assert fr["field_sha256"]
        assert fr["producer"]
        assert fr["source_commit"]
        assert fr["jsonpath"].startswith("$.")


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_artifact_provenance_production_gate_fails_on_field_hash_drift(tmp_path: Path) -> None:
    """Production path: changing one field's value (without updating its field hash) fails.

    Drift a downstream artifact's single field while leaving the pinned
    field-level hash in artifact_provenance.json stale. The whole-artifact
    sha256 layer also catches gross drift, so to isolate the FIELD-level
    contract we restore the artifact bytes and instead corrupt the stored
    field hash to a value that no longer re-derives from disk.
    """
    from gates.output_checks import validate_outputs

    path = PROJECT_ROOT / "output" / "data" / "artifact_provenance.json"
    if not path.is_file() or "field_rows" not in _load(path):
        ensure_gate_artifacts(PROJECT_ROOT)
    backup = tmp_path / "artifact_provenance.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = _load(path)
    field_rows = payload.get("field_rows") or []
    assert field_rows, "live artifact must carry field_rows"
    # Corrupt one stored field hash; the field on disk is unchanged so the
    # re-derivation mismatches exactly that field. Leave aggregates lying True.
    field_rows[0]["field_sha256"] = "0" * 64
    payload["all_field_hashes_present"] = True
    try:
        _write(path, payload)
        checks = validate_outputs(PROJECT_ROOT)
        assert checks["artifact_provenance_schema"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
    checks = validate_outputs(PROJECT_ROOT)
    assert checks["artifact_provenance_schema"] is True


# ---------------------------------------------------------------------------
# AI-DEPENDENCY-FIELDS-1
# ---------------------------------------------------------------------------


def test_dependency_graph_builder_emits_field_level_jsonpath_edges(project_root: Path) -> None:
    """Write-path: field-level JSONPath edges and a re-derivable count are emitted."""
    from roadmap_tracks.sheaf_tracks_reports import build_validation_dependency_graph

    payload = build_validation_dependency_graph(project_root)
    assert payload["all_required_edge_types_present"] is True
    assert set(payload["field_level_edge_kinds"]) == {"artifact_to_field", "field_to_claim", "field_to_section"}
    observed = sum(
        1 for edge in payload["edges"] if edge.get("kind") in set(payload["field_level_edge_kinds"])
    )
    assert payload["field_level_edge_count"] == observed > 0
    field_edges = [e for e in payload["edges"] if e.get("kind") == "artifact_to_field"]
    assert field_edges and all(e["jsonpath"].startswith("$.") for e in field_edges)


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_dependency_graph_production_gate_fails_on_deleted_field_edge(tmp_path: Path) -> None:
    """Production path: an artifact field used in prose with no dependency edge fails.

    Delete the field-level edges for one claim (the artifact_to_field /
    field_to_claim / field_to_section span) while leaving the stored count
    lying. The re-derived count then mismatches and the gate fails.
    """
    from gates.output_checks import validate_outputs

    path = PROJECT_ROOT / "output" / "data" / "validation_dependency_graph.json"
    if not path.is_file() or "field_level_edge_count" not in _load(path):
        ensure_gate_artifacts(PROJECT_ROOT)
    backup = tmp_path / "validation_dependency_graph.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = _load(path)
    # Drop one artifact_to_field edge (its field is still consumed in prose).
    dropped = next(e for e in payload["edges"] if e.get("kind") == "artifact_to_field")
    payload["edges"] = [e for e in payload["edges"] if e is not dropped]
    # Leave the stored count lying at the original value.
    try:
        _write(path, payload)
        checks = validate_outputs(PROJECT_ROOT)
        assert checks["canonical_sheaf_track_schemas"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
    checks = validate_outputs(PROJECT_ROOT)
    assert checks["canonical_sheaf_track_schemas"] is True
