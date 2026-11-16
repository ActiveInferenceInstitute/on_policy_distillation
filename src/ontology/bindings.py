"""Active Inference Ontology bindings and concordance helpers."""

from __future__ import annotations

from pathlib import Path

import yaml

from gnn.concordance import BERNOULLI_EXPECTED_TERMS, BERNOULLI_SYMBOL_MAP, parity_gaps
from gnn.parser import parse_gnn_file

SI_SYMBOL_MAP: dict[str, str] = {
    "location": "loc",
    "reward_location": "reward_loc",
    "location_observation": "obs_location",
    "outcome_observation": "obs_outcome",
    "cue_observation": "obs_cue",
    "policy": "q_pi",
    "first_action_probability": "first_action_prob",
    "belief_entropy": "belief_entropy",
    "si_tree": "si_tree_nodes",
}

SI_EXPECTED_TERMS: dict[str, str] = {
    "loc": "HiddenState",
    "reward_loc": "HiddenState",
    "obs_location": "ObservationLikelihood",
    "obs_outcome": "ObservationLikelihood",
    "obs_cue": "ObservationLikelihood",
    "q_pi": "PolicyPosterior",
    "first_action_prob": "PolicyPosterior",
    "belief_entropy": "BeliefEntropy",
    "si_tree_nodes": "PolicyPosterior",
}

GRAPH_WORLD_SYMBOL_MAP: dict[str, str] = {
    "node": "node",
    "edge": "edge",
    "action": "action",
    "graph_policy": "graph_policy",
    "goal": "goal",
    "trace_step": "trace_step",
    "goal_reached": "goal_reached",
}

GRAPH_WORLD_EXPECTED_TERMS: dict[str, str] = {
    "node": "GraphWorldState",
    "edge": "GraphWorldTopology",
    "action": "GraphWorldAction",
    "graph_policy": "GraphWorldPolicy",
    "goal": "GraphWorldGoal",
    "trace_step": "GraphWorldTrace",
    "goal_reached": "GraphWorldReachability",
}


_MODEL_SECTIONS = {
    "bernoulli_toy": "methods_analytical",
    "si_tmaze": "methods_pymdp",
    "graph_world": "results_invariants",
}


def resolve_model_ontology_path(project_root: Path, model_id: str) -> Path:
    """Resolve a model's active ontology binding from the canonical live manifest.

    Missing, ambiguous, or non-rendered bindings are errors; the historical
    fragment location is never a fallback. File existence is checked by readers.
    """
    from manuscript.sheaf.manifest import default_manifest_path, load_manifest
    from manuscript.sheaf.registry import track_order_for_section

    root = project_root.resolve()
    if model_id not in _MODEL_SECTIONS:
        raise ValueError(f"unknown ontology model {model_id!r}")
    section_id = _MODEL_SECTIONS[model_id]
    manifest = load_manifest(default_manifest_path(root), project_root=root)
    sections = [section for section in manifest.sections if section.id == section_id]
    if len(sections) != 1:
        raise ValueError(f"{model_id}: expected one manifest section {section_id!r}, found {len(sections)}")
    section = sections[0]
    binding = section.tracks.get("ontology", "")
    if not section.should_compose() or not binding or "ontology" not in track_order_for_section(section, {}):
        raise ValueError(f"{model_id}: missing active ontology binding in section {section_id!r}")
    path = (root / binding).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"{model_id}: ontology binding leaves the project root: {binding!r}")
    return path


def load_section_ontology(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    terms_block = data.get("terms")
    if isinstance(terms_block, dict):
        entries: dict[str, str] = {}
        for key, value in terms_block.items():
            if isinstance(value, dict):
                entries[str(key)] = str(value.get("label") or value.get("description") or key)
            else:
                entries[str(key)] = str(value)
        return entries
    return {str(k): str(v) for k, v in data.items()}


def validate_gnn_ontology(
    gnn_path: Path,
    symbol_map: dict[str, str] | None = None,
    *,
    expected_terms: dict[str, str] | None = None,
    label: str | None = None,
) -> list[str]:
    model = parse_gnn_file(gnn_path)
    terms = expected_terms if expected_terms is not None else BERNOULLI_EXPECTED_TERMS
    gaps: list[str] = parity_gaps(model, symbol_map or BERNOULLI_SYMBOL_MAP, expected_terms=terms)
    prefix = label or gnn_path.stem
    return [f"{prefix}: {gap}" for gap in gaps]


def _validate_section_ontology_exact(
    *,
    section_path: Path,
    expected_terms: dict[str, str],
    label: str,
) -> list[str]:
    section_terms = load_section_ontology(section_path)
    gaps: list[str] = []
    for variable, expected in expected_terms.items():
        actual = section_terms.get(variable)
        if actual != expected:
            gaps.append(f"{label}: section ontology variable {variable!r} annotated {actual!r}, expected {expected!r}")
    for variable in sorted(set(section_terms) - set(expected_terms)):
        gaps.append(f"{label}: section ontology variable {variable!r} is not mapped by the expected model terms")
    return gaps


def validate_all_gnn_ontology(project_root: Path) -> list[str]:
    """Validate every project GNN model against its model-specific ontology map."""
    root = project_root.resolve()
    checks = (
        (
            root / "gnn" / "bernoulli_toy.gnn.md",
            "bernoulli_toy",
            BERNOULLI_SYMBOL_MAP,
            BERNOULLI_EXPECTED_TERMS,
            "bernoulli_toy",
        ),
        (
            root / "gnn" / "si_tmaze.gnn.md",
            "si_tmaze",
            SI_SYMBOL_MAP,
            SI_EXPECTED_TERMS,
            "si_tmaze",
        ),
        (
            root / "gnn" / "graph_world.gnn.md",
            "graph_world",
            GRAPH_WORLD_SYMBOL_MAP,
            GRAPH_WORLD_EXPECTED_TERMS,
            "graph_world",
        ),
    )
    gaps: list[str] = []
    for path, model_id, symbol_map, expected_terms, label in checks:
        if not path.is_file():
            gaps.append(f"{label}: missing {path.relative_to(root)}")
            continue
        gaps.extend(
            validate_gnn_ontology(
                path,
                symbol_map,
                expected_terms=expected_terms,
                label=label,
            )
        )
        try:
            section_path = resolve_model_ontology_path(root, model_id)
        except (ValueError, OSError, yaml.YAMLError) as exc:
            gaps.append(f"{label}: cannot resolve canonical ontology binding: {exc}")
            continue
        gaps.extend(
            _validate_section_ontology_exact(
                section_path=section_path,
                expected_terms=expected_terms,
                label=label,
            )
        )
    return gaps
