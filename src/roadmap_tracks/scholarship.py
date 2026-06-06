"""Source-backed scholarship matrix for the active-inference exemplar."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

SCHOLARSHIP_SCHEMA = "template_active_inference.scholarship_source_matrix.v1"

EXPECTED_SCHOLARSHIP_KEYS: tuple[str, ...] = (
    "friston2010fep",
    "buckley2017mathreview",
    "dacosta2020discrete",
    "friston2019generalised",
    "parr2019generalised",
    "millidge2020efe",
    "parr2022active",
    "smith2022tutorial",
    "hinton2015distilling",
    "ross2011dagger",
    "bengio2015scheduled",
    "gu2024minillm",
    "agarwal2024gkd",
    "thinkingmachines2025opd",
    "vapnik2009lupi",
    "lopezpaz2016unifying",
    "zhao2026opsd",
    "shenfeld2026sdft",
    "hubotter2026sdpo",
    "liu2026sdpg",
    "lauyikfung2026sdpgcode",
    "penaloza2026pidistill",
    "penaloza2026tutorial",
    "levine2018rlinference",
    "abdolmaleki2018mpo",
    "awesomeopd2026",
    "song2026opdsurvey",
    "zhu2026manyfacesopd",
    "ramos2026dgrpo",
    "liu2026oisd",
    "pymdp2024",
    "gnn2023",
    "curry2014sheaves",
    "robinson2014topological",
)

SCHOLARSHIP_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "citation_key": "friston2010fep",
        "source_kind": "primary_article",
        "source_family": "free_energy_principle",
        "method_role": "scope_background",
        "tracks": ["prose", "formalism", "scholarship"],
        "artifact": "output/data/scholarship_source_matrix.json",
        "manuscript_sections": ["intro_motivation", "methods_sheaf"],
        "claim_boundary": "background only; no empirical biological claim is inferred",
    },
    {
        "citation_key": "buckley2017mathreview",
        "source_kind": "mathematical_review",
        "source_family": "free_energy_principle",
        "method_role": "mathematical_review",
        "tracks": ["formalism", "scholarship"],
        "artifact": "output/data/analytical_assumption_index.json",
        "manuscript_sections": ["methods_analytical", "appendix_full_sheaf"],
        "claim_boundary": "supports finite variational-free-energy notation only",
    },
    {
        "citation_key": "dacosta2020discrete",
        "source_kind": "primary_article",
        "source_family": "discrete_state_space_active_inference",
        "method_role": "discrete_planning_formalism",
        "tracks": ["pymdp", "model_checking", "scholarship"],
        "artifact": "output/reports/model_checking_witnesses.json",
        "manuscript_sections": ["methods_pymdp", "methods_lean"],
        "claim_boundary": "finite toy state spaces only",
    },
    {
        "citation_key": "friston2019generalised",
        "source_kind": "primary_article",
        "source_family": "sophisticated_inference",
        "method_role": "recursive_expected_free_energy_planning",
        "tracks": ["pymdp", "formalism", "scholarship"],
        "artifact": "output/data/si_tmaze_summary.json",
        "manuscript_sections": ["methods_pymdp", "results_si_tmaze"],
        "claim_boundary": "planning-depth context only; local rollout supplies the measured evidence",
    },
    {
        "citation_key": "parr2019generalised",
        "source_kind": "primary_article",
        "source_family": "generalised_free_energy",
        "method_role": "future_free_energy_context",
        "tracks": ["formalism", "scholarship"],
        "artifact": "output/data/firstprinciples/reward_tilting_demo.json",
        "manuscript_sections": ["methods_analytical", "discussion_outlook"],
        "claim_boundary": "unifies free-energy framing; toy reward tilt is generated locally",
    },
    {
        "citation_key": "millidge2020efe",
        "source_kind": "primary_preprint",
        "source_family": "expected_free_energy",
        "method_role": "epistemic_pragmatic_decomposition",
        "tracks": ["formalism", "pymdp", "scholarship"],
        "artifact": "output/data/firstprinciples/reward_tilting_demo.json",
        "manuscript_sections": ["methods_pymdp", "results_free_energy"],
        "claim_boundary": "EFE decomposition context only; no new empirical result is inferred",
    },
    {
        "citation_key": "parr2022active",
        "source_kind": "monograph",
        "source_family": "active_inference",
        "method_role": "conceptual_reference",
        "tracks": ["prose", "uncertainty", "scholarship"],
        "artifact": "output/data/uncertainty_summary.json",
        "manuscript_sections": ["intro_motivation", "results_invariants"],
        "claim_boundary": "conceptual context, not evidence for toy metrics",
    },
    {
        "citation_key": "smith2022tutorial",
        "source_kind": "tutorial_article",
        "source_family": "active_inference_practice",
        "method_role": "model_building_tutorial",
        "tracks": ["pymdp", "scholarship"],
        "artifact": "output/data/si_policy_grid.json",
        "manuscript_sections": ["methods_pymdp", "results_si_tmaze"],
        "claim_boundary": "empirical fitting is out of scope until an adapter is promoted",
    },
    {
        "citation_key": "hinton2015distilling",
        "source_kind": "primary_preprint",
        "source_family": "knowledge_distillation",
        "method_role": "off_policy_distillation_baseline",
        "tracks": ["prose", "scholarship"],
        "artifact": "output/data/firstprinciples/opd_taxonomy.json",
        "manuscript_sections": ["intro_motivation", "discussion_outlook"],
        "claim_boundary": "classical distillation baseline only; no OPD efficiency claim is inferred",
    },
    {
        "citation_key": "ross2011dagger",
        "source_kind": "primary_conference",
        "source_family": "interactive_imitation_learning",
        "method_role": "induced_distribution_shift",
        "tracks": ["prose", "scholarship"],
        "artifact": "output/data/firstprinciples/exposure_bias_demo.json",
        "manuscript_sections": ["intro_motivation", "discussion_outlook"],
        "claim_boundary": "sequential prediction lineage only; toy curves are generated locally",
    },
    {
        "citation_key": "bengio2015scheduled",
        "source_kind": "primary_conference",
        "source_family": "sequence_exposure_bias",
        "method_role": "training_inference_mismatch",
        "tracks": ["prose", "scholarship"],
        "artifact": "output/data/firstprinciples/exposure_bias_demo.json",
        "manuscript_sections": ["intro_motivation", "discussion_outlook"],
        "claim_boundary": "exposure-bias lineage only; not evidence for OPD toy metrics",
    },
    {
        "citation_key": "gu2024minillm",
        "source_kind": "primary_conference",
        "source_family": "reverse_kl_distillation",
        "method_role": "mode_seeking_distillation",
        "tracks": ["formalism", "scholarship"],
        "artifact": "output/data/firstprinciples/opd_taxonomy.json",
        "manuscript_sections": ["methods_analytical", "results_mi_sweep"],
        "claim_boundary": "reverse-KL distillation lineage only; no production-scale metric is inferred",
    },
    {
        "citation_key": "agarwal2024gkd",
        "source_kind": "primary_conference",
        "source_family": "on_policy_distillation",
        "method_role": "student_rollout_distillation",
        "tracks": ["prose", "pymdp", "scholarship"],
        "artifact": "output/data/firstprinciples/opd_taxonomy.json",
        "manuscript_sections": ["intro_contributions", "methods_pymdp"],
        "claim_boundary": "supports OPD framing; toy measurements remain local artifacts",
    },
    {
        "citation_key": "thinkingmachines2025opd",
        "source_kind": "industry_report",
        "source_family": "on_policy_distillation",
        "method_role": "external_efficiency_context",
        "tracks": ["prose", "scholarship"],
        "artifact": "output/data/firstprinciples/opd_taxonomy.json",
        "manuscript_sections": ["intro_motivation", "discussion_outlook"],
        "claim_boundary": "external context only; not a peer-reviewed proof or toy-model result",
    },
    {
        "citation_key": "vapnik2009lupi",
        "source_kind": "primary_article",
        "source_family": "privileged_information",
        "method_role": "privileged_information_foundation",
        "tracks": ["prose", "scholarship"],
        "artifact": "output/data/firstprinciples/correspondence_map.json",
        "manuscript_sections": ["intro_motivation", "methods_analytical"],
        "claim_boundary": "training-time privileged-information analogy only",
    },
    {
        "citation_key": "lopezpaz2016unifying",
        "source_kind": "primary_conference",
        "source_family": "privileged_information",
        "method_role": "distillation_lupi_bridge",
        "tracks": ["prose", "scholarship"],
        "artifact": "output/data/firstprinciples/correspondence_map.json",
        "manuscript_sections": ["intro_motivation", "methods_analytical"],
        "claim_boundary": "bridges distillation and privileged information; does not validate AI equivalence",
    },
    {
        "citation_key": "zhao2026opsd",
        "source_kind": "primary_preprint",
        "source_family": "self_distillation",
        "method_role": "verified_trace_self_distillation",
        "tracks": ["prose", "pymdp", "scholarship"],
        "artifact": "output/data/firstprinciples/opd_taxonomy.json",
        "manuscript_sections": ["methods_pymdp", "results_si_tmaze"],
        "claim_boundary": "self-distillation lineage only; no production benchmark is reproduced",
    },
    {
        "citation_key": "shenfeld2026sdft",
        "source_kind": "primary_preprint",
        "source_family": "self_distillation",
        "method_role": "continual_learning_context",
        "tracks": ["prose", "scholarship"],
        "artifact": "output/data/firstprinciples/opd_taxonomy.json",
        "manuscript_sections": ["intro_motivation", "discussion_outlook"],
        "claim_boundary": "continual-learning analogy only; no forgetting experiment is run here",
    },
    {
        "citation_key": "hubotter2026sdpo",
        "source_kind": "primary_preprint",
        "source_family": "self_distillation",
        "method_role": "feedback_conditioning_context",
        "tracks": ["prose", "scholarship"],
        "artifact": "output/data/firstprinciples/opd_taxonomy.json",
        "manuscript_sections": ["results_si_tmaze", "discussion_outlook"],
        "claim_boundary": "feedback-conditioning analogy only",
    },
    {
        "citation_key": "liu2026sdpg",
        "source_kind": "primary_preprint",
        "source_family": "self_distillation",
        "method_role": "policy_gradient_self_distillation",
        "tracks": ["prose", "scholarship"],
        "artifact": "output/data/firstprinciples/sdpg_demo.json",
        "manuscript_sections": ["intro_contributions", "discussion_outlook"],
        "claim_boundary": "objective-structure analogy only; local demo is finite and deterministic",
    },
    {
        "citation_key": "lauyikfung2026sdpgcode",
        "source_kind": "primary_repository",
        "source_family": "self_distillation",
        "method_role": "sdpg_reference_implementation",
        "tracks": ["prose", "scholarship"],
        "artifact": "output/data/firstprinciples/sdpg_demo.json",
        "manuscript_sections": ["intro_contributions", "discussion_outlook"],
        "claim_boundary": "implementation context for the objective shape; no benchmark is reproduced",
    },
    {
        "citation_key": "penaloza2026pidistill",
        "source_kind": "primary_preprint",
        "source_family": "privileged_information",
        "method_role": "variational_em_privileged_distillation",
        "tracks": ["prose", "scholarship"],
        "artifact": "output/data/firstprinciples/correspondence_map.json",
        "manuscript_sections": ["intro_motivation", "results_si_tmaze"],
        "claim_boundary": "privileged-information distillation context only",
    },
    {
        "citation_key": "penaloza2026tutorial",
        "source_kind": "tutorial",
        "source_family": "privileged_information",
        "method_role": "distillation_privileged_information_tutorial",
        "tracks": ["prose", "scholarship"],
        "artifact": "output/data/firstprinciples/correspondence_map.json",
        "manuscript_sections": ["intro_contributions", "discussion_outlook"],
        "claim_boundary": "tutorial context only; method claims come from generated correspondence rows",
    },
    {
        "citation_key": "levine2018rlinference",
        "source_kind": "tutorial_article",
        "source_family": "rl_as_probabilistic_inference",
        "method_role": "reward_tilt_bridge",
        "tracks": ["formalism", "scholarship"],
        "artifact": "output/data/firstprinciples/reward_tilting_demo.json",
        "manuscript_sections": ["intro_contributions", "discussion_outlook"],
        "claim_boundary": "probabilistic-inference bridge only; local reward target supplies the measured row",
    },
    {
        "citation_key": "abdolmaleki2018mpo",
        "source_kind": "primary_preprint",
        "source_family": "rl_as_probabilistic_inference",
        "method_role": "map_policy_optimization_context",
        "tracks": ["formalism", "scholarship"],
        "artifact": "output/data/firstprinciples/reward_tilting_demo.json",
        "manuscript_sections": ["intro_contributions", "discussion_outlook"],
        "claim_boundary": "policy-optimization context only; no MPO experiment is reproduced",
    },
    {
        "citation_key": "awesomeopd2026",
        "source_kind": "curated_repository",
        "source_family": "on_policy_distillation_landscape",
        "method_role": "landscape_taxonomy_context",
        "tracks": ["prose", "scholarship"],
        "artifact": "output/data/firstprinciples/opd_taxonomy.json",
        "manuscript_sections": ["intro_motivation", "discussion_outlook"],
        "claim_boundary": "landscape index only; not a peer-reviewed evidence source",
    },
    {
        "citation_key": "song2026opdsurvey",
        "source_kind": "survey_preprint",
        "source_family": "on_policy_distillation_landscape",
        "method_role": "opd_failure_modes_and_axes",
        "tracks": ["prose", "scholarship"],
        "artifact": "output/data/firstprinciples/opd_taxonomy.json",
        "manuscript_sections": ["intro_motivation", "discussion_outlook"],
        "claim_boundary": "survey context for OPD axes and failure modes; toy artifacts remain the evidence",
    },
    {
        "citation_key": "zhu2026manyfacesopd",
        "source_kind": "primary_preprint",
        "source_family": "on_policy_distillation_landscape",
        "method_role": "opd_failure_mechanisms",
        "tracks": ["prose", "scholarship"],
        "artifact": "output/data/firstprinciples/opd_taxonomy.json",
        "manuscript_sections": ["intro_motivation", "discussion_outlook"],
        "claim_boundary": "failure-mechanism context only; local toy gates remain the evidence",
    },
    {
        "citation_key": "ramos2026dgrpo",
        "source_kind": "primary_preprint",
        "source_family": "on_policy_optimization_distillation",
        "method_role": "long_context_policy_optimization_distillation",
        "tracks": ["prose", "scholarship"],
        "artifact": "output/data/firstprinciples/exposure_bias_demo.json",
        "manuscript_sections": ["intro_motivation", "discussion_outlook"],
        "claim_boundary": "long-context OPD/GRPO context only; no benchmark is reproduced",
    },
    {
        "citation_key": "liu2026oisd",
        "source_kind": "primary_preprint",
        "source_family": "on_policy_internal_self_distillation",
        "method_role": "internal_representation_self_distillation",
        "tracks": ["prose", "scholarship"],
        "artifact": "output/data/firstprinciples/classroom.json",
        "manuscript_sections": ["results_si_tmaze", "discussion_outlook"],
        "claim_boundary": "internal self-distillation context only; classroom metrics remain toy evidence",
    },
    {
        "citation_key": "pymdp2024",
        "source_kind": "primary_repository",
        "source_family": "pymdp_implementation",
        "method_role": "implementation_anchor",
        "tracks": ["pymdp", "interop", "scholarship"],
        "artifact": "output/reports/pymdp_runtime_diagnostics.json",
        "manuscript_sections": ["methods_pymdp", "appendix_full_sheaf"],
        "claim_boundary": "runtime construction and diagnostics only",
    },
    {
        "citation_key": "gnn2023",
        "source_kind": "primary_preprint",
        "source_family": "generalized_notation_notation",
        "method_role": "notation_anchor",
        "tracks": ["gnn", "ontology", "interop", "scholarship"],
        "artifact": "output/data/interop_roundtrip_report.json",
        "manuscript_sections": ["methods_analytical", "methods_pymdp", "appendix_full_sheaf"],
        "claim_boundary": "notation and round-trip contract only",
    },
    {
        "citation_key": "curry2014sheaves",
        "source_kind": "dissertation",
        "source_family": "cellular_sheaves",
        "method_role": "sheaf_gluing_background",
        "tracks": ["prose", "formalism", "scholarship"],
        "artifact": "output/data/sheaf_gluing_certificate.json",
        "manuscript_sections": ["methods_sheaf", "appendix_full_sheaf"],
        "claim_boundary": "finite manuscript-stalk analogy, not full sheaf cohomology",
    },
    {
        "citation_key": "robinson2014topological",
        "source_kind": "monograph",
        "source_family": "applied_sheaf_signal_processing",
        "method_role": "local_to_global_consistency",
        "tracks": ["visualization", "prose", "scholarship"],
        "artifact": "output/data/sheaf_coverage_matrix.json",
        "manuscript_sections": ["methods_sheaf", "appendix_full_sheaf"],
        "claim_boundary": "applied local/global consistency analogy only",
    },
)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _bib_entries(root: Path) -> dict[str, str]:
    path = root / "manuscript" / "references.bib"
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,(.*?)(?=\n@\w+\s*\{|\Z)", re.S)
    return {match.group(1).strip(): match.group(2) for match in pattern.finditer(text)}


def _citation_present(root: Path, key: str) -> bool:
    paths = sorted((root / "manuscript" / "sections").glob("**/*.md")) + sorted(
        path
        for path in (root / "manuscript").glob("*.md")
        if path.name not in {"99_references.md", "SYNTAX.md", "README.md", "AGENTS.md"}
    )
    needle = f"@{key}"
    return any(needle in path.read_text(encoding="utf-8") for path in paths if path.is_file())


def _registry_tracks(root: Path) -> set[str]:
    tracks = (_load_yaml(root / "manuscript" / "sheaf" / "tracks.yaml").get("tracks") or {}).keys()
    return {str(track) for track in tracks}


def _manifest_sections(root: Path) -> set[str]:
    sections = _load_yaml(root / "manuscript" / "sheaf" / "manifest.yaml").get("sections") or []
    return {str(section.get("id")) for section in sections if isinstance(section, dict) and section.get("id")}


def _has_locator(entry: str) -> bool:
    lower = entry.lower()
    return "doi" in lower or "url" in lower or "https://" in lower or "http://" in lower


def build_scholarship_source_matrix(project_root: Path) -> dict[str, Any]:
    """Build the literature-to-method traceability matrix."""
    root = project_root.resolve()
    bib_entries = _bib_entries(root)
    registry = _registry_tracks(root)
    sections = _manifest_sections(root)
    rows: list[dict[str, Any]] = []
    for source in SCHOLARSHIP_SOURCES:
        key = str(source["citation_key"])
        entry = bib_entries.get(key, "")
        artifact = str(source["artifact"])
        track_ids = [str(track) for track in source["tracks"]]
        section_ids = [str(section) for section in source["manuscript_sections"]]
        row = {
            **source,
            "bib_has_entry": bool(entry),
            "bib_has_locator": bool(entry and _has_locator(entry)),
            "cited_in_manuscript": _citation_present(root, key),
            "artifact_exists": artifact == "output/data/scholarship_source_matrix.json" or (root / artifact).is_file(),
            "tracks_registered": set(track_ids).issubset(registry),
            "sections_bound": set(section_ids).issubset(sections),
        }
        row["connected"] = all(
            bool(row[field])
            for field in (
                "bib_has_entry",
                "bib_has_locator",
                "cited_in_manuscript",
                "artifact_exists",
                "tracks_registered",
                "sections_bound",
            )
        ) and bool(row["claim_boundary"])
        rows.append(row)
    expected = set(EXPECTED_SCHOLARSHIP_KEYS)
    observed = {str(row["citation_key"]) for row in rows}
    return {
        "schema": SCHOLARSHIP_SCHEMA,
        "rows": rows,
        "source_count": len(rows),
        "expected_sources": sorted(expected),
        "observed_sources": sorted(observed),
        "method_role_count": len({str(row["method_role"]) for row in rows}),
        "source_family_count": len({str(row["source_family"]) for row in rows}),
        "primary_source_count": sum(
            1
            for row in rows
            if row["source_kind"] in {"primary_article", "primary_repository", "primary_preprint", "primary_conference"}
        ),
        "all_expected_sources_present": observed == expected,
        "all_sources_connected": bool(rows) and all(row["connected"] for row in rows),
    }


def write_scholarship_source_matrix(project_root: Path) -> Path:
    """Write the source-backed scholarship matrix."""
    root = project_root.resolve()
    return _write_json(
        root / "output" / "data" / "scholarship_source_matrix.json", build_scholarship_source_matrix(root)
    )


def validate_scholarship_source_matrix(project_root: Path) -> list[str]:
    """Validate the saved scholarship-source matrix against its row evidence."""
    root = project_root.resolve()
    payload_path = root / "output" / "data" / "scholarship_source_matrix.json"
    issues: list[str] = []
    if not payload_path.is_file():
        return ["scholarship_source_matrix.json missing"]
    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return ["scholarship_source_matrix.json is not valid JSON"]
    rows = payload.get("rows") or []
    observed = {str(row.get("citation_key")) for row in rows}
    expected = set(EXPECTED_SCHOLARSHIP_KEYS)
    if payload.get("schema") != SCHOLARSHIP_SCHEMA:
        issues.append("scholarship_source_matrix.json schema mismatch")
    if observed != expected or payload.get("all_expected_sources_present") is not True:
        issues.append("scholarship_source_matrix.json source set is incomplete")
    connected = bool(rows) and all(
        row.get("bib_has_entry")
        and row.get("bib_has_locator")
        and row.get("cited_in_manuscript")
        and row.get("artifact_exists")
        and row.get("tracks_registered")
        and row.get("sections_bound")
        and row.get("claim_boundary")
        and row.get("connected")
        for row in rows
    )
    if payload.get("all_sources_connected") is not True or payload.get("all_sources_connected") != connected:
        issues.append("scholarship_source_matrix.json has disconnected source rows")
    if int(payload.get("method_role_count", 0) or 0) < 6:
        issues.append("scholarship_source_matrix.json has too few method roles")
    return issues
