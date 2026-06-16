"""Pipeline output artifact validation."""

from __future__ import annotations

import json
import math
from pathlib import Path

from gates.artifact_manifest import REQUIRED_OUTPUTS

SUPPORTED_SELECTED_OUTPUT_CHECKS = {
    *(str(Path(rel).as_posix()) for rel in REQUIRED_OUTPUTS),
    "si_invariants_all_pass",
    "invariants_all_pass",
    "simulation_invariants_all_pass",
    "si_trace_present",
    "si_summary_schema",
    "si_tmaze_model_matrices_schema",
    "pymdp_policy_posterior_grid_schema",
    "figure_output_integrity",
    "figure_source_map_schema",
    "figure_hash_manifest_schema",
    "visualization_quality_audit_schema",
    "firstprinciples_empirical_benchmark_schema",
    "firstprinciples_taxonomy_schema",
    "firstprinciples_statistics_schema",
    "firstprinciples_privilege_sweep_schema",
    "firstprinciples_classroom_schema",
    "firstprinciples_sequential_shift_schema",
    "firstprinciples_sequential_shift_sensitivity_schema",
    "firstprinciples_benchmark_table_present",
    "toy_sweep_track_schemas",
    "formal_interop_track_schemas",
    "ontology_profile_schema",
    "integration_audit_track_schemas",
    "cross_track_symbol_table_schema",
    "canonical_sheaf_track_schemas",
    "aggregate_rederivation",
}


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _as_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _close_float(value: object, expected: float, *, atol: float = 1e-9) -> bool:
    try:
        observed = float(value)
    except (TypeError, ValueError):
        return False
    return bool(math.isfinite(observed) and abs(observed - expected) <= atol)


def _finite_series(value: object, *, allow_negative: bool = False) -> list[float] | None:
    if not isinstance(value, list) or not value:
        return None
    series: list[float] = []
    for item in value:
        try:
            number = float(item)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(number) or (number < 0.0 and not allow_negative):
            return None
        series.append(number)
    return series


def _summary_matches_series(summary: object, series: list[float]) -> bool:
    if not isinstance(summary, dict):
        return False
    n = len(series)
    mean = sum(series) / n
    variance = sum((value - mean) ** 2 for value in series) / (n - 1) if n > 1 else 0.0
    expected = {
        "n": n,
        "mean": mean,
        "std": math.sqrt(variance),
        "minimum": min(series),
        "maximum": max(series),
    }
    return all(_close_float(summary.get(key), value) for key, value in expected.items())


def _cohens_d_student_minus_teacher(student: list[float], teacher: list[float]) -> float | None:
    if len(student) < 2 or len(teacher) < 2:
        return None
    student_mean = sum(student) / len(student)
    teacher_mean = sum(teacher) / len(teacher)
    student_var = sum((value - student_mean) ** 2 for value in student) / (len(student) - 1)
    teacher_var = sum((value - teacher_mean) ** 2 for value in teacher) / (len(teacher) - 1)
    pooled_var = ((len(student) - 1) * student_var + (len(teacher) - 1) * teacher_var) / (
        len(student) + len(teacher) - 2
    )
    pooled_sd = math.sqrt(pooled_var)
    if pooled_sd == 0.0:
        return 0.0
    return (student_mean - teacher_mean) / pooled_sd


_QWEN_SOURCE_LOCATOR = "Qwen3 Technical Report, Table 21"
_QWEN_SOURCE_HEADING = "Comparison of reinforcement learning and on-policy distillation on Qwen3-8B"
_QWEN_SOURCE_TABLE = "Table 21"
_QWEN_SOURCE_URL = "https://arxiv.org/abs/2505.09388"
_QWEN_SOURCE_ARXIV_ID = "2505.09388"
_QWEN_EMPIRICAL_ROWS = {
    "off_policy_distillation": {"aime24": 55.0, "gpqa_diamond": 55.6, "gpu_hours": None},
    "reinforcement_learning": {"aime24": 67.6, "gpqa_diamond": 61.3, "gpu_hours": 17920.0},
    "on_policy_distillation": {"aime24": 74.4, "gpqa_diamond": 63.3, "gpu_hours": 1800.0},
}
_FIGURE_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def _float_field_equals(value: object, expected: float | None) -> bool:
    if expected is None:
        return value is None
    return abs(_as_float(value, 1e100) - expected) <= 1e-9


def _firstprinciples_empirical_benchmark_ok(payload: dict) -> bool:
    rows = payload.get("rows") or []
    by_method = {str(row.get("method")): row for row in rows if isinstance(row, dict)}
    replication = payload.get("thinking_machines_replication") or {}
    efficiency_min = _as_float(replication.get("efficiency_range_min"), -1.0)
    efficiency_max = _as_float(replication.get("efficiency_range_max"), -1.0)
    top_level_source_ok = (
        payload.get("schema") == "firstprinciples.empirical_benchmark.v1"
        and payload.get("source") == "literature_reported"
        and payload.get("direct_bibkey") == "qwen2025technical_report"
        and payload.get("relayed_by_bibkey") == "thinkingmachines2025opd"
        and payload.get("source_locator") == _QWEN_SOURCE_LOCATOR
        and payload.get("source_heading") == _QWEN_SOURCE_HEADING
        and payload.get("source_table") == _QWEN_SOURCE_TABLE
        and payload.get("source_url") == _QWEN_SOURCE_URL
        and payload.get("source_arxiv_id") == _QWEN_SOURCE_ARXIV_ID
        and _as_int(payload.get("row_count"), -1) == len(_QWEN_EMPIRICAL_ROWS)
        and len(rows) == len(_QWEN_EMPIRICAL_ROWS)
        and set(by_method) == set(_QWEN_EMPIRICAL_ROWS)
    )
    rows_ok = all(
        row.get("bibkey") == "qwen2025technical_report"
        and row.get("relayed_by") == "thinkingmachines2025opd"
        and row.get("source_locator") == _QWEN_SOURCE_LOCATOR
        and row.get("source_heading") == _QWEN_SOURCE_HEADING
        and row.get("source_table") == _QWEN_SOURCE_TABLE
        and row.get("source_url") == _QWEN_SOURCE_URL
        and row.get("source_arxiv_id") == _QWEN_SOURCE_ARXIV_ID
        and _float_field_equals(row.get("aime24"), expected["aime24"])
        and _float_field_equals(row.get("gpqa_diamond"), expected["gpqa_diamond"])
        and _float_field_equals(row.get("gpu_hours"), expected["gpu_hours"])
        for method, expected in _QWEN_EMPIRICAL_ROWS.items()
        for row in [by_method.get(method, {})]
    )
    replication_ok = (
        replication.get("bibkey") == "thinkingmachines2025opd"
        and _as_float(replication.get("aime24_accuracy"), 0.0) > 0.0
        and _as_int(replication.get("training_steps"), 0) > 0
        and 0.0 < efficiency_min <= efficiency_max
    )
    return bool(top_level_source_ok and rows_ok and replication_ok)


def _firstprinciples_taxonomy_ok(payload: dict) -> bool:
    methods = payload.get("methods") or []
    by_key = {str(row.get("bibkey")): row for row in methods if isinstance(row, dict)}
    freshness = by_key.get("chen2026freshness_opd") or {}
    return (
        payload.get("schema") == "firstprinciples.opd_taxonomy.v1"
        and int(payload.get("method_count", 0) or 0) == len(methods)
        and int(payload.get("method_count", 0) or 0) >= 8
        and int(payload.get("on_policy_count", 0) or 0) >= 1
        and "freshness_aware_async_buffer" in set(payload.get("signal_sources") or [])
        and freshness.get("acronym") == "f-OPD"
        and freshness.get("signal_source") == "freshness_aware_async_buffer"
        and freshness.get("divergence") == "freshness_weighted_reverse_kl"
        and freshness.get("on_policy") is True
        and freshness.get("privileged_info") is False
        and "staleness" in str(freshness.get("note", "")).lower()
    )


def _firstprinciples_sequential_shift_ok(payload: dict) -> bool:
    from firstprinciples.sequential_shift import validate_payload

    return bool(payload) and not validate_payload(payload)


def _firstprinciples_sequential_shift_sensitivity_ok(payload: dict) -> bool:
    from firstprinciples.sequential_shift import validate_sensitivity_payload

    return bool(payload) and not validate_sensitivity_payload(payload)


