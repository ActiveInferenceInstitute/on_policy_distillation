"""Analysis orchestration: parameter sweeps and artifact writers."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from analytical.bernoulli_toy import empirical_mutual_information, ising_mutual_information
from analytical.hyperparameters import lambda_grid, load_hyperparameters
from analytical.invariants import run_invariants
from analytical.sweep_io import summarize_sweep_file
from simulation.pymdp_config import config_hash, load_pymdp_config
from simulation.statistics import load_si_artifacts, summarize_si_trace


def write_parameter_sweep(project_root: Path) -> Path:
    root = project_root.resolve()
    out = root / "output" / "data" / "parameter_sweep.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    hp = load_hyperparameters()
    rows: list[dict[str, float]] = []
    for lam in lambda_grid(hp):
        rows.append(
            {
                "lambda": lam,
                "closed_form_mi": ising_mutual_information(lam),
                "empirical_mi": empirical_mutual_information(lam),
            }
        )
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["lambda", "closed_form_mi", "empirical_mi"])
        writer.writeheader()
        writer.writerows(rows)
    return out


def write_invariants_report(
    project_root: Path,
    results: dict[str, bool] | None = None,
) -> Path:
    root = project_root.resolve()
    out = root / "output" / "reports" / "invariants.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    from simulation.invariants import build_merged_invariants_payload

    payload = build_merged_invariants_payload(root, analytical_results=results)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out


def summarize_sweep(csv_path: Path) -> dict[str, Any]:
    summary: dict[str, Any] = summarize_sweep_file(csv_path)
    return summary


def write_analysis_statistics(project_root: Path) -> Path:
    root = project_root.resolve()
    sweep_path = root / "output" / "data" / "parameter_sweep.csv"
    summary, trace = load_si_artifacts(root)
    cfg = load_pymdp_config(root)
    q_pi_rows = summary.get("q_pi_by_step") or []
    action_probability_rows = summary.get("action_probabilities") or []
    observations_by_modality = summary.get("observations_by_modality") or {}
    matrices = {}
    matrices_path = root / "output" / "data" / "si_tmaze_model_matrices.json"
    if matrices_path.is_file():
        matrices = json.loads(matrices_path.read_text(encoding="utf-8"))
    payload = {
        "sweep": summarize_sweep(sweep_path),
        "si_tmaze": summarize_si_trace(trace, summary),
        "pymdp_profile": summary.get("profile", cfg.profile),
        "pymdp_planner": summary.get("planner", cfg.planner),
        "pymdp_config_hash": summary.get("config_hash", config_hash(cfg)),
        "si_tmaze_q_pi_row_count": len(q_pi_rows),
        "si_tmaze_action_probability_row_count": len(action_probability_rows),
        "si_tmaze_observation_modality_count": len(observations_by_modality),
        "si_tmaze_tree_available": bool(summary.get("tree_available", False)),
        "si_tmaze_matrix_shape_summary": {
            "A_shapes": matrices.get("A_shapes", []),
            "B_shapes": matrices.get("B_shapes", []),
        },
    }
    out = root / "output" / "data" / "analysis_statistics.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out


def run_analysis(project_root: Path) -> dict[str, Path]:
    inv_results = run_invariants()
    return {
        "parameter_sweep": write_parameter_sweep(project_root),
        "invariants": write_invariants_report(project_root, inv_results),
    }
