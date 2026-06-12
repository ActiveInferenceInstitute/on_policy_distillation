"""Validation gates for canonical sheaf-track artifacts."""

from __future__ import annotations

from pathlib import Path

import roadmap_tracks.sheaf_tracks as _tracks
from .formal_interop import proof_inventory_mismatch
from .supplemental import validate_supplemental_artifacts


def _all_rows(payload: dict, field: str) -> bool:
    rows = payload.get("rows") or []
    return bool(rows) and all(row.get(field) for row in rows)


def _all_rows_absent(payload: dict, field: str) -> bool:
    rows = payload.get("rows") or []
    return bool(rows) and all(not row.get(field) for row in rows)


def _semantic_obligation_issues(root: Path, semantic: dict) -> list[str]:
    from manuscript.sheaf.semantic import _proof_obligations

    classes = semantic.get("restriction_classes") or {}
    rows = semantic.get("proof_obligations") or []
    required_classes = {"scope", "provenance", "dependency", "evidence", "formal", "render", "release", "blocked_scope"}
    issues: list[str] = []
    if set(classes) != required_classes:
        issues.append("sheaf_gluing_certificate.json restriction classes are incomplete")
    if not rows:
        issues.append("sheaf_gluing_certificate.json has no proof obligations")
        return issues
    boolean_restrictions = {
        key for key, value in (semantic.get("restrictions") or {}).items() if isinstance(value, bool)
    }
    obligation_restrictions = {str(row.get("semantic_restriction")) for row in rows}
    if obligation_restrictions != boolean_restrictions:
        issues.append("sheaf_gluing_certificate.json proof obligations do not cover every boolean restriction")
    expected_classes, expected_rows = _proof_obligations(root, semantic.get("restrictions") or {})
    expected_by_restriction = {str(row.get("semantic_restriction")): row for row in expected_rows}
    rows_by_restriction = {str(row.get("semantic_restriction")): row for row in rows}
    if set(classes) == required_classes and classes != expected_classes:
        issues.append("sheaf_gluing_certificate.json restriction classes drifted from live proof obligations")
    if rows_by_restriction.keys() == expected_by_restriction.keys():
        comparable_fields = ("class", "source_artifacts", "gate", "negative_control", "passed")
        for restriction, row in rows_by_restriction.items():
            expected = expected_by_restriction[restriction]
            if any(row.get(field) != expected.get(field) for field in comparable_fields):
                issues.append("sheaf_gluing_certificate.json proof-obligation row drifted from live mapping")
                break
    for class_id, class_row in classes.items():
        class_rows = [row for row in rows if row.get("class") == class_id]
        if not class_rows or class_row.get("obligation_count") != len(class_rows) or class_row.get("all_passed") is not True:
            issues.append(f"sheaf_gluing_certificate.json class {class_id} has incomplete proof obligations")
            break
    for row in rows:
        artifacts = row.get("source_artifacts") or []
        if (
            row.get("passed") is not True
            or row.get("class") not in required_classes
            or not row.get("gate")
            or not row.get("negative_control")
            or not row.get("semantic_restriction")
            or not artifacts
            or any(not (root / str(artifact)).exists() for artifact in artifacts)
        ):
            issues.append("sheaf_gluing_certificate.json has an invalid proof-obligation row")
            break
    if semantic.get("all_proof_obligations_passed") is not True:
        issues.append("sheaf_gluing_certificate.json proof obligations did not all pass")
    return issues


def load_sheaf_track_payloads(project_root: Path) -> dict[str, dict]:
    """Load the canonical artifact payload set once for cheap in-memory checks."""
    root = project_root.resolve()
    payloads = {
        key: _tracks._load_json(root / relative_path)
        for key, relative_path in _tracks.CANONICAL_ARTIFACTS.items()
    }
    payloads["lean_theorems"] = _tracks._load_json(root / "output" / "reports" / "lean_theorem_inventory.json")
    return payloads


