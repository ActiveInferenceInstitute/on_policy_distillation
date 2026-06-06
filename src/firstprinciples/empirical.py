"""Curated empirical evidence for on-policy distillation (literature-reported).

These are numbers *reported in the literature* (the curated review), not measured
in this repository: the on-policy-distillation compute/accuracy benchmarks from
the Thinking Machines study and the GKD line of work. They are encoded as
structured, source-attributed data so the manuscript can present them as
hydrated tokens with provenance rather than hard-coded prose. Every row carries
the bibkey it came from; nothing here is an experiment we ran.

The active-inference reading: on-policy distillation reaches higher accuracy at a
fraction of the compute of reinforcement learning because the per-token teacher
signal is a *dense* prediction-error (free-energy gradient) at every state the
student visits, whereas RL supplies one sparse scalar per trajectory.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

SCHEMA = "firstprinciples.empirical_benchmark.v1"

__all__ = [
    "BenchmarkRow",
    "BENCHMARKS",
    "compute_reduction",
    "accuracy_gain",
    "as_records",
    "markdown_table",
    "build_payload",
]


@dataclass(frozen=True)
class BenchmarkRow:
    """One literature-reported training-method benchmark row."""

    method: str
    aime24: float  # AIME'24 accuracy (%)
    gpqa_diamond: float  # GPQA-Diamond accuracy (%)
    gpu_hours: float | None  # reported training GPU-hours (None if unreported)
    bibkey: str


# Source: Thinking Machines Lab on-policy distillation study (@thinkingmachines2025opd),
# Qwen3-8B-Base distilled from Qwen3-32B; figures as reported in the curated review.
BENCHMARKS: tuple[BenchmarkRow, ...] = (
    BenchmarkRow("off_policy_distillation", 55.0, 55.6, None, "thinkingmachines2025opd"),
    BenchmarkRow("reinforcement_learning", 67.6, 61.3, 17920.0, "thinkingmachines2025opd"),
    BenchmarkRow("on_policy_distillation", 74.4, 63.3, 1800.0, "thinkingmachines2025opd"),
)


def _row(name: str) -> BenchmarkRow:
    for row in BENCHMARKS:
        if row.method == name:
            return row
    raise KeyError(name)


def compute_reduction() -> float:
    """RL GPU-hours / on-policy-distillation GPU-hours (reported)."""
    rl = _row("reinforcement_learning").gpu_hours
    opd = _row("on_policy_distillation").gpu_hours
    if not rl or not opd:
        raise ValueError("compute reduction requires both GPU-hour figures")
    return float(rl / opd)


def accuracy_gain() -> dict[str, float]:
    """On-policy-distillation accuracy gain over the off-policy and RL baselines."""
    off = _row("off_policy_distillation")
    rl = _row("reinforcement_learning")
    opd = _row("on_policy_distillation")
    return {
        "aime24_over_off_policy": opd.aime24 - off.aime24,
        "aime24_over_rl": opd.aime24 - rl.aime24,
        "gpqa_over_rl": opd.gpqa_diamond - rl.gpqa_diamond,
    }


def as_records() -> list[dict[str, object]]:
    return [asdict(row) for row in BENCHMARKS]


def markdown_table() -> str:
    header = "| Method | AIME'24 (%) | GPQA-Diamond (%) | GPU-hours |\n"
    sep = "| --- | --- | --- | --- |\n"
    rows = "".join(
        f"| {r.method.replace('_', ' ')} | {r.aime24:.1f} | {r.gpqa_diamond:.1f} | "
        f"{'—' if r.gpu_hours is None else f'{r.gpu_hours:.0f}'} |\n"
        for r in BENCHMARKS
    )
    return header + sep + rows


def build_payload() -> dict[str, object]:
    gain = accuracy_gain()
    reduction = compute_reduction()
    opd = _row("on_policy_distillation")
    rl = _row("reinforcement_learning")
    return {
        "schema": SCHEMA,
        "source": "literature_reported",
        "bibkey": "thinkingmachines2025opd",
        "rows": as_records(),
        "row_count": len(BENCHMARKS),
        "compute_reduction_factor": reduction,
        "accuracy_gain": gain,
        "opd_aime24": opd.aime24,
        "rl_aime24": rl.aime24,
        "opd_gpu_hours": opd.gpu_hours,
        "rl_gpu_hours": rl.gpu_hours,
        "opd_beats_rl_on_accuracy": bool(opd.aime24 > rl.aime24),
        "opd_cheaper_than_rl": bool((opd.gpu_hours or 0) < (rl.gpu_hours or 0)),
        "ok": bool(opd.aime24 > rl.aime24 and reduction > 1.0),
    }
