"""The two-agent active-inference classroom: privileged teacher, on-policy student.

This is the executable heart of the thesis. Two *sophisticated-inference* pymdp
agents run the canonical T-maze. The **teacher** is given a near-perfect cue
(``cue_validity`` close to 1.0): the cue observation is privileged information
that all but reveals the latent reward location, so the teacher's policy
posterior ``q(pi)`` commits confidently to the rewarded arm. The **student**
sees an uninformative cue (``cue_validity`` near 0.5): it must generate its own
observations (the on-policy rollout) and infer against the teacher.

The per-decision *distillation signal* is the reverse KL between the student's
and the teacher's first-action distributions — the variational-free-energy term
for this declared finite target. The cue is a scoped Markov-blanket-style
boundary; the rollout is the posterior generating its own observations; the
reverse KL is the local loss. The construction measures the title's reading
inside this toy classroom rather than turning it into a production-scale claim.

The metric helpers are pure (testable without pymdp); :func:`run_classroom`
drives two real sophisticated-inference rollouts and requires pymdp.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

import json

import numpy as np

from simulation.pymdp_config import PymdpConfig, apply_pymdp_overrides, load_pymdp_config
from simulation.si_loop import SIRunResult, pymdp_available, run_si_tmaze

from .divergences import forward_kl, jensen_shannon, normalize, reverse_kl

SCHEMA = "firstprinciples.classroom.v1"

__all__ = [
    "ClassroomConfig",
    "ClassroomResult",
    "align_distributions",
    "distillation_metrics",
    "summarize_steps",
    "run_classroom",
    "build_payload",
    "validate_classroom_payload",
    "write_classroom_artifact",
    "SCHEMA",
]


@dataclass(frozen=True)
class ClassroomConfig:
    """Privileged-teacher vs on-policy-student rollout parameters."""

    teacher_cue_validity: float = 0.98
    student_cue_validity: float = 0.5
    steps: int = 3
    seed: int = 0

    def __post_init__(self) -> None:
        for name in ("teacher_cue_validity", "student_cue_validity"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        if self.steps < 1:
            raise ValueError("steps must be >= 1")


@dataclass(frozen=True)
class ClassroomResult:
    teacher_cue_validity: float
    student_cue_validity: float
    steps: int
    per_step: list[dict[str, Any]]
    mean_reverse_kl: float
    mean_forward_kl: float
    mean_jensen_shannon: float
    teacher_mean_belief_entropy: float
    student_mean_belief_entropy: float
    teacher_belief_entropies: list[float]
    student_belief_entropies: list[float]
    teacher_goal_reached: bool
    student_goal_reached: bool
    privileged_advantage: bool
    teacher_config_hash: str
    student_config_hash: str
    runtime: dict[str, Any] = field(default_factory=dict)


def align_distributions(
    teacher: dict[str, float], student: dict[str, float]
) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Return a shared key order and normalised teacher/student vectors.

    The union of action names is used so a missing action (probability 0 in one
    agent) is handled symmetrically.
    """
    keys = sorted(set(teacher) | set(student))
    if not keys:
        raise ValueError("at least one action distribution is required")
    t = np.array([float(teacher.get(k, 0.0)) for k in keys], dtype=np.float64)
    s = np.array([float(student.get(k, 0.0)) for k in keys], dtype=np.float64)
    return keys, normalize(t), normalize(s)


def distillation_metrics(teacher: dict[str, float], student: dict[str, float]) -> dict[str, Any]:
    """Per-decision distillation geometry between teacher and student actions."""
    keys, t, s = align_distributions(teacher, student)
    return {
        "actions": keys,
        "teacher": t.tolist(),
        "student": s.tolist(),
        "reverse_kl": reverse_kl(s, t),
        "forward_kl": forward_kl(t, s),
        "jensen_shannon": jensen_shannon(s, t),
        "teacher_argmax": keys[int(np.argmax(t))],
        "student_argmax": keys[int(np.argmax(s))],
        "agreement": bool(int(np.argmax(t)) == int(np.argmax(s))),
    }