def _firstprinciples_statistics_ok(root: Path, payload: dict) -> bool:
    """Validate the classroom statistics artifact against its measured source rows."""
    from firstprinciples.classroom import validate_classroom_payload

    teacher = _finite_series(payload.get("teacher_entropy"))
    student = _finite_series(payload.get("student_entropy"))
    differences = _finite_series(payload.get("paired_difference"), allow_negative=True)
    if teacher is None or student is None or differences is None:
        return False
    if len(teacher) != len(student) or len(teacher) != len(differences):
        return False
    sample_size = len(differences)
    expected_differences = [s - t for s, t in zip(student, teacher, strict=True)]
    if _as_int(payload.get("sample_size"), -1) != sample_size:
        return False
    if any(not math.isfinite(value) for value in differences):
        return False
    if any(abs(value - expected) > 1e-9 for value, expected in zip(differences, expected_differences, strict=True)):
        return False
    if not _summary_matches_series(payload.get("teacher_summary"), teacher):
        return False
    if not _summary_matches_series(payload.get("student_summary"), student):
        return False

    classroom = _read_json(root / "output" / "data" / "firstprinciples" / "classroom.json")
    classroom_teacher = _finite_series(classroom.get("teacher_belief_entropies"))
    classroom_student = _finite_series(classroom.get("student_belief_entropies"))
    per_step = classroom.get("per_step") or []
    if not validate_classroom_payload(classroom) or classroom_teacher != teacher or classroom_student != student:
        return False
    if _as_int(classroom.get("decision_count"), -1) != sample_size or len(per_step) != sample_size:
        return False
    for row, expected_teacher, expected_student in zip(per_step, teacher, student, strict=True):
        if not isinstance(row, dict):
            return False
        if not _close_float(row.get("teacher_belief_entropy"), expected_teacher):
            return False
        if not _close_float(row.get("student_belief_entropy"), expected_student):
            return False

    ci = payload.get("advantage_bootstrap_ci") or {}
    permutation = payload.get("paired_permutation") or {}
    sign = payload.get("paired_sign_test") or {}
    diff_mean = sum(differences) / sample_size
    positive = sum(1 for value in differences if value > 0.0)
    negative = sum(1 for value in differences if value < 0.0)
    cohens_d = _cohens_d_student_minus_teacher(student, teacher)
    if cohens_d is None:
        return False
    claim_scope = str(payload.get("claim_scope") or "").lower()
    sample_unit = str(payload.get("sample_unit") or "").lower()
    effect_size = str(payload.get("effect_size") or "").lower()
    paired_test = str(payload.get("paired_test") or "").lower()
    return bool(
        payload.get("schema") == "firstprinciples.statistics_demo.v1"
        and payload.get("ok") is True
        and "toy-classroom" in claim_scope
        and "not a production-scale" in claim_scope
        and "classroom" in sample_unit
        and "student minus teacher" in effect_size
        and "student-minus-teacher" in paired_test
        and payload.get("effect_size_reference") == "cohen1988power"
        and _as_int(ci.get("n"), -1) == sample_size
        and _as_int(ci.get("n_boot"), 0) > 0
        and 0.0 < _as_float(ci.get("alpha"), -1.0) < 1.0
        and _close_float(ci.get("point"), diff_mean)
        and math.isfinite(_as_float(ci.get("ci_low"), math.inf))
        and math.isfinite(_as_float(ci.get("ci_high"), math.inf))
        and _as_float(ci.get("ci_low"), math.inf) <= _as_float(ci.get("ci_high"), -math.inf)
        and _as_int(permutation.get("n"), -1) == sample_size
        and _as_int(permutation.get("n_perm"), 0) > 0
        and _close_float(permutation.get("mean_difference"), diff_mean)
        and 0.0 <= _as_float(permutation.get("p_value"), -1.0) <= 1.0
        and _close_float(sign.get("positive"), float(positive))
        and _close_float(sign.get("negative"), float(negative))
        and _close_float(sign.get("n"), float(positive + negative))
        and _as_float(sign.get("p_value"), -1.0) <= 1.0
        and _as_float(sign.get("p_value"), -1.0) >= 0.0
        and _close_float(payload.get("cohens_d_student_minus_teacher"), cohens_d)
    )


def _pymdp_logging_expected(root: Path) -> bool:
    from simulation.pymdp_config import load_pymdp_config
    from simulation.si_runner import pymdp_available

    if not pymdp_available():
        return False
    cfg = load_pymdp_config(root)
    return bool(cfg.logging.enabled)


def _efe_values_explained(payload: dict) -> bool:
    rows = payload.get("rows") or []
    return bool(rows) and all(
        (row.get("terms_available") and bool((row.get("terms") or {}).get("values")))
        or (not row.get("terms_available") and bool(row.get("fallback_reason")))
        for row in rows
    )


def _si_invariants_all_pass_ok(payload: dict) -> bool:
    invariants = payload.get("invariants") or {}
    return bool(invariants) and all(value is True for value in invariants.values())


def _si_efe_rows_explained(payload: dict) -> bool:
    runs = payload.get("runs") or []
    return bool(runs) and all(
        bool(run.get("policy_posterior_steps"))
        and all(
            step.get("posterior_available") is True or bool(step.get("fallback_reason"))
            for step in run.get("policy_posterior_steps") or []
        )
        for run in runs
    )


#: Gate-index ids whose live check key differs from the row id.
_GATE_INDEX_ALIASES = {
    "canonical_sheaf_tracks": "canonical_sheaf_track_schemas",
    "semantic_sheaf_gluing": "canonical_sheaf_track_schemas",
    "typed_claim_evidence": "claim_evidence_audit_schema",
}

#: Gate-index ids that are external commands and cannot appear in `checks`:
#: the validate runner itself, the manuscript CLI, and the Lean toolchain.
_EXTERNAL_GATE_IDS = {"validate_outputs", "validate_manuscript", "lake_build"}


def _gate_index_binding(gate_index: dict, check_keys: set[str]) -> bool:
    """Every indexed gate-index row must bind to the live validator surface.

    A row binds when its id (or alias) is an exact or prefix match of a check
    key produced by THIS validate run, or names a known external gate. This is
    the read-time control that keeps the declarative GATE_INDEX_ROWS registry
    from drifting into phantom rows (AI-GATE-INDEX-3).
    """
    rows = gate_index.get("rows") or []
    if not rows:
        return False
    for row in rows:
        gate_id = str(row.get("id") or "")
        if row.get("indexed") is not True:
            return False
        if gate_id in _EXTERNAL_GATE_IDS:
            continue
        target = _GATE_INDEX_ALIASES.get(gate_id, gate_id)
        if target not in check_keys and not any(key.startswith(target) for key in check_keys):
            return False
    return True


def _figure_source_map_ok(root: Path, payload: dict) -> bool:
    from roadmap_tracks.integration_audit import _figure_source_rows_complete

    return (
        payload.get("schema") == "template_active_inference.figure_source_map.v1"
        and payload.get("all_figures_mapped") is True
        and _figure_source_rows_complete(root, payload)
    )


def _figure_hash_manifest_ok(root: Path, payload: dict) -> bool:
    from roadmap_tracks.integration_audit import _figure_hash_rows_complete

    return (
        payload.get("schema") == "template_active_inference.figure_hash_manifest.v1"
        and payload.get("all_hashes_present") is True
        and _figure_hash_rows_complete(root, payload)
    )


