"""The same situation, two frameworks: active inference (pymdp/energy) and ML (jax).

This is the most direct demonstration of the thesis: take ONE scenario and solve
it both ways.

* Active-inference side (``energy.GenerativeModel``): the teacher is the exact
  Bayesian posterior ``p(s|o)`` -- the unique minimiser of variational free energy
  (``F = -ln p(o)`` there). This is the "generative model conditioned on
  privileged beliefs".
* Machine-learning side (``jax`` autodiff -- a standard ML framework): a student
  categorical policy with logits ``theta`` is trained by gradient descent on the
  reverse-KL on-policy distillation loss ``D_KL(softmax(theta) || teacher)``.

Both converge to the SAME distribution: the ML-distilled student reproduces the
active-inference posterior, and its free energy reaches the same minimum. The
reverse-KL distillation gradient computed by jax autodiff IS the variational
free-energy gradient -- the equivalence, executed in two frameworks.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .divergences import normalize, reverse_kl
from .energy import GenerativeModel, evidence, posterior, vfe_complexity_accuracy

ArrayF = NDArray[np.float64]

SCHEMA = "firstprinciples.parallel_demo.v1"

__all__ = ["MLDistillResult", "ml_distill_to_teacher", "build_payload"]


@dataclass(frozen=True)
class MLDistillResult:
    student: list[float]
    reverse_kl_first: float
    reverse_kl_last: float
    steps: int
    converged: bool
    loss_trajectory: list[float]
    trajectory_steps: list[int]


def ml_distill_to_teacher(
    teacher: ArrayF, *, steps: int = 800, lr: float = 0.5, tol: float = 1e-5, record_every: int = 20
) -> MLDistillResult:
    """Train a student policy to a teacher by jax-autodiff reverse-KL distillation.

    Standard ML framework: parameterise the student as ``softmax(theta)`` and run
    gradient descent on the reverse-KL distillation loss using ``jax.grad``. The
    loss is minimised (at zero) exactly when the student equals the teacher. The
    per-step loss trajectory is recorded (every ``record_every`` steps) so the
    convergence to the active-inference posterior can be visualised.
    """
    import jax
    import jax.numpy as jnp

    target = jnp.asarray(normalize(teacher))

    def loss(theta: "jax.Array") -> "jax.Array":
        q = jax.nn.softmax(theta)
        return jnp.sum(q * (jnp.log(q) - jnp.log(target)))

    grad = jax.grad(loss)
    theta = jnp.zeros(target.shape[0])
    first = float(loss(theta))
    trajectory: list[float] = [first]
    traj_steps: list[int] = [0]
    for step in range(1, steps + 1):
        theta = theta - lr * grad(theta)
        if step % record_every == 0 or step == steps:
            trajectory.append(float(loss(theta)))
            traj_steps.append(step)
    student = np.asarray(jax.nn.softmax(theta), dtype=np.float64)
    last = reverse_kl(student, normalize(teacher))
    return MLDistillResult(
        student=student.tolist(),
        reverse_kl_first=first,
        reverse_kl_last=last,
        steps=steps,
        converged=bool(last < tol),
        loss_trajectory=trajectory,
        trajectory_steps=traj_steps,
    )


def _canonical_model() -> GenerativeModel:
    return GenerativeModel(
        prior=np.array([0.5, 0.5], dtype=np.float64),
        likelihood=np.array([[0.85, 0.15], [0.15, 0.85]], dtype=np.float64),
        preferences=np.array([0.9, 0.1], dtype=np.float64),
    )


def build_payload() -> dict[str, object]:
    """Solve one scenario in both frameworks and certify they agree.

    The active-inference teacher is the exact posterior p(s|o); the ML student is
    obtained by jax-autodiff reverse-KL distillation. They must coincide, and the
    distilled student's variational free energy must reach -ln p(o).
    """
    model = _canonical_model()
    o = 0
    teacher = posterior(model, o)  # active-inference target (VFE minimiser)
    result = ml_distill_to_teacher(teacher)
    student = np.asarray(result.student, dtype=np.float64)
    max_abs_diff = float(np.max(np.abs(student - teacher)))
    f_student, _, _ = vfe_complexity_accuracy(student, model, o)
    neg_log_evidence = float(-np.log(evidence(model, o)))
    return {
        "schema": SCHEMA,
        "scenario": "two-state reward-location inference with an informative cue",
        "active_inference_teacher_posterior": teacher.tolist(),
        "ml_distilled_student": result.student,
        "max_abs_difference": max_abs_diff,
        "reverse_kl_first": result.reverse_kl_first,
        "reverse_kl_last": result.reverse_kl_last,
        "loss_trajectory": result.loss_trajectory,
        "trajectory_steps": result.trajectory_steps,
        "student_free_energy": f_student,
        "neg_log_evidence": neg_log_evidence,
        "free_energy_matches_minimum": bool(abs(f_student - neg_log_evidence) < 1e-3),
        "frameworks_agree": bool(max_abs_diff < 1e-3 and result.converged),
        "ok": bool(max_abs_diff < 1e-3 and abs(f_student - neg_log_evidence) < 1e-3),
    }