def summarize_steps(per_step: list[dict[str, Any]]) -> dict[str, float]:
    """Mean divergences across the per-step distillation records."""
    if not per_step:
        return {"mean_reverse_kl": 0.0, "mean_forward_kl": 0.0, "mean_jensen_shannon": 0.0}
    return {
        "mean_reverse_kl": float(np.mean([row["reverse_kl"] for row in per_step])),
        "mean_forward_kl": float(np.mean([row["forward_kl"] for row in per_step])),
        "mean_jensen_shannon": float(np.mean([row["jensen_shannon"] for row in per_step])),
    }


def _finite_nonnegative(value: Any) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return bool(np.isfinite(number) and number >= 0.0)


def _int_value(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalised(values: Any, *, atol: float = 1e-6) -> bool:
    try:
        arr = np.asarray(values, dtype=np.float64).reshape(-1)
    except (TypeError, ValueError):
        return False
    return bool(
        arr.size
        and np.all(np.isfinite(arr))
        and np.all(arr >= 0.0)
        and abs(float(arr.sum()) - 1.0) <= atol
    )


def _per_step_rows_valid(rows: Any) -> bool:
    if not isinstance(rows, list) or not rows:
        return False
    for row in rows:
        if not isinstance(row, dict):
            return False
        actions = row.get("actions") or []
        teacher = row.get("teacher") or []
        student = row.get("student") or []
        if not actions or len(actions) != len(teacher) or len(actions) != len(student):
            return False
        if not _normalised(teacher) or not _normalised(student):
            return False
        if not all(_finite_nonnegative(row.get(key)) for key in ("reverse_kl", "forward_kl", "jensen_shannon")):
            return False
        if row.get("teacher_argmax") not in actions or row.get("student_argmax") not in actions:
            return False
        if not isinstance(row.get("agreement"), bool):
            return False
    return True


def _mean_matches(payload: dict[str, Any], rows: list[dict[str, Any]], payload_key: str, row_key: str) -> bool:
    try:
        observed = float(payload.get(payload_key))
        expected = float(np.mean([float(row[row_key]) for row in rows]))
    except (KeyError, TypeError, ValueError):
        return False
    return abs(observed - expected) <= 1e-9


def validate_classroom_payload(payload: dict[str, Any], *, require_ok: bool = True) -> bool:
    """Validate the persisted classroom artifact against its measured claims."""
    rows = payload.get("per_step") or []
    if require_ok and payload.get("ok") is not True:
        return False
    if payload.get("schema") != SCHEMA or not _per_step_rows_valid(rows):
        return False
    if _int_value(payload.get("decision_count")) != len(rows):
        return False
    if _int_value(payload.get("steps")) < 1:
        return False
    if not all(
        _finite_nonnegative(payload.get(key))
        for key in (
            "mean_reverse_kl",
            "mean_forward_kl",
            "mean_jensen_shannon",
            "teacher_mean_belief_entropy",
            "student_mean_belief_entropy",
        )
    ):
        return False
    if not all(
        _mean_matches(payload, rows, payload_key, row_key)
        for payload_key, row_key in (
            ("mean_reverse_kl", "reverse_kl"),
            ("mean_forward_kl", "forward_kl"),
            ("mean_jensen_shannon", "jensen_shannon"),
        )
    ):
        return False
    try:
        teacher_cue = float(payload.get("teacher_cue_validity", -1.0))
        student_cue = float(payload.get("student_cue_validity", 2.0))
    except (TypeError, ValueError):
        return False
    if teacher_cue < student_cue:
        return False
    if payload.get("privileged_advantage") is not True:
        return False
    # The reported mean belief entropies must be the means of the persisted
    # per-rollout series — the gap claim is bound to its raw data, not a flag.
    for mean_key, series_key in (
        ("teacher_mean_belief_entropy", "teacher_belief_entropies"),
        ("student_mean_belief_entropy", "student_belief_entropies"),
    ):
        series = payload.get(series_key)
        if not isinstance(series, list) or not series:
            return False
        try:
            values = [float(v) for v in series]
        except (TypeError, ValueError):
            return False
        if not all(np.isfinite(v) and v >= 0.0 for v in values):
            return False
        if abs(float(payload.get(mean_key, -1.0)) - float(np.mean(values))) > 1e-9:
            return False
    if (
        not payload.get("teacher_config_hash")
        or payload.get("teacher_config_hash") == payload.get("student_config_hash")
    ):
        return False
    runtime = payload.get("runtime") or {}
    return bool(
        runtime.get("planner") == "sophisticated_inference"
        and _int_value(runtime.get("teacher_num_policies")) > 0
        and _int_value(runtime.get("student_num_policies")) > 0
    )


def _belief_entropy_series(result: SIRunResult) -> list[float]:
    """Per-step belief entropies (nats) from the rollout trace, finite rows only."""
    series: list[float] = []
    for row in result.trace_steps:
        value = row.get("belief_entropy")
        if value is not None and np.isfinite(float(value)):
            series.append(float(value))
    return series


def _agent_config(root: Path, cue_validity: float, cfg: ClassroomConfig) -> PymdpConfig:
    base = load_pymdp_config(root)
    base = apply_pymdp_overrides(base, steps=cfg.steps, seed=cfg.seed, logging_enabled=False)
    return replace(base, environment=replace(base.environment, cue_validity=cue_validity))


def run_classroom(project_root: Path, config: ClassroomConfig | None = None) -> ClassroomResult:
    """Run the privileged-teacher / on-policy-student T-maze and measure the gap."""
    if not pymdp_available():  # pragma: no cover - exercised only without pymdp
        raise RuntimeError("inferactively-pymdp is not installed")
    cfg = config or ClassroomConfig()
    root = Path(project_root).resolve()

    teacher_cfg = _agent_config(root, cfg.teacher_cue_validity, cfg)
    student_cfg = _agent_config(root, cfg.student_cue_validity, cfg)
    teacher: SIRunResult = run_si_tmaze(root, config=teacher_cfg)
    student: SIRunResult = run_si_tmaze(root, config=student_cfg)

    teacher_entropies = _belief_entropy_series(teacher)
    student_entropies = _belief_entropy_series(student)

    n = min(len(teacher.action_probabilities), len(student.action_probabilities))
    per_step: list[dict[str, Any]] = []
    for t in range(n):
        record = distillation_metrics(teacher.action_probabilities[t], student.action_probabilities[t])
        record["step"] = t
        record["teacher_belief_entropy"] = teacher_entropies[t] if t < len(teacher_entropies) else None
        record["student_belief_entropy"] = student_entropies[t] if t < len(student_entropies) else None
        per_step.append(record)

    summary = summarize_steps(per_step)
    return ClassroomResult(
        teacher_cue_validity=cfg.teacher_cue_validity,
        student_cue_validity=cfg.student_cue_validity,
        steps=cfg.steps,
        per_step=per_step,
        mean_reverse_kl=summary["mean_reverse_kl"],
        mean_forward_kl=summary["mean_forward_kl"],
        mean_jensen_shannon=summary["mean_jensen_shannon"],
        teacher_mean_belief_entropy=teacher.mean_belief_entropy,
        student_mean_belief_entropy=student.mean_belief_entropy,
        teacher_belief_entropies=teacher_entropies,
        student_belief_entropies=student_entropies,
        teacher_goal_reached=teacher.goal_reached,
        student_goal_reached=student.goal_reached,
        privileged_advantage=bool(teacher.mean_belief_entropy <= student.mean_belief_entropy + 1e-9),
        teacher_config_hash=teacher.config_hash,
        student_config_hash=student.config_hash,
        runtime={
            "teacher_num_policies": teacher.num_policies,
            "student_num_policies": student.num_policies,
            "planner": teacher.planner,
        },
    )


def build_payload(result: ClassroomResult) -> dict[str, Any]:
    """Build the canonical `firstprinciples.classroom` artifact payload from a run result."""
    payload = asdict(result)
    payload["schema"] = SCHEMA
    payload["decision_count"] = len(result.per_step)
    payload["ok"] = validate_classroom_payload(payload, require_ok=False)
    return payload


def write_classroom_artifact(project_root: Path, result: ClassroomResult) -> Path:
    root = Path(project_root).resolve()
    path = root / "output" / "data" / "firstprinciples" / "classroom.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_payload(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