def _visualization_quality_audit_ok(root: Path, payload: dict) -> bool:
    from roadmap_tracks.integration_audit import _visualization_quality_caption_claims_rederived

    rows = payload.get("rows") or []
    contrast_rows = (payload.get("palette_contrast_report") or {}).values()
    font_rows = (payload.get("font_role_report") or {}).values()
    return (
        payload.get("schema") == "template_active_inference.visualization_quality_audit.v1"
        # Defense-in-depth: re-derive caption-claim booleans from the registry so a
        # fully self-consistent forged audit (all stored booleans flipped green over a
        # bad claim) cannot pass on stored values alone.
        and _visualization_quality_caption_claims_rederived(root, payload)
        and bool(rows)
        and int(payload.get("figure_count", -1) or -1) == len(rows)
        and payload.get("all_figures_readable") is True
        and payload.get("all_figures_nonblank") is True
        and payload.get("all_figures_source_bound") is True
        and payload.get("all_caption_claims_ok") is True
        and payload.get("all_scope_guards_present") is True
        and payload.get("all_caption_overclaims_free") is True
        and payload.get("all_claim_wording_ok") is True
        and payload.get("all_cover_quantitative_free") is True
        and payload.get("all_accessibility_metadata_ok") is True
        and payload.get("palette_contrast_ok") is True
        and payload.get("font_roles_ok") is True
        and bool(payload.get("palette_contrast_report"))
        and bool(payload.get("font_role_report"))
        and all(
            row.get("passes_aa") is True
            and "ratio" in row
            and "minimum_ratio" in row
            and float(row["ratio"]) >= float(row["minimum_ratio"])
            for row in contrast_rows
        )
        and all(
            row.get("meets_minimum") is True
            and "size_pt" in row
            and "minimum_pt" in row
            and float(row["size_pt"]) >= float(row["minimum_pt"])
            for row in font_rows
        )
        and payload.get("no_unexpected_image_artifacts") is True
        and int(payload.get("unexpected_image_count", 0) or 0) == 0
        and payload.get("unexpected_image_paths") == []
        and payload.get("all_rows_ok") is True
        and all(
            row.get("readable") is True
            and row.get("nonblank") is True
            and row.get("source_bound") is True
            and int(row.get("caption_claim_count", 0) or 0) > 0
            and row.get("caption_claims_source_bound") is True
            and row.get("caption_claim_fields_resolved") is True
            and row.get("caption_claim_terms_present") is True
            and row.get("caption_claim_scope_ok") is True
            and row.get("caption_claim_display_transform_ok") is True
            and row.get("caption_claims_ok") is True
            and row.get("metadata_complete") is True
            and row.get("scope_guard_present") is True
            and row.get("caption_overclaim_free") is True
            and row.get("claim_wording_ok") is True
            and row.get("cover_quantitative_free") is True
            and row.get("accessibility_ok") is True
            and row.get("ok") is True
            and int(row.get("image_width_px", 0) or 0) >= 400
            and int(row.get("image_height_px", 0) or 0) >= 200
            for row in rows
        )
    )


def _figure_output_integrity_ok(root: Path) -> bool:
    figures_dir = root / "output" / "figures"
    if not figures_dir.is_dir():
        return False
    hidden_images = [
        path
        for path in figures_dir.iterdir()
        if path.is_file() and path.name.startswith(".") and path.suffix.lower() in _FIGURE_IMAGE_SUFFIXES
    ]
    if hidden_images:
        return False
    from visualizations.figure_registry import load_figure_registry

    expected = {f"output/figures/{spec.filename}" for spec in load_figure_registry(root).values()}
    expected.add("output/figures/si_belief_trajectory.gif")
    visible_images = {
        path.relative_to(root).as_posix()
        for path in figures_dir.iterdir()
        if path.is_file() and not path.name.startswith(".") and path.suffix.lower() in _FIGURE_IMAGE_SUFFIXES
    }
    if visible_images - expected:
        return False
    pngs = sorted(figures_dir.glob("*.png"))
    if not pngs:
        return False
    try:
        from PIL import Image
    except ImportError:
        return False
    for path in pngs:
        try:
            with Image.open(path) as img:
                img.load()
                width, height = img.size
                extrema = img.convert("L").getextrema()
        except (OSError, ValueError):
            return False
        if width <= 0 or height <= 0 or extrema[0] >= extrema[1]:
            return False
    return True


def _proof_extraction_ok(proof_extraction: dict, lean_theorems: dict) -> bool:
    proof_rows = proof_extraction.get("rows") or []
    lean_rows = lean_theorems.get("rows") or []
    extracted = {str(row.get("theorem")) for row in proof_rows if row.get("theorem")}
    inventory = {str(row.get("name")) for row in lean_rows if row.get("name")}
    return (
        proof_extraction.get("schema") == "template_active_inference.proof_extraction_index.v1"
        and proof_extraction.get("all_extracted") is True
        and proof_extraction.get("all_constructive") is True
        and proof_extraction.get("all_inventory_theorems_extracted") is True
        and proof_extraction.get("missing_inventory_theorems") == []
        and proof_extraction.get("extra_extracted_theorems") == []
        and int(proof_extraction.get("theorem_count", -1) or -1) == int(lean_theorems.get("theorem_count", -2) or -2)
        and int(proof_extraction.get("inventory_theorem_count", -1) or -1)
        == int(lean_theorems.get("theorem_count", -2) or -2)
        and bool(inventory)
        and extracted == inventory
    )


def _ontology_profile_ok(payload: dict) -> bool:
    rows = payload.get("rows") or []
    expected = set(payload.get("expected_models") or [])
    present = set(payload.get("models_present") or [])
    present_from_rows = {str(row.get("model")) for row in rows if row.get("model")}
    return (
        payload.get("schema") == "template_active_inference.ontology_profile_matrix.v1"
        and bool(rows)
        and expected == {"bernoulli_toy", "si_tmaze", "graph_world", "bernoulli_ising"}
        and present == expected
        and present_from_rows == expected
        and payload.get("all_expected_models_present") is True
        and payload.get("all_terms_used") is True
        and payload.get("unused_profile_terms") == []
        and payload.get("all_mapped_once") is True
        and all(any(row.get("model") == model for row in rows) for model in expected)
        and all(
            row.get("model") in expected
            and row.get("mapping_count") == 1
            and row.get("mapped_once") is True
            and row.get("unused_profile_term") is False
            and bool(row.get("jsonpath"))
            and bool(row.get("variable"))
            and bool(row.get("ontology"))
            for row in rows
        )
    )


def _cross_track_symbol_table_ok(payload: dict) -> bool:
    rows = payload.get("rows") or []
    domain_rows = payload.get("domain_rows") or []
    required = set(payload.get("required_domains") or [])
    present = set(payload.get("domains_present") or [])
    present_from_rows = {str(row.get("domain")) for row in domain_rows if row.get("domain")}
    return (
        payload.get("schema") == "template_active_inference.cross_track_symbol_table.v1"
        and bool(rows)
        and bool(domain_rows)
        and required
        == {
            "gnn_variable",
            "ontology_term",
            "lean_theorem",
            "manuscript_variable",
            "json_field",
            "figure_label",
            "rendered_manuscript_consumer",
        }
        and required == present
        and required == present_from_rows
        and payload.get("all_required_domains_present") is True
        and payload.get("all_domain_rows_consistent") is True
        and payload.get("all_consistent") is True
        and payload.get("all_shapes_declared") is True
        and payload.get("all_dtypes_declared") is True
        and payload.get("all_ontology_terms_declared") is True
        and payload.get("all_section_terms_declared") is True
        and all(
            row.get("domain") in required
            and row.get("consistent") is True
            and bool(row.get("symbol"))
            and bool(row.get("source"))
            and bool(row.get("consumer"))
            for row in domain_rows
        )
    )


def _firstprinciples_classroom_ok(payload: dict) -> bool:
    from firstprinciples.classroom import validate_classroom_payload

    return validate_classroom_payload(payload)