def _payload(root: Path, payloads: dict[str, dict] | None, key: str) -> dict:
    if payloads is not None and key in payloads:
        return payloads[key]
    if key == "lean_theorems":
        return _tracks._load_json(root / "output" / "reports" / "lean_theorem_inventory.json")
    return _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS[key])


def validate_sheaf_track_payloads(
    project_root: Path,
    payloads: dict[str, dict],
    *,
    validate_saved_certificate: bool = True,
) -> list[str]:
    """Validate already-loaded canonical sheaf-track payloads.

    This keeps row-level negative controls fail-closed without rewriting the
    generated artifact tree for every mutation.
    """
    return _validate_sheaf_track_artifacts(
        project_root,
        payloads=payloads,
        validate_saved_certificate=validate_saved_certificate,
    )


def validate_sheaf_track_artifacts(project_root: Path, *, validate_saved_certificate: bool = True) -> list[str]:
    """Validate canonical sheaf-track artifacts and their semantic certificate."""
    return _validate_sheaf_track_artifacts(
        project_root,
        payloads=None,
        validate_saved_certificate=validate_saved_certificate,
    )


def _validate_sheaf_track_artifacts(
    project_root: Path,
    *,
    payloads: dict[str, dict] | None,
    validate_saved_certificate: bool,
) -> list[str]:
    root = project_root.resolve()
    issues: list[str] = []
    registry = _tracks._registry_tracks(root)
    versioned = sorted(track_id for track_id in registry if _tracks.VERSIONED_TRACK_RE.search(track_id))
    if versioned:
        issues.append(f"versioned live track ids are not allowed: {', '.join(versioned)}")

    missing_tracks = sorted(set(_tracks.CANONICAL_TRACKS) - set(registry))
    if missing_tracks:
        issues.append(f"missing canonical live tracks: {', '.join(missing_tracks)}")
    bound = _tracks._bound_tracks(root)
    unbound = sorted(track_id for track_id in _tracks.CANONICAL_TRACKS if not bound.get(track_id))
    if unbound:
        issues.append(f"canonical live tracks missing manuscript bindings: {', '.join(unbound)}")

    provenance = _payload(root, payloads, "provenance")
    if provenance.get("schema") != "template_active_inference.artifact_provenance.v1":
        issues.append("artifact_provenance.json schema mismatch")
    if provenance.get("all_records_complete") is not True or provenance.get("all_bundles_complete") is not True:
        issues.append("artifact_provenance.json has incomplete provenance rows or bundles")

    replay = _payload(root, payloads, "replay_matrix")
    if replay.get("schema") != "template_active_inference.replay_matrix.v1":
        issues.append("replay_matrix.json schema mismatch")
    replay_rows_matched = _all_rows(replay, "matched")
    producers_represented_ok = bool(replay.get("rows")) and {
        row.get("producer_script") for row in replay.get("rows") or []
    } == set(replay.get("configured_scripts") or [])
    if (
        replay.get("all_replay_rows_matched") is not True
        or replay.get("all_replay_rows_matched") != replay_rows_matched
    ):
        issues.append("replay_matrix.json records a replay mismatch")
    if (
        replay.get("all_configured_producers_represented") is not True
        or replay.get("all_configured_producers_represented") != producers_represented_ok
    ):
        issues.append("replay_matrix.json does not represent every configured producer")

    sensitivity = _payload(root, payloads, "sensitivity")
    if sensitivity.get("schema") != "template_active_inference.sensitivity_sweep.v1":
        issues.append("sensitivity_sweep.json schema mismatch")
    if sensitivity.get("complete_grid") is not True or sensitivity.get("row_count") != sensitivity.get(
        "expected_cells"
    ):
        issues.append("sensitivity_sweep.json grid is incomplete")

    uncertainty = _payload(root, payloads, "uncertainty")
    if uncertainty.get("schema") != "template_active_inference.uncertainty_summary.v1":
        issues.append("uncertainty_summary.json schema mismatch")
    uncertainty_normalized = _all_rows(uncertainty, "normalized")
    valid_bins = set((uncertainty.get("bins") or {}).keys())
    uncertainty_bins_valid = bool(uncertainty.get("rows")) and all(
        row.get("bin") in valid_bins for row in uncertainty.get("rows") or []
    )
    if (
        uncertainty.get("all_normalized") is not True
        or uncertainty.get("all_normalized") != uncertainty_normalized
        or uncertainty.get("all_bins_valid") is not True
        or uncertainty.get("all_bins_valid") != uncertainty_bins_valid
    ):
        issues.append("uncertainty_summary.json has invalid bins or unnormalized rows")

    counter = _payload(root, payloads, "counterexample")
    if counter.get("schema") != "template_active_inference.counterexample_matrix.v1":
        issues.append("counterexample_matrix.json schema mismatch")
    counter_observed = bool(counter.get("rows")) and all(
        row.get("fixture_replay_status") == "expected_failure_observed" for row in counter.get("rows") or []
    )
    if (
        counter.get("all_expected_failures_observed") is not True
        or counter.get("all_expected_failures_observed") != counter_observed
    ):
        issues.append("counterexample_matrix.json has expected-failure fixtures passing")

    model = _payload(root, payloads, "model_checking")
    if model.get("schema") != "template_active_inference.model_checking_witnesses.v1":
        issues.append("model_checking_witnesses.json schema mismatch")
    model_exhaustive = _all_rows(model, "exhaustive")
    model_passed = bool(model.get("rows")) and all(
        row.get("passed") and not row.get("counterexamples") for row in model.get("rows") or []
    )
    if (
        model.get("all_exhaustive") is not True
        or model.get("all_exhaustive") != model_exhaustive
        or model.get("all_passed") is not True
        or model.get("all_passed") != model_passed
    ):
        issues.append("model_checking_witnesses.json missed a finite counterexample")

    interop = _payload(root, payloads, "interop")
    if interop.get("schema") != "template_active_inference.interop_roundtrip_report.v1":
        issues.append("interop_roundtrip_report.json schema mismatch")
    interop_lossless = _all_rows(interop, "lossless")
    interop_shapes_empty = _all_rows_absent(interop, "shape_diff")
    if (
        interop.get("all_lossless") is not True
        or interop.get("all_lossless") != interop_lossless
        or interop.get("all_shape_diffs_empty") is not True
        or interop.get("all_shape_diffs_empty") != interop_shapes_empty
    ):
        issues.append("interop_roundtrip_report.json is not lossless")

    adversarial = _payload(root, payloads, "adversarial_audit")
    if adversarial.get("schema") != "template_active_inference.adversarial_audit.v1":
        issues.append("adversarial_audit.json schema mismatch")
    adversarial_observed = bool(adversarial.get("rows")) and all(
        row.get("expected_failure") and row.get("observed") == "expected_failure"
        for row in adversarial.get("rows") or []
    )
    known_bad_passed = sum(1 for row in adversarial.get("rows") or [] if row.get("known_bad_passed"))
    if (
        adversarial.get("all_expected_failures_observed") is not True
        or adversarial.get("all_expected_failures_observed") != adversarial_observed
        or adversarial.get("known_bad_rows_passed") != known_bad_passed
        or known_bad_passed != 0
    ):
        issues.append("adversarial_audit.json has known-bad rows passing")

    dependency = _payload(root, payloads, "dependency")
    if dependency.get("schema") != _tracks.DEPENDENCY_SCHEMA:
        issues.append("validation_dependency_graph.json schema mismatch")
    if dependency.get("all_required_edge_types_present") is not True:
        issues.append("validation_dependency_graph.json lacks required edge types")
    # AI-DEPENDENCY-FIELDS-1: re-derive the field-level edge count from the edge
    # list (never trust the stored count). A field edge deleted by hand desyncs
    # the observed count from the re-derivation, and the field edge kinds must
    # be present in the set.
    dep_edges = dependency.get("edges") or []
    field_edge_kinds = set(dependency.get("field_level_edge_kinds") or [])
    if field_edge_kinds != {"artifact_to_field", "field_to_claim", "field_to_section"}:
        issues.append("validation_dependency_graph.json missing field-level edge kinds")
    observed_field_edges = sum(1 for edge in dep_edges if str(edge.get("kind")) in field_edge_kinds)
    stored_field_edges = int(dependency.get("field_level_edge_count", -1) or -1)
    if stored_field_edges <= 0 or stored_field_edges != observed_field_edges:
        issues.append("validation_dependency_graph.json field-level edge count is stale")
    if not field_edge_kinds.issubset(set(dependency.get("edge_types") or [])):
        issues.append("validation_dependency_graph.json field-level edges absent")

    section_status = _payload(root, payloads, "section_status")
    if section_status.get("schema") != "template_active_inference.sheaf_section_status_matrix.v1":
        issues.append("sheaf_section_status_matrix.json schema mismatch")
    bound_fragments_ok = bool(section_status.get("cells")) and not any(
        cell.get("bound") and cell.get("coverage_status") == "missing" and not cell.get("optional")
        for cell in section_status.get("cells") or []
    )
    if (
        section_status.get("all_bound_fragments_present") is not True
        or section_status.get("all_bound_fragments_present") != bound_fragments_ok
    ):
        issues.append("sheaf_section_status_matrix.json has missing bound fragments")
    sections_have_status_ok = bool(section_status.get("sections")) and all(
        bool(row.get("status")) for row in section_status.get("sections") or []
    )
    tracks_have_status_ok = bool(section_status.get("tracks")) and all(
        bool(row.get("status")) for row in section_status.get("tracks") or []
    )
    if (
        section_status.get("all_sections_have_status") is not True
        or section_status.get("all_sections_have_status") != sections_have_status_ok
        or section_status.get("all_tracks_have_status") is not True
        or section_status.get("all_tracks_have_status") != tracks_have_status_ok
    ):
        issues.append("sheaf_section_status_matrix.json has incomplete status rows")

    render_log = _payload(root, payloads, "render_log")
    if render_log.get("schema") != "template_active_inference.sheaf_render_log.v1":
        issues.append("sheaf_render_log.json schema mismatch")
    events_ok = bool(render_log.get("events")) and all(
        event.get("status") == "ok" for event in render_log.get("events") or []
    )
    if render_log.get("all_events_ok") is not True or render_log.get("all_events_ok") != events_ok:
        issues.append("sheaf_render_log.json has failed render events")

    scope = _payload(root, payloads, "track_improvement_scope")
    if scope.get("schema") != "template_active_inference.track_improvement_scope.v1":
        issues.append("track_improvement_scope.json schema mismatch")
    live_tracks_ok = bool(scope.get("promotion_matrix")) and all(
        row.get("promotion_complete") for row in scope.get("promotion_matrix") or []
    )
    if scope.get("all_live_tracks_valid") is not True or scope.get("all_live_tracks_valid") != live_tracks_ok:
        issues.append("track_improvement_scope.json has incomplete live-track promotion rows")

    blocked = _payload(root, payloads, "blocked_scope_manifest")
    if blocked.get("schema") != "template_active_inference.blocked_scope_manifest.v1":
        issues.append("blocked_scope_manifest.json schema mismatch")
    blocked_rows_ok = bool(blocked.get("rows")) and all(
        row.get("status") == "blocked"
        and row.get("no_live_registry_entry")
        and row.get("no_configured_producer")
        and row.get("no_empirical_result_artifact")
        for row in blocked.get("rows") or []
    )
    if blocked.get("all_blocked") is not True or blocked.get("all_blocked") != blocked_rows_ok:
        issues.append("blocked_scope_manifest.json does not keep empirical scope blocked")

    evidence = _payload(root, payloads, "evidence_fields")
    if evidence.get("schema") != "template_active_inference.evidence_field_index.v1":
        issues.append("evidence_field_index.json schema mismatch")
    evidence_fields_mapped = bool(evidence.get("rows")) and all(
        row.get("artifact")
        and row.get("field_present")
        and row.get("claim_id")
        # AI-EVIDENCE-FIELDS-1: a field with no JSONPath edge or no semantic
        # restriction is not source-backed, even if field_present is true.
        and row.get("jsonpath_present")
        and row.get("semantic_restriction_present")
        for row in evidence.get("rows") or []
    )
    if evidence.get("all_fields_mapped") is not True or evidence.get("all_fields_mapped") != evidence_fields_mapped:
        issues.append("evidence_field_index.json has unmapped evidence fields")

    release = _payload(root, payloads, "release_bundle")
    if release.get("schema") != "template_active_inference.release_bundle_manifest.v1":
        issues.append("release_bundle_manifest.json schema mismatch")
    if release.get("all_required_sources_present") is not True:
        issues.append("release_bundle_manifest.json is missing required deliverables")

    theorem = _payload(root, payloads, "theorem_traceability")
    if theorem.get("schema") != "template_active_inference.theorem_traceability_matrix.v1":
        issues.append("theorem_traceability_matrix.json schema mismatch")
    theorem_linked = _all_rows(theorem, "linked")
    if theorem.get("all_theorems_linked") is not True or theorem.get("all_theorems_linked") != theorem_linked:
        issues.append("theorem_traceability_matrix.json has unlinked theorem rows")

    gate_index = _payload(root, payloads, "gate_ergonomics")
    gate_indexed = _all_rows(gate_index, "indexed")
    if gate_index.get("all_indexed") is not True or gate_index.get("all_indexed") != gate_indexed:
        issues.append("validation_gate_index.json has unindexed gates")

    diffoscope = _payload(root, payloads, "artifact_diffoscope")
    if diffoscope.get("schema") != "template_active_inference.artifact_diffoscope.v1":
        issues.append("artifact_diffoscope.json schema mismatch")
    diffoscope_equal = _all_rows(diffoscope, "equal")
    if diffoscope.get("all_equal") is not True or diffoscope.get("all_equal") != diffoscope_equal:
        issues.append("artifact_diffoscope.json records artifact drift")

    proof = _payload(root, payloads, "proof_extraction")
    if proof.get("schema") != "template_active_inference.proof_extraction_index.v1":
        issues.append("proof_extraction_index.json schema mismatch")
    proof_extracted = _all_rows(proof, "extracted")
    proof_constructive = bool(proof.get("rows")) and all(
        not row.get("forbidden_tokens") for row in proof.get("rows") or []
    )
    lean_theorems = _payload(root, payloads, "lean_theorems")
    if (
        proof.get("all_extracted") is not True
        or proof.get("all_extracted") != proof_extracted
        or proof.get("all_constructive") is not True
        or proof.get("all_constructive") != proof_constructive
    ):
        issues.append("proof_extraction_index.json has missing statements or nonconstructive tokens")
    if (
        proof.get("inventory_theorem_count") != lean_theorems.get("theorem_count")
        or proof.get("theorem_count") != lean_theorems.get("theorem_count")
        or proof.get("all_inventory_theorems_extracted") is not True
    ):
        issues.append("proof_extraction_index.json theorem inventory mismatch")
    issues.extend(proof_inventory_mismatch(proof, lean_theorems))

    catalog = _payload(root, payloads, "state_space_catalog")
    if catalog.get("schema") != "template_active_inference.state_space_catalog.v1":
        issues.append("state_space_catalog.json schema mismatch")
    catalog_finite = _all_rows(catalog, "finite")
    catalog_counts_positive = bool(catalog.get("rows")) and all(
        int(row.get("state_count", 0) or 0) > 0 and int(row.get("policy_count", 0) or 0) >= 1
        for row in catalog.get("rows") or []
    )
    if (
        catalog.get("all_finite") is not True
        or catalog.get("all_finite") != catalog_finite
        or catalog.get("all_counts_positive") is not True
        or catalog.get("all_counts_positive") != catalog_counts_positive
    ):
        issues.append("state_space_catalog.json has missing finite spaces")

    ablation = _payload(root, payloads, "causal_ablation")
    if ablation.get("schema") != "template_active_inference.causal_ablation_matrix.v1":
        issues.append("causal_ablation_matrix.json schema mismatch")
    ablation_deterministic = _all_rows(ablation, "deterministic")
    ablation_complete = len(ablation.get("rows") or []) == int(ablation.get("expected_cells", -1) or -1)
    if (
        ablation.get("complete_grid") is not True
        or ablation.get("complete_grid") != ablation_complete
        or ablation.get("all_deterministic") is not True
        or ablation.get("all_deterministic") != ablation_deterministic
    ):
        issues.append("causal_ablation_matrix.json has incomplete deterministic rows")

    license_audit = _payload(root, payloads, "artifact_license")
    if license_audit.get("schema") != "template_active_inference.artifact_license_audit.v1":
        issues.append("artifact_license_audit.json schema mismatch")
    license_safe = bool(license_audit.get("rows")) and all(
        row.get("license_safe") and row.get("license") for row in license_audit.get("rows") or []
    )
    if license_audit.get("all_license_safe") is not True or license_audit.get("all_license_safe") != license_safe:
        issues.append("artifact_license_audit.json records unsafe artifacts")

    release_notes = _payload(root, payloads, "release_notes")
    if release_notes.get("schema") != "template_active_inference.release_notes_evidence.v1":
        issues.append("release_notes_evidence.json schema mismatch")
    notes_backed = bool(release_notes.get("rows")) and all(
        row.get("source") and row.get("passed") for row in release_notes.get("rows") or []
    )
    if (
        release_notes.get("all_notes_source_backed") is not True
        or release_notes.get("all_notes_source_backed") != notes_backed
    ):
        issues.append("release_notes_evidence.json has unsupported notes")

    scholarship = _payload(root, payloads, "scholarship")
    scholarship_rows = scholarship.get("rows") or []
    scholarship_connected = bool(scholarship_rows) and all(
        row.get("bib_has_entry")
        and row.get("bib_has_locator")
        and row.get("cited_in_manuscript")
        and row.get("artifact_exists")
        and row.get("tracks_registered")
        and row.get("sections_bound")
        and row.get("claim_boundary")
        and row.get("connected")
        for row in scholarship_rows
    )
    if scholarship.get("schema") != "template_active_inference.scholarship_source_matrix.v1":
        issues.append("scholarship_source_matrix.json schema mismatch")
    if scholarship.get("all_expected_sources_present") is not True:
        issues.append("scholarship_source_matrix.json source set is incomplete")
    if (
        scholarship.get("all_sources_connected") is not True
        or scholarship.get("all_sources_connected") != scholarship_connected
    ):
        issues.append("scholarship_source_matrix.json has disconnected source rows")
    if int(scholarship.get("method_role_count", 0) or 0) < 6:
        issues.append("scholarship_source_matrix.json has too few method roles")

    proof_dependency = _payload(root, payloads, "proof_dependency_graph")
    proof_dependency_rows = proof_dependency.get("rows") or []
    proof_dependency_edges = proof_dependency.get("edges") or []
    proof_dependency_rows_ok = bool(proof_dependency_rows) and all(row.get("linked") for row in proof_dependency_rows)
    proof_dependency_edges_ok = bool(proof_dependency_edges) and all(
        edge.get("source") and edge.get("target") and edge.get("kind") for edge in proof_dependency_edges
    )
    if proof_dependency.get("schema") != "template_active_inference.proof_dependency_graph.v1":
        issues.append("proof_dependency_graph.json schema mismatch")
    if (
        proof_dependency.get("all_theorems_have_dependencies") is not True
        or proof_dependency.get("all_theorems_have_dependencies") != proof_dependency_rows_ok
    ):
        issues.append("proof_dependency_graph.json has unlinked theorem dependencies")
    if (
        proof_dependency.get("all_edges_resolved") is not True
        or proof_dependency.get("all_edges_resolved") != proof_dependency_edges_ok
    ):
        issues.append("proof_dependency_graph.json has unresolved edges")

    transition_table = _payload(root, payloads, "state_transition_table")
    transition_rows = transition_table.get("rows") or []
    transitions_deterministic = bool(transition_rows) and all(
        row.get("deterministic") and row.get("next_state") for row in transition_rows
    )
    transitions_covered = set(transition_table.get("required_models") or []).issubset(
        set(transition_table.get("covered_models") or [])
    )
    if transition_table.get("schema") != "template_active_inference.state_transition_table.v1":
        issues.append("state_transition_table.json schema mismatch")
    if (
        transition_table.get("all_transitions_deterministic") is not True
        or transition_table.get("all_transitions_deterministic") != transitions_deterministic
    ):
        issues.append("state_transition_table.json has nondeterministic or incomplete transitions")
    if (
        transition_table.get("all_reachable_states_covered") is not True
        or transition_table.get("all_reachable_states_covered") != transitions_covered
    ):
        issues.append("state_transition_table.json omits a reachable finite model")

    ablation_sensitivity = _payload(root, payloads, "ablation_sensitivity_report")
    ablation_sensitivity_rows = ablation_sensitivity.get("rows") or []
    ablation_sensitivity_backed = bool(ablation_sensitivity_rows) and all(
        row.get("source_backed") for row in ablation_sensitivity_rows
    )
    if ablation_sensitivity.get("schema") != "template_active_inference.ablation_sensitivity_report.v1":
        issues.append("ablation_sensitivity_report.json schema mismatch")
    if (
        ablation_sensitivity.get("all_effects_source_backed") is not True
        or ablation_sensitivity.get("all_effects_source_backed") != ablation_sensitivity_backed
    ):
        issues.append("ablation_sensitivity_report.json has unsupported ablation effects")

    release_attestation = _payload(root, payloads, "release_attestation")
    release_attestation_rows = release_attestation.get("rows") or []
    # Strict re-derivation: deferred evidence is not attested evidence.
    release_attested = bool(release_attestation_rows) and all(
        row.get("passed") for row in release_attestation_rows
    )
    if release_attestation.get("schema") != "template_active_inference.release_attestation.v1":
        issues.append("release_attestation.json schema mismatch")
    # Consistency check only: the flag must agree with its rows. Whether the
    # attestation is GREEN is enforced by validate_outputs (with hash currency);
    # mid-convergence an honestly-false flag is the expected state, not a lie.
    if release_attestation.get("all_attested") != release_attested:
        issues.append("release_attestation.json claims a failed gate passed")

    if payloads is None:
        from .scholarship import validate_scholarship_source_matrix

        issues.extend(validate_scholarship_source_matrix(root))
        issues.extend(validate_supplemental_artifacts(root))

    restrictions = _tracks._canonical_restrictions(root)
    false_restrictions = sorted(key for key, ok in restrictions.items() if not ok)
    if false_restrictions:
        issues.append(f"canonical semantic restrictions failed: {', '.join(false_restrictions)}")

    if validate_saved_certificate:
        semantic = _payload(root, payloads, "semantic")
        if semantic.get("schema") != _tracks.SEMANTIC_SCHEMA:
            issues.append("sheaf_gluing_certificate.json schema mismatch")
        if semantic.get("ok") is not True:
            issues.append("sheaf_gluing_certificate.json is not ok")
        saved_restrictions = semantic.get("restrictions") or {}
        for key, expected in restrictions.items():
            if saved_restrictions.get(key) != expected:
                issues.append("sheaf_gluing_certificate.json is stale relative to canonical restrictions")
                break
        issues.extend(_semantic_obligation_issues(root, semantic))

    if "empirical_adapter" in registry:
        issues.append("empirical_adapter blocked track was promoted live")
    return issues
