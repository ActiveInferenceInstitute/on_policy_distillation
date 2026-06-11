"""Persist full-TMaze sophisticated-inference rollout artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from simulation.logging_utils import RunLogger
from simulation.numerics import STEP_POSTERIOR_ATOL
from simulation.pymdp_config import (
    ComparisonPlanner,
    PymdpConfig,
    apply_pymdp_overrides,
    config_snapshot,
    load_pymdp_config,
)
from simulation.pymdp_runtime import write_runtime_diagnostics
from simulation.si_loop import SIRunResult, run_si_tmaze, run_validation_comparison_tmaze
from simulation.tmaze_model import build_tmaze_generative_model


def _shape_list(factors: list[Any]) -> list[list[int]]:
    return [list(np.asarray(factor).shape) for factor in factors]


def _factor_sum_ranges(factors: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, factor in enumerate(factors):
        arr = np.asarray(factor, dtype=np.float64)
        sums = arr.sum(axis=0) if arr.ndim >= 2 else np.array([arr.sum()])
        rows.append(
            {
                "factor": index,
                "shape": list(arr.shape),
                "axis0_sum_min": float(np.min(sums)),
                "axis0_sum_max": float(np.max(sums)),
                "nonzero_count": int(np.count_nonzero(arr)),
            }
        )
    return rows


def model_matrices_payload(config: PymdpConfig) -> dict[str, Any]:
    model = build_tmaze_generative_model(config)
    return {
        "schema": "template_active_inference.si_tmaze_model_matrices.v1",
        "profile": config.profile,
        "planner": config.planner,
        "environment_class": model["environment_class"],
        "A_shapes": _shape_list(model["A"]),
        "B_shapes": _shape_list(model["B"]),
        "C_shapes": _shape_list(model["C"]),
        "D_shapes": _shape_list(model["D"]),
        "dependencies": model["dependencies"],
        "labels": model["labels"],
        "normalization_checks": model["normalization_checks"],
        "A_column_sum_ranges": _factor_sum_ranges(model["A"]),
        "B_column_sum_ranges": _factor_sum_ranges(model["B"]),
        "D_sum_ranges": _factor_sum_ranges(model["D"]),
        "preferences": model["preferences"],
        "environment": model["environment"],
        "transition_semantics": model["transition_semantics"],
        "config": config_snapshot(config),
    }


def write_model_matrices(project_root: Path, *, config: PymdpConfig | None = None) -> Path:
    root = project_root.resolve()
    cfg = config or load_pymdp_config(root)
    out = root / "output" / "data" / "si_tmaze_model_matrices.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(model_matrices_payload(cfg), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def write_si_artifacts(
    project_root: Path,
    result: SIRunResult,
    *,
    config: PymdpConfig | None = None,
    trace_steps: list[dict[str, Any]] | None = None,
) -> dict[str, Path]:
    root = project_root.resolve()
    cfg = config or load_pymdp_config(root)
    data_dir = root / "output" / "data"
    reports_dir = root / "output" / "reports"
    data_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    snapshot = config_snapshot(cfg)
    summary = {
        "schema": "template_active_inference.si_tmaze_summary.v2",
        "profile": result.profile,
        "planner": result.planner,
        "steps": result.steps,
        "rollout_timestep_count": len(result.actions),
        "planning_horizon": result.planning_horizon,
        "policy_len": result.policy_len,
        "num_policies": result.num_policies,
        "mean_belief_entropy": result.mean_belief_entropy,
        "actions": result.actions,
        "action_names": result.action_names,
        "action_vectors": result.action_vectors,
        "observations": result.observations,
        "observations_by_modality": result.observations_by_modality,
        "observation_names_by_modality": result.observation_names_by_modality,
        "q_pi_by_step": result.q_pi_by_step,
        "q_pi_entropy_by_step": result.q_pi_entropy_by_step,
        "action_probabilities": result.action_probabilities,
        "config_hash": result.config_hash,
        "goal_reached": result.goal_reached,
        "reward_observed": result.reward_observed,
        "action_diversity": result.action_diversity,
        "tree_available": result.tree_available,
        "tree_stats": result.tree_stats,
        "expected_known_warnings": {
            "jax_static_array": int(result.runtime_diagnostics.get("known_warning_count", 0) or 0),
            "tree_max_nodes": int(result.runtime_diagnostics.get("known_tree_warning_count", 0) or 0),
        },
        "validation_comparison": {
            "enabled": cfg.validation_comparison.enabled,
            "vanilla_role": "comparison_only",
            "planners": list(cfg.validation_comparison.planners),
        },
        "config": snapshot,
    }
    summary_path = data_dir / "si_tmaze_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    steps_payload = trace_steps if trace_steps is not None else result.trace_steps
    trace_path = data_dir / "si_tmaze_trace.json"
    trace_path.write_text(
        json.dumps(
            {
                "schema": "template_active_inference.si_tmaze_trace.v2",
                "profile": result.profile,
                "planner": result.planner,
                "config_hash": result.config_hash,
                "steps": steps_payload,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    matrices_path = write_model_matrices(root, config=cfg)

    log_path = root / cfg.logging.path
    log_records = 0
    if log_path.exists():
        log_records = sum(1 for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip())
    run_report = {
        "schema": "template_active_inference.si_tmaze_run_report.v2",
        "config": snapshot,
        "config_hash": result.config_hash,
        "profile": result.profile,
        "planner": result.planner,
        "seed": cfg.random_seed,
        "policy_len": result.policy_len,
        "planning_horizon": result.planning_horizon,
        "steps": result.steps,
        "rollout_timestep_count": len(result.actions),
        "log_path": str(cfg.logging.path),
        "log_record_count": log_records,
        "goal_reached": result.goal_reached,
        "tree_available": result.tree_available,
    }
    report_path = reports_dir / "si_tmaze_run_report.json"
    report_path.write_text(json.dumps(run_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if result.runtime_diagnostics:
        write_runtime_diagnostics(root, [result.runtime_diagnostics])

    from simulation.invariants import merge_simulation_into_invariants_report, write_simulation_invariants

    write_simulation_invariants(root)
    merge_simulation_into_invariants_report(root)

    return {
        "summary": summary_path,
        "trace": trace_path,
        "model_matrices": matrices_path,
        "run_report": report_path,
    }


def run_and_persist(
    project_root: Path,
    *,
    config: PymdpConfig | None = None,
) -> dict[str, Any]:
    cfg = config or load_pymdp_config(project_root)
    logger = RunLogger.from_project_root(
        project_root,
        relative_path=cfg.logging.path,
        enabled=cfg.logging.enabled,
    )
    logger.fresh()
    result = run_si_tmaze(project_root, config=cfg, logger=logger)
    paths = write_si_artifacts(project_root, result, config=cfg, trace_steps=result.trace_steps)
    return {"result": result, "paths": paths, "log_records": len(logger.records())}


def _comparison_row(result: SIRunResult, *, planner: ComparisonPlanner, seed: int) -> dict[str, Any]:
    posterior_steps = []
    for step in result.trace_steps:
        posterior_steps.append(
            {
                "step": step.get("step"),
                "posterior_available": bool(step.get("q_pi")),
                "posterior_source": planner,
                "q_pi": step.get("q_pi", []),
                "q_pi_sum": step.get("q_pi_sum"),
                "q_pi_entropy": step.get("q_pi_entropy"),
                "q_pi_normalized": step.get("q_pi_normalized") is True,
                "action_probabilities": step.get("action_probabilities", {}),
                "selected_action": step.get("selected_action"),
                "selected_action_name": step.get("selected_action_name"),
                "fallback_reason": None,
            }
        )
    entropy_values = [float(step["q_pi_entropy"]) for step in posterior_steps if step.get("q_pi_entropy") is not None]
    return {
        "planner": planner,
        "role": "validation_comparison",
        "horizon": result.planning_horizon,
        "seed": seed,
        "steps": result.steps,
        "rollout_timestep_count": len(result.actions),
        "policy_len": result.policy_len,
        "num_policies": result.num_policies,
        "goal_reached": result.goal_reached,
        "action_diversity": result.action_diversity,
        "mean_belief_entropy": result.mean_belief_entropy,
        "actions": result.actions,
        "action_names": result.action_names,
        "observations_by_modality": result.observations_by_modality,
        "policy_posterior_steps": posterior_steps,
        "policy_posterior_available_count": len(posterior_steps),
        "policy_posterior_all_normalized": all(step["q_pi_normalized"] for step in posterior_steps),
        "mean_policy_posterior_entropy": sum(entropy_values) / len(entropy_values) if entropy_values else None,
        "tree_available": result.tree_available,
        "tree_stats": result.tree_stats,
    }


def write_policy_comparison(
    project_root: Path,
    *,
    seeds: tuple[int, ...] | None = None,
    planners: tuple[ComparisonPlanner, ...] | None = None,
) -> Path:
    """Write SI-vs-vanilla comparison rows without changing the canonical summary."""
    root = project_root.resolve()
    base = load_pymdp_config(root)
    configured_seeds = seeds if seeds is not None else base.validation_comparison.seeds
    configured_planners = planners if planners is not None else base.validation_comparison.planners
    rows: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for seed in configured_seeds:
        cfg = apply_pymdp_overrides(base, seed=seed, logging_enabled=False)
        for planner in configured_planners:
            logger = RunLogger(
                root / "output" / "logs" / f"pymdp_compare_{planner}_{cfg.planning_horizon}_{seed}.jsonl"
            )
            result = run_validation_comparison_tmaze(root, config=cfg, planner=planner, logger=logger)
            diagnostics.append(result.runtime_diagnostics)
            rows.append(_comparison_row(result, planner=planner, seed=seed))
    expected_run_count = len(configured_planners) * len(configured_seeds)
    all_efe_rows_explained = bool(rows) and all(
        bool(row.get("policy_posterior_steps"))
        and all(
            step.get("posterior_available") is True or bool(step.get("fallback_reason"))
            for step in row.get("policy_posterior_steps") or []
        )
        for row in rows
    )
    payload = {
        "schema": "template_active_inference.si_policy_comparison.v2",
        "scope": "comparison_only",
        "canonical_planner": "sophisticated_inference",
        "runs": rows,
        "summary": {
            "run_count": len(rows),
            "planners": sorted({row["planner"] for row in rows}),
            "horizons": sorted({row["horizon"] for row in rows}),
            "seeds": sorted({row["seed"] for row in rows}),
            "expected_run_count": expected_run_count,
            "complete_grid": len(rows) == expected_run_count,
            "vanilla_role": "comparison_only",
            "goal_reached_count": sum(1 for row in rows if row["goal_reached"]),
            "posterior_available_run_count": sum(1 for row in rows if row["policy_posterior_available_count"]),
            "all_available_posteriors_normalized": all(row["policy_posterior_all_normalized"] for row in rows),
            "all_efe_rows_explained": all_efe_rows_explained,
        },
    }
    out = root / "output" / "data" / "si_policy_comparison.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_runtime_diagnostics(root, diagnostics)
    write_policy_posterior_grid(root, comparison=payload)
    return out


def write_policy_posterior_grid(
    project_root: Path,
    *,
    comparison: dict[str, Any] | None = None,
) -> Path:
    """Write step-level PyMDP policy posterior normalization evidence."""
    root = project_root.resolve()
    payload = comparison
    if payload is None:
        path = root / "output" / "data" / "si_policy_comparison.json"
        payload = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    rows: list[dict[str, Any]] = []
    for run_index, run in enumerate(payload.get("runs") or []):
        for step in run.get("policy_posterior_steps") or []:
            q_pi = [float(value) for value in step.get("q_pi", []) or []]
            q_sum = float(sum(q_pi)) if q_pi else None
            rows.append(
                {
                    "run_index": run_index,
                    "step": step.get("step"),
                    "planner": run.get("planner"),
                    "role": run.get("role"),
                    "horizon": run.get("horizon"),
                    "seed": run.get("seed"),
                    "posterior_available": step.get("posterior_available") is True,
                    "posterior_source": step.get("posterior_source"),
                    "q_pi": q_pi,
                    "q_pi_sum": q_sum,
                    "q_pi_entropy": step.get("q_pi_entropy"),
                    "action_probabilities": step.get("action_probabilities", {}),
                    "normalized": q_sum is not None and abs(q_sum - 1.0) <= STEP_POSTERIOR_ATOL,
                    "fallback_reason": step.get("fallback_reason"),
                }
            )
    available = [row for row in rows if row["posterior_available"]]
    unavailable = [row for row in rows if not row["posterior_available"]]
    grid = {
        "schema": "template_active_inference.pymdp_policy_posterior_grid.v1",
        "source": "output/data/si_policy_comparison.json",
        "scope": "comparison_only",
        "canonical_planner": payload.get("canonical_planner"),
        "rows": rows,
        "row_count": len(rows),
        "available_row_count": len(available),
        "all_available_posteriors_normalized": bool(available) and all(row["normalized"] for row in available),
        "all_unavailable_rows_explained": all(bool(row["fallback_reason"]) for row in unavailable),
    }
    out = root / "output" / "data" / "pymdp_policy_posterior_grid.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(grid, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out