def _validate_outputs_selected(root: Path, selected: set[str]) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    required_by_key = {str(Path(rel).as_posix()): root / rel for rel in REQUIRED_OUTPUTS}
    for key in selected & set(required_by_key):
        checks[key] = required_by_key[key].exists()

    if "si_invariants_all_pass" in selected:
        summary_path = root / "output" / "data" / "si_tmaze_summary.json"
        si_inv_path = root / "output" / "reports" / "si_invariants.json"
        if summary_path.exists() and not si_inv_path.exists():
            checks["si_invariants_all_pass"] = False
        elif si_inv_path.exists():
            payload = _read_json(si_inv_path)
            checks["si_invariants_all_pass"] = (
                payload.get("all_pass") is True and payload.get("all_pass") == _si_invariants_all_pass_ok(payload)
            )
        else:
            checks["si_invariants_all_pass"] = False

    if "invariants_all_pass" in selected or "simulation_invariants_all_pass" in selected:
        inv = _read_json(root / "output" / "reports" / "invariants.json")
        if "invariants_all_pass" in selected:
            checks["invariants_all_pass"] = inv.get("all_pass") is True
        if "simulation_invariants_all_pass" in selected:
            checks["simulation_invariants_all_pass"] = all((inv.get("simulation") or {}).values())

    if "si_trace_present" in selected or "si_summary_schema" in selected:
        summary = _read_json(root / "output" / "data" / "si_tmaze_summary.json")
        trace = _read_json(root / "output" / "data" / "si_tmaze_trace.json")
        steps = int(summary.get("steps", 0))
        rollout_timestep_count = int(summary.get("rollout_timestep_count", 0) or 0)
        trace_steps = trace.get("steps") or []
        if "si_trace_present" in selected:
            checks["si_trace_present"] = len(trace_steps) == rollout_timestep_count and steps >= 1
        if "si_summary_schema" in selected:
            checks["si_summary_schema"] = (
                summary.get("schema") == "template_active_inference.si_tmaze_summary.v2"
                and steps >= 1
                and rollout_timestep_count == steps + 1
                and float(summary.get("mean_belief_entropy", -1.0)) >= 0.0
                and summary.get("planner") == "sophisticated_inference"
                and summary.get("profile") == "full_tmaze_sophisticated_inference"
                and summary.get("tree_available") is True
                and bool(summary.get("q_pi_by_step"))
                and bool(summary.get("action_probabilities"))
                and set((summary.get("observations_by_modality") or {})) == {"location", "outcome", "cue"}
                and all(abs(float(sum(row)) - 1.0) <= 1e-6 for row in summary.get("q_pi_by_step") or [])
                and "config" in summary
                and "mode" not in summary
            )

    if "si_tmaze_model_matrices_schema" in selected:
        matrices = _read_json(root / "output" / "data" / "si_tmaze_model_matrices.json")
        checks["si_tmaze_model_matrices_schema"] = (
            matrices.get("schema") == "template_active_inference.si_tmaze_model_matrices.v1"
            and matrices.get("A_shapes") == [[5, 5], [3, 5, 2], [3, 5, 2]]
            and matrices.get("B_shapes") == [[5, 5, 5], [2, 2, 1]]
            and matrices.get("dependencies", {}).get("A") == [[0], [0, 1], [0, 1]]
            and matrices.get("dependencies", {}).get("B") == [[0], [1]]
            and all(check.get("normalized") is True for check in matrices.get("normalization_checks") or [])
        )

    if "pymdp_policy_posterior_grid_schema" in selected:
        from simulation.pymdp_config import load_pymdp_config

        cfg = load_pymdp_config(root)
        posterior = _read_json(root / "output" / "data" / "pymdp_policy_posterior_grid.json")
        rows = posterior.get("rows") or []
        actual_cells = {(row.get("planner"), row.get("seed")) for row in rows}
        checks["pymdp_policy_posterior_grid_schema"] = (
            posterior.get("schema") == "template_active_inference.pymdp_policy_posterior_grid.v1"
            and bool(rows)
            and posterior.get("scope") == "comparison_only"
            and posterior.get("all_available_posteriors_normalized") is True
            and posterior.get("all_unavailable_rows_explained") is True
            and actual_cells == {(planner, seed) for planner in cfg.validation_comparison.planners for seed in cfg.validation_comparison.seeds}
            and all(row.get("horizon") == cfg.planning_horizon for row in rows)
            and all(
                (not row.get("posterior_available")) or abs(float(sum(row.get("q_pi") or [])) - 1.0) <= 1e-9
                for row in rows
            )
        )

    if "figure_source_map_schema" in selected:
        checks["figure_source_map_schema"] = _figure_source_map_ok(
            root,
            _read_json(root / "output" / "data" / "figure_source_map.json"),
        )
    if "figure_hash_manifest_schema" in selected:
        checks["figure_hash_manifest_schema"] = _figure_hash_manifest_ok(
            root,
            _read_json(root / "output" / "reports" / "figure_hash_manifest.json"),
        )
    if "visualization_quality_audit_schema" in selected:
        checks["visualization_quality_audit_schema"] = _visualization_quality_audit_ok(
            root,
            _read_json(root / "output" / "reports" / "visualization_quality_audit.json"),
        )
    if "figure_output_integrity" in selected:
        checks["figure_output_integrity"] = _figure_output_integrity_ok(root)

    if "firstprinciples_empirical_benchmark_schema" in selected:
        fp_empirical = _read_json(root / "output" / "data" / "firstprinciples" / "empirical_benchmark.json")
        checks["firstprinciples_empirical_benchmark_schema"] = _firstprinciples_empirical_benchmark_ok(fp_empirical)

    if "firstprinciples_taxonomy_schema" in selected:
        fp_taxonomy = _read_json(root / "output" / "data" / "firstprinciples" / "opd_taxonomy.json")
        checks["firstprinciples_taxonomy_schema"] = _firstprinciples_taxonomy_ok(fp_taxonomy)

    if "firstprinciples_statistics_schema" in selected:
        fp_statistics = _read_json(root / "output" / "data" / "firstprinciples" / "statistics_demo.json")
        checks["firstprinciples_statistics_schema"] = _firstprinciples_statistics_ok(root, fp_statistics)

    if "firstprinciples_classroom_schema" in selected:
        checks["firstprinciples_classroom_schema"] = _firstprinciples_classroom_ok(
            _read_json(root / "output" / "data" / "firstprinciples" / "classroom.json")
        )

    if "firstprinciples_sequential_shift_schema" in selected:
        checks["firstprinciples_sequential_shift_schema"] = _firstprinciples_sequential_shift_ok(
            _read_json(root / "output" / "data" / "firstprinciples" / "sequential_shift.json")
        )
    if "firstprinciples_sequential_shift_sensitivity_schema" in selected:
        checks["firstprinciples_sequential_shift_sensitivity_schema"] = (
            _firstprinciples_sequential_shift_sensitivity_ok(
                _read_json(root / "output" / "data" / "firstprinciples" / "sequential_shift_sensitivity.json")
            )
        )

    if "firstprinciples_benchmark_table_present" in selected:
        fp_benchmark_table_path = root / "output" / "data" / "firstprinciples" / "benchmark_table.md"
        fp_benchmark_table = (
            fp_benchmark_table_path.read_text(encoding="utf-8") if fp_benchmark_table_path.is_file() else ""
        )
        checks["firstprinciples_benchmark_table_present"] = (
            fp_benchmark_table_path.is_file()
            and "qwen2025technical_report" in fp_benchmark_table
            and "thinkingmachines2025opd" in fp_benchmark_table
            and "AIME'24" in fp_benchmark_table
        )

    if "toy_sweep_track_schemas" in selected:
        from roadmap_tracks import validate_toy_sweep_artifacts

        checks["toy_sweep_track_schemas"] = not validate_toy_sweep_artifacts(root)
    if "formal_interop_track_schemas" in selected:
        from roadmap_tracks import validate_formal_interop_artifacts

        checks["formal_interop_track_schemas"] = not validate_formal_interop_artifacts(root)
    if "ontology_profile_schema" in selected:
        checks["ontology_profile_schema"] = _ontology_profile_ok(
            _read_json(root / "output" / "data" / "ontology_profile_matrix.json")
        )
    if "integration_audit_track_schemas" in selected:
        from roadmap_tracks import validate_integration_audit_artifacts

        checks["integration_audit_track_schemas"] = not validate_integration_audit_artifacts(root)
    if "cross_track_symbol_table_schema" in selected:
        checks["cross_track_symbol_table_schema"] = _cross_track_symbol_table_ok(
            _read_json(root / "output" / "data" / "cross_track_symbol_table.json")
        )
    if "canonical_sheaf_track_schemas" in selected:
        from roadmap_tracks import validate_sheaf_track_artifacts

        checks["canonical_sheaf_track_schemas"] = not validate_sheaf_track_artifacts(root)

    return checks


def validate_outputs_selected_strict(project_root: Path, only: set[str]) -> dict[str, bool]:
    """Validate selected output keys without falling back to the full gate.

    Public ``validate_outputs(..., only=...)`` keeps compatibility by falling
    back for keys that do not have a lazy implementation. Tests that assert
    runtime behavior should call this helper so new selected keys cannot
    accidentally reintroduce a full validation pass.
    """
    selected = set(only)
    unsupported = selected - SUPPORTED_SELECTED_OUTPUT_CHECKS
    if unsupported:
        raise KeyError(f"unsupported lazy output check keys: {sorted(unsupported)}")
    checks = _validate_outputs_selected(project_root.resolve(), selected)
    missing = selected - set(checks)
    if missing:
        raise AssertionError(f"lazy output checks did not return requested keys: {sorted(missing)}")
    return checks


def validate_outputs(project_root: Path, *, only: set[str] | None = None) -> dict[str, bool]:
    root = project_root.resolve()
    if only is not None:
        selected = set(only)
        selected_checks = _validate_outputs_selected(root, selected)
        if selected <= set(selected_checks):
            return selected_checks
        full = _validate_outputs_full(root)
        unsupported = selected - set(full) - set(selected_checks)
        if unsupported:
            raise KeyError(f"unsupported output check keys: {sorted(unsupported)}")
        return {key: full.get(key, selected_checks.get(key, False)) for key in selected}
    return _validate_outputs_full(root)


