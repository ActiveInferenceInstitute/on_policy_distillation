"""Privilege sweep: how the distillation signal scales with teacher privilege.

A Science-style experiment on the two-agent classroom. Hypothesis: as the
teacher's cue becomes more privileged (``cue_validity`` toward 1.0), it resolves
the latent reward location more sharply, so (H1) its belief entropy falls and
(H2) the per-decision reverse-KL distillation signal the student must close
grows. We sweep the teacher's ``cue_validity`` over a grid (student fixed,
uninformative), run the real pymdp sophisticated-inference classroom at each
level, and report the trend with a rank correlation.

The sweep drives real pymdp rollouts (two per level) and therefore requires
pymdp; it is not part of the default fast pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from .classroom import ClassroomConfig, run_classroom

SCHEMA = "firstprinciples.privilege_sweep.v1"

__all__ = ["PrivilegeSweepConfig", "rank_correlation", "run_privilege_sweep", "build_payload"]


@dataclass(frozen=True)
class PrivilegeSweepConfig:
    teacher_cue_validities: tuple[float, ...] = (0.5, 0.7, 0.9, 0.98)
    student_cue_validity: float = 0.5
    steps: int = 2
    seed: int = 0

    def __post_init__(self) -> None:
        if not self.teacher_cue_validities:
            raise ValueError("need at least one teacher cue validity")
        for v in self.teacher_cue_validities:
            if not 0.0 <= v <= 1.0:
                raise ValueError("cue validities must be in [0, 1]")


def rank_correlation(xs: list[float], ys: list[float]) -> float:
    """Spearman rank correlation (Pearson correlation of ranks), no SciPy."""
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("rank_correlation needs two equal-length series of length >= 2")

    def _ranks(values: list[float]) -> np.ndarray:
        arr = np.asarray(values, dtype=np.float64)
        order = np.argsort(arr, kind="stable")
        sorted_vals = arr[order]
        ranks = np.empty(len(arr), dtype=np.float64)
        i = 0
        n = len(arr)
        while i < n:
            j = i
            while j + 1 < n and sorted_vals[j + 1] == sorted_vals[i]:
                j += 1
            avg = (i + j) / 2.0  # average rank for ties
            for k in range(i, j + 1):
                ranks[order[k]] = avg
            i = j + 1
        return ranks

    rx, ry = _ranks(xs), _ranks(ys)
    if rx.std() == 0.0 or ry.std() == 0.0:
        return 0.0
    return float(np.corrcoef(rx, ry)[0, 1])


def run_privilege_sweep(project_root: Path, config: PrivilegeSweepConfig | None = None) -> dict[str, Any]:
    """Run the classroom across the teacher cue-validity grid; return the trend."""
    cfg = config or PrivilegeSweepConfig()
    root = Path(project_root).resolve()
    levels: list[dict[str, Any]] = []
    for validity in cfg.teacher_cue_validities:
        result = run_classroom(
            root,
            ClassroomConfig(
                teacher_cue_validity=validity,
                student_cue_validity=cfg.student_cue_validity,
                steps=cfg.steps,
                seed=cfg.seed,
            ),
        )
        levels.append(
            {
                "teacher_cue_validity": validity,
                "mean_reverse_kl": result.mean_reverse_kl,
                "teacher_belief_entropy": result.teacher_mean_belief_entropy,
                "student_belief_entropy": result.student_mean_belief_entropy,
                "privileged_advantage": result.privileged_advantage,
            }
        )
    validities = [row["teacher_cue_validity"] for row in levels]
    signals = [row["mean_reverse_kl"] for row in levels]
    entropies = [row["teacher_belief_entropy"] for row in levels]
    signal_corr = rank_correlation(validities, signals) if len(levels) >= 2 else 0.0
    entropy_corr = rank_correlation(validities, entropies) if len(levels) >= 2 else 0.0
    return {
        "schema": SCHEMA,
        "student_cue_validity": cfg.student_cue_validity,
        "levels": levels,
        "signal_rank_correlation": signal_corr,
        "entropy_rank_correlation": entropy_corr,
        "h1_entropy_falls_with_privilege": bool(entropy_corr <= 0.0),
        "h2_signal_grows_with_privilege": bool(signal_corr >= 0.0),
        "ok": bool(levels),
    }


def build_payload(project_root: Path, config: PrivilegeSweepConfig | None = None) -> dict[str, Any]:
    """Build the canonical privilege-sweep artifact payload by running the sweep."""
    return run_privilege_sweep(project_root, config)
