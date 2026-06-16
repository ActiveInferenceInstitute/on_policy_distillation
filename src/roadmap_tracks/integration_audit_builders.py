"""Core integration-audit builders (dependency graph, manuscript provenance, claims, gates).

Split out of :mod:`roadmap_tracks.integration_audit` to keep each module a cohesive
unit under the line-count gate. The public ``integration_audit`` module re-exports
every name defined here, so existing ``from roadmap_tracks.integration_audit import X``
imports continue to resolve unchanged.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

# Format spec must mirror the renderer in manuscript/hydrate.py (_TOKEN_RE): it
# accepts e/f/g conversions (and an optional sign), not only fixed-point `:.Nf`.
# A narrower regex here silently drops scientific-notation tokens ({{x:.1e}}) from
# token provenance and the hardcoded-variable audit, so those gates pass vacuously
# for an entire class of rendered tokens. TOKEN_MATCH_RE captures the full spec
# (group 2, e.g. ":.1e" or "") so the expected value is rendered via hydrate itself.
TOKEN_RE = re.compile(r"\{\{([a-z][a-z0-9_]*)(?::[+]?\.\d+[efg])?\}\}")
TOKEN_MATCH_RE = re.compile(r"\{\{([a-z][a-z0-9_]*)((?::[+]?\.\d+[efg])?)\}\}")
HARDCODED_AUDIT_SELF_TOKENS: frozenset[str] = frozenset(
    {
        "hardcoded_variable_guarded_count",
        "hardcoded_variable_issue_count",
        "hardcoded_variables_all_auto_injected",
    }
)
SELF_PRODUCER = "generate_integration_audit.py"
LATE_HYDRATION_PRODUCER = "z_generate_manuscript_variables.py"
SHEAF_TRACK_PRODUCER = "generate_sheaf_tracks.py"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _analysis_scripts(root: Path) -> list[str]:
    data = yaml.safe_load((root / "manuscript" / "config.yaml").read_text(encoding="utf-8")) or {}
    return [str(script) for script in ((data.get("analysis") or {}).get("scripts") or [])]


def build_integration_dependency_graph(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    from manuscript.sheaf.semantic import build_validation_dependency_graph

    base = build_validation_dependency_graph(root)
    artifacts = base.get("artifacts") or {}
    edges = list(base.get("edges") or [])
    for rel, record in artifacts.items():
        for gate in record.get("validation_gates") or []:
            edges.append({"source": gate, "target": rel, "kind": "validator_reads"})
    token_provenance = build_manuscript_token_provenance(root)
    for token in token_provenance["tokens"]:
        edges.append({"source": token["section"], "target": token["token"], "kind": "section_uses_token"})
        edges.append({"source": token["token"], "target": token["source"], "kind": "token_from_artifact"})
    edge_types = sorted({edge["kind"] for edge in edges})
    required = [
        "produces",
        "consumed_by",
        "validated_by",
        "validator_reads",
        "section_uses_token",
        "token_from_artifact",
    ]
    return {
        "schema": "template_active_inference.integration_dependency_graph.v1",
        "analysis_scripts": base.get("analysis_scripts") or [],
        "artifacts": artifacts,
        "edges": edges,
        "edge_types": edge_types,
        "required_edge_types": required,
        "all_required_edge_types_present": set(required).issubset(edge_types),
        "issues": base.get("issues") or [],
    }


def build_producer_completeness(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    from artifact_contracts import ARTIFACT_PRODUCERS

    configured = set(_analysis_scripts(root))
    rows = [
        {
            "artifact": rel,
            "producer": producer,
            "exists": (root / rel).is_file() or producer in {SELF_PRODUCER, LATE_HYDRATION_PRODUCER},
            "configured": producer in configured,
        }
        for rel, producer in sorted(ARTIFACT_PRODUCERS.items())
    ]
    return {
        "schema": "template_active_inference.producer_completeness.v1",
        "rows": rows,
        "all_complete": all(row["exists"] and row["configured"] for row in rows),
    }


def build_stale_artifact_report(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    graph = build_integration_dependency_graph(root)
    rows = []
    excluded_producers = {SELF_PRODUCER, LATE_HYDRATION_PRODUCER, SHEAF_TRACK_PRODUCER}
    for rel, record in sorted((graph.get("artifacts") or {}).items()):
        if record.get("producer") in excluded_producers:
            continue
        path = root / rel
        sha = _sha256(path) if path.is_file() else ""
        rows.append(
            {
                "artifact": rel,
                "exists": path.is_file(),
                "sha256": sha,
                "fresh": path.is_file(),
            }
        )
    return {
        "schema": "template_active_inference.stale_artifact_report.v1",
        "rows": rows,
        "excluded_producers": sorted(excluded_producers),
        "all_fresh": all(row["fresh"] for row in rows),
    }


def build_cross_track_symbol_table(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    from gnn.parser import parse_gnn_file
    from ontology.bindings import load_section_ontology

    rows = []
    domain_rows: list[dict[str, Any]] = []
    section_ontology_paths = {
        "bernoulli_toy": root / "manuscript" / "sections" / "imrad" / "methods_analytical" / "ontology.yaml",
        "si_tmaze": root / "manuscript" / "sections" / "imrad" / "methods_pymdp" / "ontology.yaml",
        "graph_world": root / "manuscript" / "sections" / "imrad" / "results_invariants" / "ontology.yaml",
    }
    for path in sorted((root / "gnn").glob("*.gnn.md")):
        model_id = path.stem.replace(".gnn", "")
        model = parse_gnn_file(path)
        section_ontology = (
            load_section_ontology(section_ontology_paths[model_id]) if model_id in section_ontology_paths else {}
        )
        for variable, var in sorted(model.variables.items()):
            gnn_term = model.ontology.get(variable)
            section_term = section_ontology.get(variable)
            term_consistent = bool(gnn_term) and bool(section_term) and gnn_term == section_term
            symbol_id = f"{model_id}:{variable}"
            rows.append(
                {
                    "model": model_id,
                    "symbol": variable,
                    "symbol_id": symbol_id,
                    "shape": list(var.dims),
                    "dtype": var.dtype,
                    "gnn_term": gnn_term,
                    "section_ontology_term": section_term,
                    "json_field": variable,
                    "lean_namespace": "OnPolicyDistillation",
                    "domains": ["gnn_variable", "ontology_term", "json_field"],
                    "consumers": [model_id, f"ontology:{section_term}", f"json:{variable}"],
                    "shape_declared": bool(var.dims),
                    "dtype_declared": bool(var.dtype),
                    "ontology_declared": bool(gnn_term),
                    "section_ontology_declared": bool(section_term),
                    "term_consistent": term_consistent,
                    "consistent": bool(var.dims and var.dtype and term_consistent),
                }
            )
            domain_rows.extend(
                [
                    {
                        "domain": "gnn_variable",
                        "symbol": symbol_id,
                        "source": path.relative_to(root).as_posix(),
                        "consumer": model_id,
                        "consistent": bool(var.dims and var.dtype and gnn_term),
                    },
                    {
                        "domain": "ontology_term",
                        "symbol": symbol_id,
                        "source": section_ontology_paths.get(model_id, path).relative_to(root).as_posix(),
                        "consumer": section_term or "",
                        "consistent": term_consistent,
                    },
                    {
                        "domain": "json_field",
                        "symbol": symbol_id,
                        "source": path.relative_to(root).as_posix(),
                        "consumer": variable,
                        "consistent": bool(variable),
                    },
                ]
            )
    lean = _load_json(root / "output" / "reports" / "lean_theorem_inventory.json")
    for row in lean.get("rows") or []:
        theorem = str(row.get("name") or "")
        if theorem:
            domain_rows.append(
                {
                    "domain": "lean_theorem",
                    "symbol": theorem,
                    "source": "output/reports/lean_theorem_inventory.json",
                    "consumer": "OnPolicyDistillation",
                    "consistent": row.get("status") == "proved",
                }
            )
    variables = _load_json(root / "output" / "data" / "manuscript_variables.json")
    for token in sorted(variables):
        domain_rows.append(
            {
                "domain": "manuscript_variable",
                "symbol": str(token),
                "source": "output/data/manuscript_variables.json",
                "consumer": "hydration",
                "consistent": True,
            }
        )
    evidence = _load_json(root / "output" / "data" / "evidence_field_index.json")
    for row in evidence.get("rows") or []:
        jsonpath = str(row.get("jsonpath") or "")
        if jsonpath:
            domain_rows.append(
                {
                    "domain": "json_field",
                    "symbol": f"{row.get('artifact')}#{jsonpath}",
                    "source": str(row.get("artifact") or ""),
                    "consumer": str(row.get("claim_id") or ""),
                    "consistent": row.get("jsonpath_present") is True,
                }
            )
    figures = _load_json(root / "output" / "figures" / "figure_registry.json")
    figure_rows: Any = figures.get("figures") or figures.get("rows") or figures
    if isinstance(figure_rows, dict):
        figure_iter = [{"id": key, **(value if isinstance(value, dict) else {})} for key, value in figure_rows.items()]
    else:
        figure_iter = [row for row in figure_rows if isinstance(row, dict)]
    for row in figure_iter:
        figure_id = str(row.get("id") or row.get("figure_id") or "").removeprefix("fig:")
        if figure_id:
            domain_rows.append(
                {
                    "domain": "figure_label",
                    "symbol": f"fig:{figure_id}",
                    "source": "output/figures/figure_registry.json",
                    "consumer": str(row.get("path") or row.get("filename") or figure_id),
                    "consistent": True,
                }
            )
    token_provenance = _load_json(root / "output" / "data" / "manuscript_token_provenance.json")
    for row in token_provenance.get("tokens") or []:
        domain_rows.append(
            {
                "domain": "rendered_manuscript_consumer",
                "symbol": str(row.get("token") or ""),
                "source": str(row.get("section") or ""),
                "consumer": str(row.get("source") or ""),
                "consistent": row.get("mapped") is True,
            }
        )
    required_domains = {
        "gnn_variable",
        "ontology_term",
        "lean_theorem",
        "manuscript_variable",
        "json_field",
        "figure_label",
        "rendered_manuscript_consumer",
    }
    observed_domains = {str(row.get("domain")) for row in domain_rows if row.get("domain")}
    return {
        "schema": "template_active_inference.cross_track_symbol_table.v1",
        "rows": rows,
        "domain_rows": domain_rows,
        "symbol_count": len(rows),
        "domain_row_count": len(domain_rows),
        "required_domains": sorted(required_domains),
        "domains_present": sorted(observed_domains),
        "all_required_domains_present": required_domains == observed_domains,
        "all_domain_rows_consistent": bool(domain_rows) and all(row.get("consistent") is True for row in domain_rows),
        "all_shapes_declared": bool(rows) and all(row["shape_declared"] for row in rows),
        "all_dtypes_declared": bool(rows) and all(row["dtype_declared"] for row in rows),
        "all_ontology_terms_declared": bool(rows) and all(row["ontology_declared"] for row in rows),
        "all_section_terms_declared": bool(rows) and all(row["section_ontology_declared"] for row in rows),
        "all_consistent": bool(rows)
        and required_domains == observed_domains
        and all(row["consistent"] for row in rows)
        and all(row.get("consistent") is True for row in domain_rows),
    }


def build_manuscript_token_provenance(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    source = "output/data/manuscript_variables.json"
    variables = _load_json(root / source)
    from manuscript.variables import generate_variables

    variables = {**generate_variables(root, require_analysis_outputs=False), **variables}
    rows = []
    paths = sorted((root / "manuscript").glob("*.md")) + sorted((root / "manuscript" / "sections").glob("**/*.md"))
    excluded = {"AGENTS.md", "README.md", "SYNTAX.md", "preamble.md"}
    rendered_tokens: set[str] = set()
    for path in paths:
        if path.name in excluded:
            continue
        text = path.read_text(encoding="utf-8")
        for token in sorted(set(TOKEN_RE.findall(text))):
            rendered_tokens.add(token)
            rows.append(
                {
                    "section": path.relative_to(root).as_posix(),
                    "token": token,
                    "source": source,
                    "mapped": token in variables,
                }
            )
    # AI-MANUSCRIPT-TOKEN-3: rendered token set (every distinct {{token}} that
    # appears in a manuscript source and therefore renders into the hydrated
    # output) must set_equal the provenance-key set (every distinct token a
    # provenance row covers). A phantom row whose token is never rendered, or a
    # rendered token whose provenance row was hand-deleted, breaks the equality.
    provenance_keys = {str(row["token"]) for row in rows}
    rendered_sorted = sorted(rendered_tokens)
    provenance_sorted = sorted(provenance_keys)
    return {
        "schema": "template_active_inference.manuscript_token_provenance.v1",
        "tokens": rows,
        "token_count": len(rows),
        "all_tokens_mapped": all(row["mapped"] for row in rows),
        "rendered_tokens": rendered_sorted,
        "provenance_keys": provenance_sorted,
        "rendered_tokens_match_provenance_keys": bool(rendered_tokens) and rendered_tokens == provenance_keys,
    }


def _literal_guarded(value: str) -> bool:
    """Return whether a formatted variable value is specific enough to audit."""
    if value in {"", "true", "false", "none"}:
        return False
    if re.fullmatch(r"[0-9a-f]{8,}", value):
        return True
    if re.fullmatch(r"-?\d+\.\d+", value):
        return True
    if re.fullmatch(r"-?\d+", value):
        return abs(int(value)) >= 10
    return False


def _literal_pattern(value: str) -> re.Pattern[str]:
    right_boundary = r"(?![A-Za-z0-9_-]|\.\d)" if re.fullmatch(r"-?\d+(?:\.\d+)?", value) else r"(?![A-Za-z0-9_-])"
    return re.compile(rf"(?<![A-Za-z0-9_-]){re.escape(value)}{right_boundary}")


def build_hardcoded_variable_audit(project_root: Path) -> dict[str, Any]:
    """Find generated variable values hard-coded in manuscript source."""
    root = project_root.resolve()
    from manuscript.hydrate import EXCLUDED_DOC_FILENAMES, format_variables
    from manuscript.variables import generate_variables

    raw_variables = generate_variables(root, require_analysis_outputs=False)
    variables = format_variables(raw_variables)
    authored_top_level = [
        path
        for path in sorted((root / "manuscript").glob("*.md"))
        if path.name in {"00_abstract.md", "17_conclusion.md"}
    ]
    paths = authored_top_level + sorted((root / "manuscript" / "sections").glob("**/*.md"))
    excluded = set(EXCLUDED_DOC_FILENAMES) | {"99_references.md"}
    source_by_path: dict[str, str] = {}
    used_tokens_by_path: dict[str, set[str]] = {}
    for path in paths:
        if path.name in excluded:
            continue
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(root).as_posix()
        source_by_path[rel] = TOKEN_MATCH_RE.sub("", text)
        for token, _spec in TOKEN_MATCH_RE.findall(text):
            used_tokens_by_path.setdefault(rel, set()).add(token)

    used_tokens = sorted(
        {token for tokens in used_tokens_by_path.values() for token in tokens} - HARDCODED_AUDIT_SELF_TOKENS
    )
    rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for token in used_tokens:
        value = str(variables.get(token, ""))
        guarded = _literal_guarded(value)
        literal_occurrences: list[dict[str, Any]] = []
        if guarded:
            pattern = _literal_pattern(value)
            for rel, text in source_by_path.items():
                for match in pattern.finditer(text):
                    line = text.count("\n", 0, match.start()) + 1
                    literal_occurrences.append({"section": rel, "line": line})
        row = {
            "token": token,
            "formatted_value": value,
            "sections_using_token": sorted(rel for rel, tokens in used_tokens_by_path.items() if token in tokens),
            "guarded_literal": guarded,
            "literal_occurrences": literal_occurrences,
            "auto_injected": not literal_occurrences,
        }
        rows.append(row)
        if literal_occurrences:
            issues.append(
                {
                    "token": token,
                    "formatted_value": value,
                    "occurrences": literal_occurrences,
                }
            )
    return {
        "schema": "template_active_inference.hardcoded_variable_audit.v1",
        "rows": rows,
        "token_count": len(rows),
        "guarded_token_count": sum(1 for row in rows if row["guarded_literal"]),
        "issue_count": len(issues),
        "issues": issues,
        "all_values_auto_injected": not issues,
    }


def _expected_token_value(token: str, spec: str | None, variables: dict[str, Any]) -> str:
    # Render the actual placeholder through hydrate so the expected value matches the
    # renderer byte-for-byte across all format specs (e/f/g, sign) with no second
    # formatter to drift. `spec` is the captured ":.Nf"/":.1e"/"" suffix.
    from manuscript.hydrate import format_variables, substitute_snake_case_tokens

    formatted = format_variables(variables)
    placeholder = f"{{{{{token}{spec or ''}}}}}"
    rendered, _unresolved = substitute_snake_case_tokens(placeholder, formatted)
    # An unknown token renders back to its placeholder; fall back to the raw value.
    return rendered if rendered != placeholder else str(formatted.get(token, ""))


def build_manuscript_staleness_report(project_root: Path) -> dict[str, Any]:
    """Compare hydrated manuscript tokens against the current generated variables."""
    root = project_root.resolve()
    from manuscript.hydrate import EXCLUDED_DOC_FILENAMES
    from manuscript.variables import generate_variables

    variables = generate_variables(root, require_analysis_outputs=False)
    rows: list[dict[str, Any]] = []
    output_dir = root / "output" / "manuscript"
    for path in sorted((root / "manuscript").glob("*.md")):
        if path.name in EXCLUDED_DOC_FILENAMES:
            continue
        resolved_path = output_dir / path.name
        try:
            source_text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            rows.append(
                {
                    "section": path.relative_to(root).as_posix(),
                    "token": "<missing_source>",
                    "expected": "source file exists",
                    "resolved_path": resolved_path.relative_to(root).as_posix(),
                    "fresh": False,
                }
            )
            continue
        resolved_text = resolved_path.read_text(encoding="utf-8") if resolved_path.is_file() else ""
        seen: set[tuple[str, str | None]] = set()
        for match in TOKEN_MATCH_RE.finditer(source_text):
            token = match.group(1)
            spec = match.group(2)
            key = (token, spec)
            if key in seen:
                continue
            seen.add(key)
            expected = _expected_token_value(token, spec, variables)
            if token == "manuscript_staleness_all_fresh":
                expected = "true"
            unresolved = match.group(0) in resolved_text
            fresh = resolved_path.is_file() and not unresolved and expected in resolved_text
            rows.append(
                {
                    "section": path.relative_to(root).as_posix(),
                    "token": token,
                    "expected": expected,
                    "resolved_path": resolved_path.relative_to(root).as_posix(),
                    "fresh": fresh,
                }
            )
    for row in rows:
        if row["token"] == "manuscript_staleness_row_count":
            row["expected"] = str(len(rows))
            resolved_path = root / str(row["resolved_path"])
            resolved_text = resolved_path.read_text(encoding="utf-8") if resolved_path.is_file() else ""
            row["fresh"] = resolved_path.is_file() and row["expected"] in resolved_text
    rows = sorted(
        rows,
        key=lambda row: (
            str(row.get("section") or ""),
            str(row.get("token") or ""),
            str(row.get("resolved_path") or ""),
            str(row.get("expected") or ""),
        ),
    )
    return {
        "schema": "template_active_inference.manuscript_staleness_report.v1",
        "rows": rows,
        "row_count": len(rows),
        "all_fresh": bool(rows) and all(row["fresh"] for row in rows),
    }


def build_claim_evidence_audit(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    ledger = yaml.safe_load((root / "data" / "claim_ledger.yaml").read_text(encoding="utf-8")) or {}
    rows = []
    for claim in ledger.get("claims") or []:
        rows.append(
            {
                "id": claim.get("id"),
                "path": claim.get("path"),
                "has_evidence": bool(claim.get("evidence")),
                "has_tracks": bool(claim.get("tracks")),
            }
        )
    return {
        "schema": "template_active_inference.claim_evidence_audit.v1",
        "rows": rows,
        "claim_count": len(rows),
        "all_claims_typed": bool(rows) and all(row["has_evidence"] and row["has_tracks"] for row in rows),
    }


#: Declarative gate-index registry:
#: (gate id, required input paths, command, output, negative control). The id
#: must bind to the live validator surface — ``validate_outputs`` re-derives
#: the binding at read time (``validation_gate_index_binding``), so a phantom
#: row here fails validation instead of silently inflating the index.
GATE_INDEX_ROWS: tuple[tuple[str, tuple[str, ...], str, str, str], ...] = (
    (
        "validate_outputs",
        ("output/data", "output/reports"),
        "uv run python scripts/validate_outputs.py",
        "validate_outputs check map over generated output artifacts",
        "remove a required output artifact or falsify a stored schema boolean",
    ),
    (
        "aggregate_rederivation",
        ("output/data", "output/reports"),
        "uv run python -c \"from gates.aggregate_rederivation import aggregates_consistent; import pathlib; raise SystemExit(0 if aggregates_consistent(pathlib.Path('.')) else 1)\"",
        "stored all_* aggregates agree with row-level re-derivations",
        "mutate a row while leaving the stored all_* flag unchanged",
    ),
    (
        "validate_manuscript",
        ("manuscript/sheaf", "output/manuscript"),
        "uv run python scripts/compose_manuscript.py --validate-only --strict",
        "strict manuscript compose validation across the sheaf tree",
        "delete a bound manuscript fragment or inject an unknown token",
    ),
    (
        "semantic_sheaf_gluing",
        ("output/data/sheaf_gluing_certificate.json",),
        "uv run python scripts/compose_manuscript.py --validate-only --strict",
        "semantic sheaf gluing certificate and cross-track restrictions",
        "drop a required symbol or force cross-track disagreement in the certificate",
    ),
    (
        "typed_claim_evidence",
        ("data/claim_ledger.yaml",),
        "uv run python scripts/compose_manuscript.py --validate-only --strict",
        "typed claim evidence ledger for manuscript-facing claims",
        "point a claim at a missing artifact or contradict its evidence predicate",
    ),
    (
        "manuscript_staleness_report",
        ("output/manuscript", "output/data/manuscript_variables.json"),
        "uv run python scripts/generate_integration_audit.py",
        "output/reports/manuscript_staleness_report.json",
        "mutate resolved markdown while leaving all_fresh true",
    ),
    (
        "animation_frame_deltas",
        ("output/figures/si_belief_trajectory.gif",),
        "uv run python scripts/render_animation.py",
        "output/data/animation_frame_deltas.json",
        "replace a delta row with zero change while leaving all_nonzero true",
    ),
    (
        "pymdp_runtime_diagnostics",
        ("output/reports/pymdp_runtime_diagnostics.json",),
        "uv run python scripts/simulate_si_tmaze.py --comparison",
        "output/reports/pymdp_runtime_diagnostics.json",
        "inject an unexpected runtime warning while keeping the summary clean",
    ),
    (
        "pymdp_policy_posterior_grid",
        ("output/data/pymdp_policy_posterior_grid.json",),
        "uv run python scripts/simulate_si_tmaze.py --comparison",
        "output/data/pymdp_policy_posterior_grid.json",
        "delete one configured planner-seed cell or unnormalize q_pi in an available row",
    ),
    (
        "analytical_assumption_index",
        ("output/data/analytical_assumption_index.json",),
        "uv run python scripts/generate_toy_sweep_tracks.py",
        "output/data/analytical_assumption_index.json",
        "blank an equation_id or assumptions list while leaving all_equations_indexed true",
    ),
    (
        "canonical_sheaf_tracks",
        ("output/data/track_improvement_scope.json",),
        "uv run python scripts/generate_sheaf_tracks.py",
        "canonical promoted sheaf-track artifact bundle",
        "remove a required promoted track artifact from the canonical bundle",
    ),
    (
        "release_bundle_manifest",
        ("output/reports/release_bundle_manifest.json",),
        "uv run python scripts/generate_sheaf_tracks.py",
        "output/reports/release_bundle_manifest.json",
        "drop a required release artifact row while leaving all_artifacts_present true",
    ),
    (
        "evidence_field_index",
        ("output/data/evidence_field_index.json",),
        "uv run python scripts/generate_sheaf_tracks.py",
        "output/data/evidence_field_index.json",
        "clear a mapped evidence field while leaving all_fields_mapped true",
    ),
    (
        "theorem_traceability_matrix",
        ("output/data/theorem_traceability_matrix.json",),
        "uv run python scripts/generate_sheaf_tracks.py",
        "output/data/theorem_traceability_matrix.json",
        "remove a theorem trace row while leaving all_rows_traced true",
    ),
    (
        "artifact_diffoscope",
        ("output/reports/artifact_diffoscope.json",),
        "uv run python scripts/generate_integration_audit.py",
        "output/reports/artifact_diffoscope.json",
        "flip a row equal=false while leaving all_equal true",
    ),
    (
        "proof_extraction_index",
        ("output/data/proof_extraction_index.json",),
        "uv run python scripts/generate_sheaf_tracks.py",
        "output/data/proof_extraction_index.json",
        "remove an extracted theorem row while leaving all_extracted true",
    ),
    (
        "state_space_catalog",
        ("output/data/state_space_catalog.json",),
        "uv run python scripts/generate_sheaf_tracks.py",
        "output/data/state_space_catalog.json",
        "clear a state identifier while leaving all_states_cataloged true",
    ),
    (
        "causal_ablation_matrix",
        ("output/data/causal_ablation_matrix.json",),
        "uv run python scripts/generate_sheaf_tracks.py",
        "output/data/causal_ablation_matrix.json",
        "mark a row non-deterministic while leaving all_deterministic true",
    ),
    (
        "artifact_license_audit",
        ("output/reports/artifact_license_audit.json",),
        "uv run python scripts/generate_integration_audit.py",
        "output/reports/artifact_license_audit.json",
        "blank a license source row while leaving all_licenses_resolved true",
    ),
    (
        "release_notes_evidence",
        ("output/reports/release_notes_evidence.json",),
        "uv run python scripts/generate_integration_audit.py",
        "output/reports/release_notes_evidence.json",
        "delete a cited release-note row while leaving all_release_notes_backed true",
    ),
    (
        "proof_dependency_graph",
        ("output/data/proof_dependency_graph.json",),
        "uv run python scripts/generate_sheaf_tracks.py",
        "output/data/proof_dependency_graph.json",
        "remove a required dependency edge while leaving all_dependencies_resolved true",
    ),
    (
        "state_transition_table",
        ("output/data/state_transition_table.json",),
        "uv run python scripts/generate_toy_sweep_tracks.py",
        "output/data/state_transition_table.json",
        "drop a transition row while leaving all_rows_total true",
    ),
    (
        "ablation_sensitivity_report",
        ("output/reports/ablation_sensitivity_report.json",),
        "uv run python scripts/generate_toy_sweep_tracks.py",
        "output/reports/ablation_sensitivity_report.json",
        "set a sensitivity row unexplained while leaving all_rows_explained true",
    ),
    (
        "release_attestation",
        ("output/reports/release_attestation.json",),
        "uv run python scripts/run_full_chain.py --tail-only",
        "output/reports/release_attestation.json",
        "contradict one attested dependency while leaving attestation_complete true",
    ),
    (
        "track_improvement_scope",
        ("output/data/track_improvement_scope.json",),
        "uv run python scripts/generate_sheaf_tracks.py",
        "output/data/track_improvement_scope.json",
        "mark a blocked track live while leaving all_live_tracks_valid true",
    ),
    (
        "blocked_scope_manifest",
        ("output/reports/blocked_scope_manifest.json",),
        "uv run python scripts/generate_sheaf_tracks.py",
        "output/reports/blocked_scope_manifest.json",
        "flip a blocked row to unblocked while leaving all_blocked true",
    ),
    (
        "lake_build",
        ("lean/lakefile.lean",),
        "cd lean && lake build",
        "Lean theorem inventory and lake build status",
        "introduce a sorry theorem or break the Lean build graph",
    ),
)


def _rows_fully_specified(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(
        bool(str(row.get(field, "")).strip()) for row in rows for field in ("command", "output", "negative_control")
    )


def build_validation_gate_index(project_root: Path) -> dict[str, Any]:
    """Index the validator surface with per-gate required inputs.

    ``indexed`` is DERIVED from on-disk input existence (pre-Run-6 it was a
    hardcoded ``True`` and ``project_root`` was ignored — AI-GATE-INDEX-3).
    """
    root = project_root.resolve()
    rows = []
    for gate_id, inputs, command, output, negative_control in GATE_INDEX_ROWS:
        inputs_exist = all((root / rel).exists() for rel in inputs)
        rows.append(
            {
                "id": gate_id,
                "inputs": list(inputs),
                "command": command,
                "output": output,
                "negative_control": negative_control,
                "inputs_exist": inputs_exist,
                "indexed": inputs_exist,
            }
        )
    return {
        "schema": "template_active_inference.validation_gate_index.v1",
        "rows": rows,
        "gate_count": len(rows),
        "all_indexed": bool(rows) and all(row["indexed"] for row in rows),
        "all_rows_fully_specified": _rows_fully_specified(rows),
    }
