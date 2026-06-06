"""Tests for the two-agent active-inference distillation classroom.

The pure metric helpers run everywhere; the full two-agent rollout requires
pymdp and is marked accordingly (it runs two sophisticated-inference searches).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from firstprinciples import classroom
from firstprinciples.classroom import ClassroomConfig
from simulation.si_loop import pymdp_available

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_classroom_config_validation() -> None:
    with pytest.raises(ValueError):
        ClassroomConfig(teacher_cue_validity=1.5)
    with pytest.raises(ValueError):
        ClassroomConfig(steps=0)


def test_align_distributions_union_of_keys() -> None:
    teacher = {"a": 0.9, "b": 0.1}
    student = {"a": 0.5, "c": 0.5}
    keys, t, s = classroom.align_distributions(teacher, student)
    assert keys == ["a", "b", "c"]
    assert t.sum() == pytest.approx(1.0)
    assert s.sum() == pytest.approx(1.0)
    with pytest.raises(ValueError):
        classroom.align_distributions({}, {})


def test_distillation_metrics_on_synthetic_dists() -> None:
    teacher = {"left": 0.95, "right": 0.05}
    student = {"left": 0.55, "right": 0.45}
    metrics = classroom.distillation_metrics(teacher, student)
    assert metrics["reverse_kl"] >= 0.0
    assert metrics["forward_kl"] >= 0.0
    assert metrics["teacher_argmax"] == "left"
    assert metrics["agreement"] is True


def test_summarize_steps_empty_and_nonempty() -> None:
    assert classroom.summarize_steps([])["mean_reverse_kl"] == 0.0
    per_step = [
        {"reverse_kl": 0.2, "forward_kl": 0.3, "jensen_shannon": 0.1},
        {"reverse_kl": 0.4, "forward_kl": 0.5, "jensen_shannon": 0.2},
    ]
    summary = classroom.summarize_steps(per_step)
    assert summary["mean_reverse_kl"] == pytest.approx(0.3)


@pytest.mark.requires_pymdp
@pytest.mark.timeout(300)
@pytest.mark.skipif(not pymdp_available(), reason="inferactively-pymdp not installed")
def test_run_classroom_measures_privileged_advantage(tmp_path: Path) -> None:
    cfg = ClassroomConfig(teacher_cue_validity=0.98, student_cue_validity=0.5, steps=2, seed=0)
    result = classroom.run_classroom(PROJECT_ROOT, cfg)
    assert result.per_step, "classroom must produce per-step distillation records"
    assert result.mean_reverse_kl >= 0.0
    assert result.teacher_config_hash != result.student_config_hash
    payload = classroom.build_payload(result)
    assert payload["schema"] == classroom.SCHEMA
    assert payload["ok"] is True
    # artifact round-trips
    path = classroom.write_classroom_artifact(tmp_path, result)
    reloaded = json.loads(path.read_text(encoding="utf-8"))
    assert reloaded["schema"] == classroom.SCHEMA