def _validate_outputs_full(project_root: Path) -> dict[str, bool]:
    root = project_root.resolve()
    required = [root / rel for rel in REQUIRED_OUTPUTS]
    checks = {str(p.relative_to(root)): p.exists() for p in required}

    summary_path = root / "output" / "data" / "si_tmaze_summary.json"
    trace_path = root / "output" / "data" / "si_tmaze_trace.json"
    matrices_path = root / "output" / "data" / "si_tmaze_model_matrices.json"
    si_inv_path = root / "output" / "reports" / "si_invariants.json"
    si_summary_present = summary_path.exists()
    if si_summary_present and not si_inv_path.exists():
        checks["si_invariants_all_pass"] = False
    elif si_inv_path.exists():
        si_inv = json.loads(si_inv_path.read_text(encoding="utf-8"))
        checks["si_invariants_all_pass"] = (
            si_inv.get("all_pass") is True and si_inv.get("all_pass") == _si_invariants_all_pass_ok(si_inv)
        )

    inv_path = root / "output" / "reports" / "invariants.json"
    if inv_path.exists():
        inv = json.loads(inv_path.read_text(encoding="utf-8"))
        checks["invariants_all_pass"] = inv.get("all_pass") is True
        sim = inv.get("simulation") or {}
        if sim:
            checks["simulation_invariants_all_pass"] = all(sim.values())

    if summary_path.exists() and trace_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        steps = int(summary.get("steps", 0))
        rollout_timestep_count = int(summary.get("rollout_timestep_count", 0) or 0)
        trace_steps = trace.get("steps") or []
        checks["si_trace_present"] = len(trace_steps) == rollout_timestep_count and steps >= 1
        checks["si_summary_schema"] = (
            summary.get("schema") == "template_active_inference.si_tmaze_summary.v2"
            and steps >= 1
            and rollout_timestep_count == steps + 1
            and float(summary.get("mean_belief_entropy", -1.0)) >= 0.0
            and summary.get("planner") == "sophisticated_inference"
            and summary.get("profile") == "full_tmaze_sophisticated_inference"
            and summary.get("tree_available") is True
            and bool(summary.get("q_pi_by_step"))
            and bool(summary.get("action_probabilities"))
            and set((summary.get("observations_by_modality") or {})) == {"location", "outcome", "cue"}
            and all(abs(float(sum(row)) - 1.0) <= 1e-6 for row in summary.get("q_pi_by_step") or [])
            and "config" in summary
            and "mode" not in summary
        )
    if matrices_path.exists():
        matrices = json.loads(matrices_path.read_text(encoding="utf-8"))
        checks["si_tmaze_model_matrices_schema"] = (
            matrices.get("schema") == "template_active_inference.si_tmaze_model_matrices.v1"
            and matrices.get("A_shapes") == [[5, 5], [3, 5, 2], [3, 5, 2]]
            and matrices.get("B_shapes") == [[5, 5, 5], [2, 2, 1]]
            and matrices.get("dependencies", {}).get("A") == [[0], [0, 1], [0, 1]]
            and matrices.get("dependencies", {}).get("B") == [[0], [1]]
            and all(check.get("normalized") is True for check in matrices.get("normalization_checks") or [])
        )

    comparison_path = root / "output" / "data" / "si_policy_comparison.json"
    if comparison_path.exists():
        comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
        runs = comparison.get("runs") or []
        checks["si_policy_comparison_schema"] = (
            bool(runs)
            and comparison.get("scope") == "comparison_only"
            and comparison.get("canonical_planner") == "sophisticated_inference"
            and {row.get("planner") for row in runs} == {"sophisticated_inference", "vanilla"}
            and all(row.get("role") == "validation_comparison" for row in runs)
            and all("horizon" in row and "goal_reached" in row for row in runs)
            and (comparison.get("summary") or {}).get("complete_grid") is True
            and (comparison.get("summary") or {}).get("vanilla_role") == "comparison_only"
            and (comparison.get("summary") or {}).get("all_efe_rows_explained") is True
            and (comparison.get("summary") or {}).get("all_efe_rows_explained") == _si_efe_rows_explained(comparison)
        )
    posterior_path = root / "output" / "data" / "pymdp_policy_posterior_grid.json"
    if posterior_path.exists():
        from simulation.pymdp_config import load_pymdp_config

        cfg = load_pymdp_config(root)
        posterior = json.loads(posterior_path.read_text(encoding="utf-8"))
        rows = posterior.get("rows") or []
        actual_cells = {(row.get("planner"), row.get("seed")) for row in rows}
        checks["pymdp_policy_posterior_grid_schema"] = (
            posterior.get("schema") == "template_active_inference.pymdp_policy_posterior_grid.v1"
            and bool(rows)
            and posterior.get("scope") == "comparison_only"
            and posterior.get("all_available_posteriors_normalized") is True
            and posterior.get("all_unavailable_rows_explained") is True
            and actual_cells
            == {
                (planner, seed)
                for planner in cfg.validation_comparison.planners
                for seed in cfg.validation_comparison.seeds
            }
            and all(row.get("horizon") == cfg.planning_horizon for row in rows)
            and all(
                (not row.get("posterior_available")) or abs(float(sum(row.get("q_pi") or [])) - 1.0) <= 1e-9
                for row in rows
            )
        )
    runtime_path = root / "output" / "reports" / "pymdp_runtime_diagnostics.json"
    if runtime_path.exists():
        from simulation.pymdp_runtime import _runtime_rows_explained, validate_runtime_diagnostics

        runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
        _runtime_rows = runtime.get("rows") or []
        checks["pymdp_runtime_diagnostics_schema"] = (
            runtime.get("schema") == "template_active_inference.pymdp_runtime_diagnostics.v1"
            and runtime.get("ok") is True
            and int(runtime.get("unexpected_warning_count", 0) or 0) == 0
            # Re-derive the categorized-row contract from rows (never trust the
            # stored all_rows_explained boolean); empty rows fail closed.
            and runtime.get("all_rows_explained") is True
            and _runtime_rows_explained(_runtime_rows)
            and not validate_runtime_diagnostics(root)
        )

    graph_summary_path = root / "output" / "data" / "si_graph_world_summary.json"
    graph_trace_path = root / "output" / "data" / "si_graph_world_trace.json"
    if graph_summary_path.exists() and graph_trace_path.exists():
        graph_summary = json.loads(graph_summary_path.read_text(encoding="utf-8"))
        graph_trace = json.loads(graph_trace_path.read_text(encoding="utf-8"))
        checks["si_graph_world_schema"] = (
            graph_summary.get("status") == "ok"
            and graph_summary.get("goal_reached") is True
            and len(graph_trace.get("steps") or []) == int(graph_summary.get("steps", 0))
            and "not_implemented" not in json.dumps(graph_summary)
        )

    crosswalk_path = root / "output" / "data" / "sheaf_evidence_crosswalk.json"
    dependency_path = root / "output" / "data" / "validation_dependency_graph.json"
    if crosswalk_path.exists():
        crosswalk = json.loads(crosswalk_path.read_text(encoding="utf-8"))
        checks["sheaf_evidence_crosswalk_schema"] = crosswalk.get(
            "schema"
        ) == "template_active_inference.evidence_crosswalk.v1" and int(crosswalk.get("claim_count", 0)) == len(
            crosswalk.get("claims") or []
        )
    if dependency_path.exists():
        dependency = json.loads(dependency_path.read_text(encoding="utf-8"))
        artifacts = dependency.get("artifacts") or {}
        checks["validation_dependency_graph_schema"] = (
            dependency.get("schema") == "template_active_inference.validation_dependency_graph.v1"
            and not dependency.get("issues")
            and bool(artifacts.get("output/data/sheaf_gluing_certificate.json"))
            and bool(artifacts.get("output/figures/si_belief_trajectory.gif"))
        )

    provenance_path = root / "output" / "data" / "artifact_provenance.json"
    replay_path = root / "output" / "reports" / "reproducibility_replay.json"
    counterexample_path = root / "output" / "reports" / "counterexample_matrix.json"
    if provenance_path.exists():
        from validation_spine import validate_artifact_provenance

        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        checks["artifact_provenance_schema"] = (
            provenance.get("schema") == "template_active_inference.artifact_provenance.v1"
            and provenance.get("all_hashed") is True
            and provenance.get("all_seeded") is True
            and provenance.get("all_config_digests") is True
            and provenance.get("all_source_commits") is True
            and provenance.get("all_producers_configured") is True
            # AI-PROVENANCE-FIELDS-1: field-level lineage must be present and the
            # per-field hashes re-derive (the validator below re-hashes each field
            # from disk; the flag here is a presence guard, the validator is truth).
            and provenance.get("all_field_hashes_present") is True
            and not validate_artifact_provenance(root)
        )
    if replay_path.exists():
        from validation_spine import validate_reproducibility_replay

        replay = json.loads(replay_path.read_text(encoding="utf-8"))
        checks["reproducibility_replay_schema"] = (
            replay.get("schema") == "template_active_inference.reproducibility_replay.v1"
            and replay.get("all_passed") is True
            and not validate_reproducibility_replay(root)
        )
    if counterexample_path.exists():
        from validation_spine import validate_counterexample_matrix

        counterexamples = json.loads(counterexample_path.read_text(encoding="utf-8"))
        checks["counterexample_matrix_schema"] = (
            counterexamples.get("schema") == "template_active_inference.counterexample_matrix.v1"
            and counterexamples.get("all_expected_failures_documented") is True
            and not validate_counterexample_matrix(root)
        )

    from roadmap_tracks import (
        validate_formal_interop_artifacts,
        validate_integration_audit_artifacts,
        validate_sheaf_track_artifacts,
        validate_toy_sweep_artifacts,
    )

    sensitivity = _read_json(root / "output" / "data" / "sensitivity_sweep.json")
    uncertainty = _read_json(root / "output" / "data" / "uncertainty_summary.json")
    benchmark = _read_json(root / "output" / "data" / "toy_benchmark_matrix.json")
    policy_grid = _read_json(root / "output" / "data" / "si_policy_grid.json")
    efe_terms = _read_json(root / "output" / "data" / "si_efe_terms.json")
    topology = _read_json(root / "output" / "data" / "si_graph_world_topology_sweep.json")
    topology_traces = _read_json(root / "output" / "data" / "si_graph_world_topology_traces.json")
    graph_invariants = _read_json(root / "output" / "reports" / "graph_world_invariants.json")
    observable = _read_json(root / "output" / "data" / "analytical_observable_sweep.json")
    model_checking = _read_json(root / "output" / "reports" / "model_checking_witnesses.json")
    interop = _read_json(root / "output" / "data" / "interop_roundtrip_report.json")
    gnn_roundtrip = _read_json(root / "output" / "data" / "gnn_roundtrip_report.json")
    gnn_lint = _read_json(root / "output" / "reports" / "gnn_lint_report.json")
    ontology_alias = _read_json(root / "output" / "data" / "ontology_alias_index.json")
    ontology_profile = _read_json(root / "output" / "data" / "ontology_profile_matrix.json")
    lean_theorems = _read_json(root / "output" / "reports" / "lean_theorem_inventory.json")
    lean_graph = _read_json(root / "output" / "reports" / "lean_graph_world_inventory.json")
    producer_completeness = _read_json(root / "output" / "reports" / "producer_completeness.json")
    stale_report = _read_json(root / "output" / "reports" / "stale_artifact_report.json")
    manuscript_staleness = _read_json(root / "output" / "reports" / "manuscript_staleness_report.json")
    cross_symbols = _read_json(root / "output" / "data" / "cross_track_symbol_table.json")
    evidence_tables = _read_json(root / "output" / "data" / "manuscript_evidence_tables.json")
    token_provenance = _read_json(root / "output" / "data" / "manuscript_token_provenance.json")
    hardcoded_variables = _read_json(root / "output" / "reports" / "manuscript_hardcoded_variable_audit.json")
    claim_audit = _read_json(root / "output" / "reports" / "claim_evidence_audit.json")
    gate_index = _read_json(root / "output" / "data" / "validation_gate_index.json")
    section_status = _read_json(root / "output" / "data" / "sheaf_section_status_matrix.json")
    render_log = _read_json(root / "output" / "reports" / "sheaf_render_log.json")
    figure_source = _read_json(root / "output" / "data" / "figure_source_map.json")
    figure_hash = _read_json(root / "output" / "reports" / "figure_hash_manifest.json")
    visualization_quality = _read_json(root / "output" / "reports" / "visualization_quality_audit.json")
    scope = _read_json(root / "output" / "reports" / "scope_boundary_audit.json")
    adversarial = _read_json(root / "output" / "reports" / "adversarial_audit.json")
    assumptions = _read_json(root / "output" / "data" / "analytical_assumption_index.json")
    animation_deltas = _read_json(root / "output" / "data" / "animation_frame_deltas.json")
    replay_matrix = _read_json(root / "output" / "reports" / "replay_matrix.json")
    track_scope = _read_json(root / "output" / "data" / "track_improvement_scope.json")
    blocked_scope = _read_json(root / "output" / "reports" / "blocked_scope_manifest.json")
    evidence_fields = _read_json(root / "output" / "data" / "evidence_field_index.json")
    release_bundle = _read_json(root / "output" / "reports" / "release_bundle_manifest.json")
    theorem_traceability = _read_json(root / "output" / "data" / "theorem_traceability_matrix.json")
    artifact_diffoscope = _read_json(root / "output" / "reports" / "artifact_diffoscope.json")
    proof_extraction = _read_json(root / "output" / "data" / "proof_extraction_index.json")
    state_space_catalog = _read_json(root / "output" / "data" / "state_space_catalog.json")
    causal_ablation = _read_json(root / "output" / "data" / "causal_ablation_matrix.json")
    artifact_license = _read_json(root / "output" / "reports" / "artifact_license_audit.json")
    release_notes = _read_json(root / "output" / "reports" / "release_notes_evidence.json")
    scholarship = _read_json(root / "output" / "data" / "scholarship_source_matrix.json")
    fp_divergence = _read_json(root / "output" / "data" / "firstprinciples" / "divergence_demo.json")
    fp_exposure = _read_json(root / "output" / "data" / "firstprinciples" / "exposure_bias_demo.json")
    fp_classroom = _read_json(root / "output" / "data" / "firstprinciples" / "classroom.json")
    fp_sequential_shift = _read_json(root / "output" / "data" / "firstprinciples" / "sequential_shift.json")
    fp_sequential_sensitivity = _read_json(
        root / "output" / "data" / "firstprinciples" / "sequential_shift_sensitivity.json"
    )
    fp_taxonomy = _read_json(root / "output" / "data" / "firstprinciples" / "opd_taxonomy.json")
    fp_statistics = _read_json(root / "output" / "data" / "firstprinciples" / "statistics_demo.json")
    fp_empirical = _read_json(root / "output" / "data" / "firstprinciples" / "empirical_benchmark.json")
    fp_benchmark_table_path = root / "output" / "data" / "firstprinciples" / "benchmark_table.md"
    proof_dependency = _read_json(root / "output" / "data" / "proof_dependency_graph.json")
    transition_table = _read_json(root / "output" / "data" / "state_transition_table.json")
    ablation_sensitivity = _read_json(root / "output" / "reports" / "ablation_sensitivity_report.json")
    release_attestation = _read_json(root / "output" / "reports" / "release_attestation.json")

    checks["analytical_observable_sweep_schema"] = (
        observable.get("schema") == "template_active_inference.analytical_observable_sweep.v1"
        and float(observable.get("max_abs_residual", 1.0)) <= 1e-12
    )
    checks["analytical_assumption_index_schema"] = (
        assumptions.get("schema") == "template_active_inference.analytical_assumption_index.v1"
        and assumptions.get("all_equations_indexed") is True
    )
    checks["sensitivity_sweep_schema"] = (
        sensitivity.get("schema") == "template_active_inference.sensitivity_sweep.v1"
        and sensitivity.get("complete_grid") is True
    )
    checks["uncertainty_summary_schema"] = (
        uncertainty.get("schema") == "template_active_inference.uncertainty_summary.v1"
        and uncertainty.get("all_normalized") is True
    )
    checks["toy_benchmark_matrix_schema"] = (
        benchmark.get("schema") == "template_active_inference.toy_benchmark_matrix.v1"
        and benchmark.get("all_models_complete") is True
    )
    checks["si_policy_grid_schema"] = policy_grid.get("complete_grid") is True
    checks["si_efe_terms_schema"] = (
        efe_terms.get("schema") == "template_active_inference.si_efe_values.v1"
        and efe_terms.get("all_rows_explained") is True
        and efe_terms.get("all_rows_explained") == _efe_values_explained(efe_terms)
    )
    checks["si_graph_world_topology_sweep_schema"] = topology.get("all_summary_trace_agree") is True
    checks["si_graph_world_topology_traces_schema"] = (
        topology_traces.get("schema") == "template_active_inference.si_graph_world_topology_traces.v1"
        and topology_traces.get("all_trace_summary_agree") is True
        and topology_traces.get("topology_count") == topology.get("topology_count")
    )
    checks["graph_world_invariants_schema"] = graph_invariants.get("all_passed") is True
    checks["model_checking_witnesses_schema"] = (
        model_checking.get("schema") == "template_active_inference.model_checking_witnesses.v1"
        and model_checking.get("all_passed") is True
    )
    checks["interop_roundtrip_schema"] = (
        interop.get("schema") == "template_active_inference.interop_roundtrip_report.v1"
        and interop.get("all_lossless") is True
    )
    checks["gnn_roundtrip_schema"] = gnn_roundtrip.get("all_lossless") is True
    _gnn_lint_rows = gnn_lint.get("rows") or []
    checks["gnn_lint_schema"] = (
        gnn_lint.get("all_variables_mapped_once") is True
        # Re-derive the per-variable round-trip contract from rows (never trust the
        # stored boolean); empty rows fail closed.
        and gnn_lint.get("all_round_trip_ok") is True
        and bool(_gnn_lint_rows)
        and all(row.get("round_trip_ok") is True for row in _gnn_lint_rows)
    )
    checks["ontology_alias_schema"] = ontology_alias.get("no_conflicts") is True
    checks["ontology_profile_schema"] = _ontology_profile_ok(ontology_profile)
    checks["lean_theorem_inventory_schema"] = lean_theorems.get("all_proved") is True
    checks["lean_graph_world_inventory_schema"] = lean_graph.get("all_topologies_witnessed") is True
    checks["lean_graph_world_inventory_schema"] = (
        checks["lean_graph_world_inventory_schema"]
        and lean_graph.get("all_policy_witnesses_present") is True
        and int(lean_graph.get("topology_count", 0) or 0) == int(topology.get("topology_count", 0) or 0)
    )
    checks["producer_completeness_schema"] = producer_completeness.get("all_complete") is True
    checks["stale_artifact_report_schema"] = stale_report.get("all_fresh") is True
    checks["manuscript_staleness_report_schema"] = (
        manuscript_staleness.get("schema") == "template_active_inference.manuscript_staleness_report.v1"
        and manuscript_staleness.get("all_fresh") is True
    )
    checks["cross_track_symbol_table_schema"] = _cross_track_symbol_table_ok(cross_symbols)
    checks["manuscript_evidence_tables_schema"] = evidence_tables.get("all_source_backed") is True
    checks["manuscript_token_provenance_schema"] = token_provenance.get("all_tokens_mapped") is True
    checks["manuscript_hardcoded_variable_audit_schema"] = (
        hardcoded_variables.get("schema") == "template_active_inference.hardcoded_variable_audit.v1"
        and hardcoded_variables.get("all_values_auto_injected") is True
        and int(hardcoded_variables.get("issue_count", 0) or 0) == 0
    )
    checks["claim_evidence_audit_schema"] = claim_audit.get("all_claims_typed") is True
    from roadmap_tracks.integration_audit_builders import _rows_fully_specified as _gi_rows_fully_specified

    _gi_rows = gate_index.get("rows") or []
    checks["validation_gate_index_schema"] = (
        gate_index.get("all_indexed") is True
        and gate_index.get("all_rows_fully_specified") is True
        # Re-derive at gate time from the rows, never trust the stored flag: a
        # blanked command/output/negative_control with the flag left true is caught.
        and gate_index.get("all_rows_fully_specified") == _gi_rows_fully_specified(_gi_rows)
    )
    checks["sheaf_section_status_matrix_schema"] = (
        section_status.get("schema") == "template_active_inference.sheaf_section_status_matrix.v1"
        and section_status.get("all_bound_fragments_present") is True
        and section_status.get("all_sections_have_status") is True
        and section_status.get("all_tracks_have_status") is True
        and int(section_status.get("cell_count", 0) or 0) > 0
    )
    checks["sheaf_render_log_schema"] = (
        render_log.get("schema") == "template_active_inference.sheaf_render_log.v1"
        and render_log.get("all_events_ok") is True
        and int(render_log.get("event_count", 0) or 0) > 0
    )
    checks["figure_source_map_schema"] = _figure_source_map_ok(root, figure_source)
    checks["figure_hash_manifest_schema"] = _figure_hash_manifest_ok(root, figure_hash)
    checks["visualization_quality_audit_schema"] = _visualization_quality_audit_ok(root, visualization_quality)
    checks["figure_output_integrity"] = _figure_output_integrity_ok(root)
    checks["scope_boundary_audit_schema"] = scope.get("scope_boundary_status") == "toy_only_pass"
    checks["adversarial_audit_schema"] = (
        adversarial.get("all_expected_failures_documented") is True
        and adversarial.get("all_expected_failures_observed") is True
        and int(adversarial.get("known_bad_rows_passed", 0) or 0) == 0
    )
    checks["replay_matrix_schema"] = (
        replay_matrix.get("schema") == "template_active_inference.replay_matrix.v1"
        and replay_matrix.get("all_replay_rows_matched") is True
        and replay_matrix.get("all_configured_producers_represented") is True
    )
    checks["track_improvement_scope_schema"] = (
        track_scope.get("schema") == "template_active_inference.track_improvement_scope.v1"
        and track_scope.get("all_live_tracks_valid") is True
    )
    checks["blocked_scope_manifest_schema"] = (
        blocked_scope.get("schema") == "template_active_inference.blocked_scope_manifest.v1"
        and blocked_scope.get("all_blocked") is True
    )
    checks["evidence_field_index_schema"] = (
        evidence_fields.get("schema") == "template_active_inference.evidence_field_index.v1"
        and evidence_fields.get("all_fields_mapped") is True
    )
    # Parity flag re-derived from its (nested) rows at read time — the
    # aggregate_rederivation table only addresses top-level `rows`, so the
    # copied-output parity aggregate gets its flag↔rows check here (Run-6,
    # AI-RELEASE-PARITY-1).
    _parity_rows = (release_bundle.get("copied_output_parity") or {}).get("rows") or []
    _parity_rederived = bool(_parity_rows) and all(row.get("matches_when_copied") is True for row in _parity_rows)
    checks["release_bundle_manifest_schema"] = (
        release_bundle.get("schema") == "template_active_inference.release_bundle_manifest.v1"
        and release_bundle.get("all_required_sources_present") is True
        and release_bundle.get("all_copied_outputs_match_or_deferred") is True
        and _parity_rederived
    )
    checks["theorem_traceability_matrix_schema"] = (
        theorem_traceability.get("schema") == "template_active_inference.theorem_traceability_matrix.v1"
        and theorem_traceability.get("all_theorems_linked") is True
    )
    checks["artifact_diffoscope_schema"] = (
        artifact_diffoscope.get("schema") == "template_active_inference.artifact_diffoscope.v1"
        and artifact_diffoscope.get("all_equal") is True
    )
    checks["proof_extraction_index_schema"] = (
        _proof_extraction_ok(proof_extraction, lean_theorems)
    )
    checks["state_space_catalog_schema"] = (
        state_space_catalog.get("schema") == "template_active_inference.state_space_catalog.v1"
        and state_space_catalog.get("all_finite") is True
        and state_space_catalog.get("all_counts_positive") is True
    )
    checks["causal_ablation_matrix_schema"] = (
        causal_ablation.get("schema") == "template_active_inference.causal_ablation_matrix.v1"
        and causal_ablation.get("complete_grid") is True
        and causal_ablation.get("all_deterministic") is True
    )
    checks["artifact_license_audit_schema"] = (
        artifact_license.get("schema") == "template_active_inference.artifact_license_audit.v1"
        and artifact_license.get("all_license_safe") is True
    )
    checks["release_notes_evidence_schema"] = (
        release_notes.get("schema") == "template_active_inference.release_notes_evidence.v1"
        and release_notes.get("all_notes_source_backed") is True
    )
    checks["scholarship_source_matrix_schema"] = (
        scholarship.get("schema") == "template_active_inference.scholarship_source_matrix.v1"
        and scholarship.get("all_sources_connected") is True
        and scholarship.get("all_expected_sources_present") is True
    )
    checks["firstprinciples_divergence_schema"] = (
        fp_divergence.get("schema") == "firstprinciples.divergence_demo.v1"
        and float(fp_divergence.get("reverse_kl", -1.0)) >= 0.0
        and float(fp_divergence.get("forward_kl", -1.0)) >= 0.0
        and bool(fp_divergence.get("teacher"))
        and bool(fp_divergence.get("student"))
    )
    exposure_gap = fp_exposure.get("gap") or {}
    checks["firstprinciples_exposure_bias_schema"] = (
        fp_exposure.get("schema") == "firstprinciples.exposure_bias_demo.v1"
        and exposure_gap.get("off_policy_collapses") is True
        and float(exposure_gap.get("terminal_gap", -1.0)) > 0.0
    )
    checks["firstprinciples_classroom_schema"] = _firstprinciples_classroom_ok(fp_classroom)
    checks["firstprinciples_sequential_shift_schema"] = _firstprinciples_sequential_shift_ok(fp_sequential_shift)
    checks["firstprinciples_sequential_shift_sensitivity_schema"] = (
        _firstprinciples_sequential_shift_sensitivity_ok(fp_sequential_sensitivity)
    )
    checks["firstprinciples_taxonomy_schema"] = _firstprinciples_taxonomy_ok(fp_taxonomy)
    checks["firstprinciples_empirical_benchmark_schema"] = _firstprinciples_empirical_benchmark_ok(fp_empirical)
    checks["firstprinciples_statistics_schema"] = _firstprinciples_statistics_ok(root, fp_statistics)
    fp_privilege = _read_json(root / "output" / "data" / "firstprinciples" / "privilege_sweep.json")
    checks["firstprinciples_privilege_sweep_schema"] = (
        fp_privilege.get("schema") == "firstprinciples.privilege_sweep.v1"
        and len(fp_privilege.get("levels") or []) >= 2
        and fp_privilege.get("h1_entropy_falls_with_privilege") is True
        and fp_privilege.get("h3_gap_grows_with_privilege") is True
        and fp_privilege.get("h4_baseline_gap_zero") is True
    )
    fp_benchmark_table = (
        fp_benchmark_table_path.read_text(encoding="utf-8") if fp_benchmark_table_path.is_file() else ""
    )
    checks["firstprinciples_benchmark_table_present"] = (
        fp_benchmark_table_path.is_file()
        and "qwen2025technical_report" in fp_benchmark_table
        and "thinkingmachines2025opd" in fp_benchmark_table
        and "AIME'24" in fp_benchmark_table
    )
    checks["proof_dependency_graph_schema"] = (
        proof_dependency.get("schema") == "template_active_inference.proof_dependency_graph.v1"
        and proof_dependency.get("all_theorems_have_dependencies") is True
        and proof_dependency.get("all_edges_resolved") is True
        and proof_dependency.get("all_edge_keys_unique") is True
        and proof_dependency.get("duplicate_edge_keys") == []
        and proof_dependency.get("all_required_edge_types_present") is True
        and proof_dependency.get("all_edge_targets_resolved") is True
        and proof_dependency.get("orphan_edge_targets") == []
    )
    checks["state_transition_table_schema"] = (
        transition_table.get("schema") == "template_active_inference.state_transition_table.v1"
        and transition_table.get("all_transitions_deterministic") is True
        and transition_table.get("all_transition_keys_unique") is True
        and transition_table.get("duplicate_transition_keys") == []
        and transition_table.get("all_reachable_states_covered") is True
        and transition_table.get("all_reachable_states_have_outgoing") is True
        and transition_table.get("missing_outgoing_state_keys") == []
        and transition_table.get("all_terminal_states_have_self_transition") is True
        and transition_table.get("models_without_terminal_self_transition") == []
    )
    checks["ablation_sensitivity_report_schema"] = (
        ablation_sensitivity.get("schema") == "template_active_inference.ablation_sensitivity_report.v1"
        and ablation_sensitivity.get("all_effects_source_backed") is True
        and ablation_sensitivity.get("all_ablation_rows_joined") is True
        and ablation_sensitivity.get("source_row_count_agreement") is True
        and ablation_sensitivity.get("row_count") == ablation_sensitivity.get("ablation_source_row_count")
    )
    _attest_rows = {str(row.get("id")): row for row in release_attestation.get("rows") or []}
    _validation_row = _attest_rows.get("validation_report") or {}
    _report_path = root / "output" / "reports" / "validation_report.json"
    if _report_path.is_file() and _validation_row and not _validation_row.get("deferred_until_validation"):
        import hashlib as _hashlib

        # Hash currency: the attestation must refer to the validation report
        # actually on disk — a stale attested report cannot certify this tree.
        _attestation_current = _validation_row.get("report_sha256") == _hashlib.sha256(
            _report_path.read_bytes()
        ).hexdigest()
    else:
        # Before the first-ever validate the row is deferred; currency is moot.
        _attestation_current = bool(_validation_row.get("deferred_until_validation", not _attest_rows))
    checks["release_attestation_schema"] = (
        release_attestation.get("schema") == "template_active_inference.release_attestation.v1"
        and release_attestation.get("all_attested") is True
        and release_attestation.get("attested_source_count") == len(_attest_rows)
        and release_attestation.get("attested_validation_check_count", 0) > 0
        and _attestation_current
    )
    from visualizations.animation import validate_animation_frame_deltas

    _animation_rows = animation_deltas.get("rows") or []
    checks["animation_frame_deltas_schema"] = (
        animation_deltas.get("schema") == "template_active_inference.animation_frame_deltas.v1"
        and animation_deltas.get("all_nonzero") is True
        # Re-derive the duplicate/static-frame guard from rows (never trust the
        # stored boolean); empty rows must not vacuously pass.
        and animation_deltas.get("all_hashes_distinct") is True
        and bool(_animation_rows)
        and all(row.get("hashes_differ") is True for row in _animation_rows)
        and not validate_animation_frame_deltas(root)
    )
    checks["toy_sweep_track_schemas"] = not validate_toy_sweep_artifacts(root)
    checks["formal_interop_track_schemas"] = not validate_formal_interop_artifacts(root)
    checks["integration_audit_track_schemas"] = not validate_integration_audit_artifacts(root)
    checks["canonical_sheaf_track_schemas"] = not validate_sheaf_track_artifacts(root)

    # Read-time honesty: every covered stored all_* aggregate must equal its
    # row-level re-derivation (gates.aggregate_rederivation — AI-STALE-SUMMARY-1).
    from gates.aggregate_rederivation import aggregates_consistent

    checks["aggregate_rederivation"] = aggregates_consistent(root)

    # Read-time honesty: every gate-index row must bind to a check key this
    # run actually produced (or a known external gate) — AI-GATE-INDEX-3.
    checks["validation_gate_index_binding"] = _gate_index_binding(gate_index, set(checks))

    log_path = root / "output" / "logs" / "pymdp_runs.jsonl"
    if _pymdp_logging_expected(root):
        checks["si_log_present"] = log_path.exists() and any(
            line.strip() for line in log_path.read_text(encoding="utf-8").splitlines()
        )

    checks["experiment_plan_metrics"] = checks.get("invariants_all_pass", False) and checks.get(
        str(summary_path.relative_to(root)),
        False,
    )
    if si_summary_present:
        checks["experiment_plan_metrics"] = (
            checks["experiment_plan_metrics"]
            and checks.get("si_summary_schema", False)
            and checks.get("si_invariants_all_pass", False)
        )
    if comparison_path.exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "si_policy_comparison_schema",
            False,
        )
    if graph_summary_path.exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "si_graph_world_schema",
            False,
        )
    if crosswalk_path.exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "sheaf_evidence_crosswalk_schema",
            False,
        )
    if dependency_path.exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "validation_dependency_graph_schema",
            False,
        )
    if provenance_path.exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "artifact_provenance_schema",
            False,
        )
    if replay_path.exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "reproducibility_replay_schema",
            False,
        )
    if counterexample_path.exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "counterexample_matrix_schema",
            False,
        )
    checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and all(
        checks.get(key, False)
        for key in (
            "toy_sweep_track_schemas",
            "formal_interop_track_schemas",
            "integration_audit_track_schemas",
            "animation_frame_deltas_schema",
            "pymdp_policy_posterior_grid_schema",
            "pymdp_runtime_diagnostics_schema",
            "si_graph_world_topology_traces_schema",
            "canonical_sheaf_track_schemas",
            "sheaf_section_status_matrix_schema",
            "sheaf_render_log_schema",
            "figure_source_map_schema",
            "figure_hash_manifest_schema",
            "visualization_quality_audit_schema",
            "figure_output_integrity",
            "artifact_diffoscope_schema",
            "proof_extraction_index_schema",
            "state_space_catalog_schema",
            "causal_ablation_matrix_schema",
            "artifact_license_audit_schema",
            "release_notes_evidence_schema",
            "scholarship_source_matrix_schema",
            "firstprinciples_empirical_benchmark_schema",
            "firstprinciples_statistics_schema",
            "firstprinciples_privilege_sweep_schema",
            "firstprinciples_sequential_shift_sensitivity_schema",
            "firstprinciples_benchmark_table_present",
            "proof_dependency_graph_schema",
            "state_transition_table_schema",
            "ablation_sensitivity_report_schema",
            "release_attestation_schema",
        )
    )

    return checks
