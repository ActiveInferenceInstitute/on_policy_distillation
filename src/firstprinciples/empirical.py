"""Curated empirical evidence for on-policy distillation (literature-reported).

These are numbers *reported in the literature*, not measured in this
repository: the Qwen3 technical report benchmark rows relayed by the Thinking
Machines on-policy-distillation post, plus Thinking Machines' own replication
context. They are encoded as
structured, source-attributed data so the manuscript can present them as
hydrated tokens with provenance rather than hard-coded prose. Every row carries
the direct bibkey it came from and the relay bibkey that motivates its inclusion;
nothing here is an experiment we ran.

The active-inference reading: on-policy distillation reaches higher accuracy at a
fraction of the compute of reinforcement learning because the per-token teacher
signal is a *dense* prediction-error (free-energy gradient) at every state the
student visits, whereas RL supplies one sparse scalar per trajectory.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

SCHEMA = "firstprinciples.empirical_benchmark.v1"
QWEN_SOURCE_LOCATOR = "Qwen3 Technical Report, Table 21"
QWEN_SOURCE_HEADING = "Comparison of reinforcement learning and on-policy distillation on Qwen3-8B"
QWEN_SOURCE_TABLE = "Table 21"
QWEN_SOURCE_URL = "https://arxiv.org/abs/2505.09388"
QWEN_SOURCE_ARXIV_ID = "2505.09388"

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
    relayed_by: str
    source_locator: str
    source_heading: str
    source_table: str
    source_url: str
    source_arxiv_id: str
    source_note: str


# Direct source: Qwen3 Technical Report Table 21 (@qwen2025technical_report),
# relayed and discussed by Thinking Machines Lab (@thinkingmachines2025opd).
BENCHMARKS: tuple[BenchmarkRow, ...] = (
    BenchmarkRow(
        "off_policy_distillation",
        55.0,
        55.6,
        None,
        "qwen2025technical_report",
        "thinkingmachines2025opd",
        QWEN_SOURCE_LOCATOR,
        QWEN_SOURCE_HEADING,
        QWEN_SOURCE_TABLE,
        QWEN_SOURCE_URL,
        QWEN_SOURCE_ARXIV_ID,
        "Qwen3 Table 21 value relayed by Thinking Machines as the off-policy distillation baseline.",
    ),
    BenchmarkRow(
        "reinforcement_learning",
        67.6,
        61.3,
        17920.0,
        "qwen2025technical_report",
        "thinkingmachines2025opd",
        QWEN_SOURCE_LOCATOR,
        QWEN_SOURCE_HEADING,
        QWEN_SOURCE_TABLE,
        QWEN_SOURCE_URL,
        QWEN_SOURCE_ARXIV_ID,
        "Qwen3 Table 21 RL baseline value relayed by Thinking Machines.",
    ),
    BenchmarkRow(
        "on_policy_distillation",
        74.4,
        63.3,
        1800.0,
        "qwen2025technical_report",
        "thinkingmachines2025opd",
        QWEN_SOURCE_LOCATOR,
        QWEN_SOURCE_HEADING,
        QWEN_SOURCE_TABLE,
        QWEN_SOURCE_URL,
        QWEN_SOURCE_ARXIV_ID,
        "Qwen3 Table 21 on-policy distillation value relayed by Thinking Machines.",
    ),
)

THINKING_MACHINES_REPLICATION: dict[str, object] = {
    "bibkey": "thinkingmachines2025opd",
    "aime24_accuracy": 70.0,
    "training_steps": 150,
    "efficiency_range_min": 9.0,
    "efficiency_range_max": 30.0,
    "note": (
        "Thinking Machines reports its own replication at about 70% AIME-24 "
        "in roughly 150 steps and frames the method as 9-30x more efficient "
        "than a reinforcement-learning baseline."
    ),
}


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
    header = "| Method | AIME'24 (%) | GPQA-Diamond (%) | GPU-hours | Direct source | Relay/context |\n"
    sep = "| --- | --- | --- | --- | --- | --- |\n"
    rows = "".join(
        f"| {r.method.replace('_', ' ')} | {r.aime24:.1f} | {r.gpqa_diamond:.1f} | "
        f"{'—' if r.gpu_hours is None else f'{r.gpu_hours:.0f}'} | "
        f"{r.bibkey} | {r.relayed_by} |\n"
        for r in BENCHMARKS
    )
    return header + sep + rows


def build_payload() -> dict[str, object]:
    """Build the canonical `firstprinciples.empirical_benchmark` artifact payload."""
    gain = accuracy_gain()
    reduction = compute_reduction()
    opd = _row("on_policy_distillation")
    rl = _row("reinforcement_learning")
    return {
        "schema": SCHEMA,
        "source": "literature_reported",
        "bibkey": "qwen2025technical_report",
        "direct_bibkey": "qwen2025technical_report",
        "source_locator": QWEN_SOURCE_LOCATOR,
        "source_heading": QWEN_SOURCE_HEADING,
        "source_table": QWEN_SOURCE_TABLE,
        "source_url": QWEN_SOURCE_URL,
        "source_arxiv_id": QWEN_SOURCE_ARXIV_ID,
        "relayed_by_bibkey": "thinkingmachines2025opd",
        "rows": as_records(),
        "row_count": len(BENCHMARKS),
        "compute_reduction_factor": reduction,
        "accuracy_gain": gain,
        "opd_aime24": opd.aime24,
        "rl_aime24": rl.aime24,
        "opd_gpu_hours": opd.gpu_hours,
        "rl_gpu_hours": rl.gpu_hours,
        "thinking_machines_replication": dict(THINKING_MACHINES_REPLICATION),
        "opd_beats_rl_on_accuracy": bool(opd.aime24 > rl.aime24),
        "opd_cheaper_than_rl": bool((opd.gpu_hours or 0) < (rl.gpu_hours or 0)),
        "ok": bool(opd.aime24 > rl.aime24 and reduction > 1.0),
    }
