"""Deterministic artifact emitters for the first-principles OPD<->AI package.

Each writer produces a small, sorted-key JSON artifact under
``output/data/firstprinciples/`` plus markdown tables the sheaf manuscript can
include. Everything here is closed-form and seedless except the optional
classroom rollout (which requires pymdp and is driven separately).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from . import active_selection
from . import adaptive
from . import divergences as dv
from . import diversity
from . import empirical
from . import energy
from . import exposure_bias as eb
from . import gkd
from . import mapping
from . import parallel
from . import reward_tilting as rt
from . import sdpg
from . import sequential_shift
from . import statistics as stats
from . import taxonomy
from . import variational_em

__all__ = [
    "ARTIFACT_DIR",
    "divergence_demo",
    "reward_tilting_demo",
    "exposure_bias_demo",
    "sdpg_demo",
    "write_json",
    "write_all",
    "write_markdown_tables",
    "write_statistics_artifact",
]

ARTIFACT_DIR = ("output", "data", "firstprinciples")

# Canonical teacher/student example: a confident teacher (one dominant mode) and
# a diffuse student. Reverse KL (mode-seeking) should be smaller than forward KL
# (mode-covering) once the student concentrates on the teacher's mode.
_TEACHER = np.array([0.80, 0.15, 0.04, 0.01], dtype=np.float64)
_STUDENT = np.array([0.55, 0.25, 0.15, 0.05], dtype=np.float64)
_REFERENCE = np.array([0.25, 0.25, 0.25, 0.25], dtype=np.float64)
_REWARD = np.array([2.0, 0.5, -0.5, -2.0], dtype=np.float64)
_SDPG_MODES = ("fkl", "rkl", "ufkl", "urkl")
_SDPG_LOSS_TERMS = (
    "clip_term",
    "distill_term",
    "ref_kl_term",
    "self_distillation_kl",
    "reference_kl",
    "total",
)


def _dir(root: Path) -> Path:
    path = Path(root).resolve().joinpath(*ARTIFACT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(root: Path, name: str, payload: dict[str, Any]) -> Path:
    path = _dir(root) / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def divergence_demo() -> dict[str, Any]:
    """Forward/reverse/JSD/skew/alpha geometry on the canonical example."""
    return {
        "schema": "firstprinciples.divergence_demo.v1",
        "teacher": _TEACHER.tolist(),
        "student": _STUDENT.tolist(),
        "forward_kl": dv.forward_kl(_TEACHER, _STUDENT),
        "reverse_kl": dv.reverse_kl(_STUDENT, _TEACHER),
        "jensen_shannon": dv.jensen_shannon(_STUDENT, _TEACHER),
        "skew_kl_alpha_0_1": dv.skew_kl(_TEACHER, _STUDENT, 0.1),
        "alpha_divergence_0_5": dv.alpha_divergence(_TEACHER, _STUDENT, 0.5),
        "clipped_reverse_kl": dv.clipped_pointwise_kl(_STUDENT, _TEACHER, clip=0.5),
        "mode_concentration": dv.mode_concentration(_STUDENT, _TEACHER),
    }


def reward_tilting_demo() -> dict[str, Any]:
    """Reward-tilted target and numerical optimality certificate."""
    target = rt.reward_tilted_target(_REFERENCE, _REWARD, beta=1.0)
    return {
        "schema": "firstprinciples.reward_tilting_demo.v1",
        "reference": _REFERENCE.tolist(),
        "reward": _REWARD.tolist(),
        "beta": 1.0,
        "target": target.tolist(),
        "objective": rt.kl_regularized_objective(target, _REFERENCE, _REWARD, beta=1.0),
        "free_energy_of_reference": rt.free_energy_against_tilted(_REFERENCE, _REFERENCE, _REWARD, beta=1.0),
        "optimality": rt.verify_optimality(_REFERENCE, _REWARD, beta=1.0),
    }


def exposure_bias_demo() -> dict[str, Any]:
    """On-policy vs off-policy survival curves under compounding error."""
    spec = eb.DriftSpec()
    return {
        "schema": "firstprinciples.exposure_bias_demo.v1",
        "spec": {
            "accuracy": spec.accuracy,
            "horizon": spec.horizon,
            "on_recovery": spec.on_recovery,
            "off_recovery": spec.off_recovery,
        },
        "curves": eb.drift_curves(spec),
        "gap": eb.exposure_gap(spec),
    }


def sdpg_demo() -> dict[str, Any]:
    """SDPG objective terms across KL modes on canonical logits."""
    teacher = sdpg.softmax(np.array([2.0, 0.0, -1.0, -2.0]))  # privileged-context teacher
    student = sdpg.softmax(np.array([0.5, 0.2, 0.0, -0.5]))  # student without context
    reference = sdpg.softmax(np.array([0.0, 0.0, 0.0, 0.0]))
    modes = {
        mode: sdpg.sdpg_loss(student, teacher, reference, advantage=1.0, config=sdpg.SDPGConfig(kl_mode=mode))
        for mode in _SDPG_MODES
    }
    mode_rows = [{"mode": mode, **modes[mode]} for mode in _SDPG_MODES]
    signal_density = sdpg.signal_density(student, teacher)
    all_loss_terms_present = all(all(term in row for term in _SDPG_LOSS_TERMS) for row in mode_rows)
    all_loss_terms_finite = all(
        bool(np.isfinite(float(row[term]))) for row in mode_rows for term in _SDPG_LOSS_TERMS
    )
    all_self_distillation_kl_positive = all(row["self_distillation_kl"] > 0.0 for row in mode_rows)
    all_reference_kl_positive = all(row["reference_kl"] > 0.0 for row in mode_rows)
    dense_privileged_signal = (
        signal_density["denser_than_scalar"] is True
        and signal_density["density_ratio"] > signal_density["scalar_reward_components"]
    )
    ok = (
        set(modes) == set(_SDPG_MODES)
        and all_loss_terms_present
        and all_loss_terms_finite
        and all_self_distillation_kl_positive
        and all_reference_kl_positive
        and dense_privileged_signal
    )
    return {
        "schema": "firstprinciples.sdpg_demo.v1",
        "teacher": teacher.tolist(),
        "student": student.tolist(),
        "reference": reference.tolist(),
        "mode_keys": list(_SDPG_MODES),
        "modes": modes,
        "mode_rows": mode_rows,
        "required_loss_terms": list(_SDPG_LOSS_TERMS),
        "signal_density": signal_density,
        "all_loss_terms_present": all_loss_terms_present,
        "all_loss_terms_finite": all_loss_terms_finite,
        "all_self_distillation_kl_positive": all_self_distillation_kl_positive,
        "all_reference_kl_positive": all_reference_kl_positive,
        "dense_privileged_signal": dense_privileged_signal,
        "ok": ok,
    }


def write_statistics_artifact(
    root: Path,
    teacher_entropy: list[float],
    student_entropy: list[float],
) -> Path:
    """Write ``statistics_demo.json`` from measured classroom belief entropies.

    Lives outside :func:`write_all` because the inferential summary is only
    honest when fed the per-decision entropies of a classroom rollout that
    actually ran — there is deliberately no synthetic fallback.
    """
    payload = stats.build_payload(teacher_entropy, student_entropy)
    return write_json(root, "statistics_demo.json", payload)


def write_markdown_tables(root: Path) -> dict[str, Path]:
    """Write the correspondence and taxonomy markdown tables."""
    directory = _dir(root)
    paths: dict[str, Path] = {}
    for name, text in (
        ("correspondence_table.md", mapping.markdown_table()),
        ("taxonomy_table.md", taxonomy.markdown_table()),
        ("benchmark_table.md", empirical.markdown_table()),
    ):
        path = directory / name
        path.write_text(text, encoding="utf-8")
        paths[name] = path
    return paths


def write_all(root: Path) -> dict[str, Path]:
    """Emit every deterministic first-principles artifact; return name->path."""
    paths: dict[str, Path] = {
        "correspondence_map.json": write_json(root, "correspondence_map.json", mapping.build_payload()),
        "opd_taxonomy.json": write_json(root, "opd_taxonomy.json", taxonomy.build_payload()),
        "divergence_demo.json": write_json(root, "divergence_demo.json", divergence_demo()),
        "reward_tilting_demo.json": write_json(root, "reward_tilting_demo.json", reward_tilting_demo()),
        "exposure_bias_demo.json": write_json(root, "exposure_bias_demo.json", exposure_bias_demo()),
        "sdpg_demo.json": write_json(root, "sdpg_demo.json", sdpg_demo()),
        "gkd_demo.json": write_json(root, "gkd_demo.json", gkd.build_payload()),
        "variational_em_demo.json": write_json(root, "variational_em_demo.json", variational_em.build_payload()),
        "diversity_demo.json": write_json(root, "diversity_demo.json", diversity.build_payload()),
        "adaptive_demo.json": write_json(root, "adaptive_demo.json", adaptive.build_payload()),
        "energy_demo.json": write_json(root, "energy_demo.json", energy.build_payload()),
        "active_selection_demo.json": write_json(
            root, "active_selection_demo.json", active_selection.build_payload()
        ),
        "empirical_benchmark.json": write_json(root, "empirical_benchmark.json", empirical.build_payload()),
        "parallel_demo.json": write_json(root, "parallel_demo.json", parallel.build_payload()),
        "sequential_shift.json": write_json(root, "sequential_shift.json", sequential_shift.build_payload()),
        "sequential_shift_sensitivity.json": write_json(
            root,
            "sequential_shift_sensitivity.json",
            sequential_shift.build_sensitivity_payload(),
        ),
    }
    paths.update(write_markdown_tables(root))
    return paths
