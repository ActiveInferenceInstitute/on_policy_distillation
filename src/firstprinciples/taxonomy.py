"""Structured taxonomy of the on-policy distillation literature.

A machine-readable distillation of the Awesome-LLM-On-Policy-Distillation
survey (github.com/nick7nlp/Awesome-LLM-On-Policy-Distillation): the methods,
their signal sources, divergence objectives, the 2026 loss-family shares, and
the application domains. Encoded as data (not prose) so the manuscript and the
gates can both consume it and so claims about the field are auditable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

__all__ = [
    "Method",
    "METHODS",
    "LOSS_SHARES",
    "SIGNAL_SOURCES",
    "DOMAINS",
    "methods",
    "on_policy_methods",
    "privileged_info_methods",
    "loss_share_total",
    "as_records",
    "markdown_table",
    "SCHEMA",
    "build_payload",
]

SCHEMA = "firstprinciples.opd_taxonomy.v1"


@dataclass(frozen=True)
class Method:
    """One on-policy distillation method with its structural attributes."""

    name: str
    acronym: str
    year: int
    bibkey: str
    signal_source: str
    divergence: str
    on_policy: bool
    privileged_info: bool
    note: str


METHODS: tuple[Method, ...] = (
    Method(
        "Distilling the Knowledge in a Neural Network", "KD", 2015, "hinton2015distilling",
        "white_box_logit", "forward_kl", False, False,
        "The off-policy baseline OPD corrects: teacher-generated data, forward KL.",
    ),
    Method(
        "MiniLLM", "MiniLLM", 2024, "gu2024minillm",
        "white_box_logit", "reverse_kl", True, False,
        "First reverse-KL LLM distillation via policy gradient (mode-seeking).",
    ),
    Method(
        "Generalized Knowledge Distillation", "GKD", 2024, "agarwal2024gkd",
        "white_box_logit", "flexible", True, False,
        "Canonical OPD: student rollouts, per-token teacher scoring, any divergence.",
    ),
    Method(
        "Self-Distilled Reasoner", "OPSD", 2026, "zhao2026opsd",
        "self_privileged", "clipped_reverse_kl", True, True,
        "Single model teacher/student via verified-trace context; per-token KL clip.",
    ),
    Method(
        "Self-Distillation Fine-Tuning", "SDFT", 2026, "shenfeld2026sdft",
        "self_privileged", "reverse_kl", True, True,
        "In-context demonstration as self-teacher; continual learning, no forgetting.",
    ),
    Method(
        "Self-Distillation Policy Optimization", "SDPO", 2026, "hubotter2026sdpo",
        "self_external_feedback", "kl_plus_rl", True, True,
        "Rich textual feedback as dense signal; 3x fewer attempts at test time.",
    ),
    Method(
        "Self-Distilled Policy Gradient", "SDPG", 2026, "liu2026sdpg",
        "self_privileged", "kl_plus_rl", True, True,
        "Full-vocabulary on-policy self-distillation term on a clipped GRPO loss.",
    ),
    Method(
        "Privileged Information Distillation", "pi-Distill", 2026, "penaloza2026pidistill",
        "self_privileged", "variational_em", True, True,
        "Joint shared-parameter teacher/student; variational-EM unification.",
    ),
)

# 2026 loss-family shares from the survey (fractions of surveyed papers).
LOSS_SHARES: dict[str, float] = {
    "kl_plus_rl": 0.23,
    "reverse_kl": 0.23,
    "forward_kl": 0.21,
    "symmetric_jsd": 0.13,
    "advantage_weighted": 0.16,
    "preference_f_divergence": 0.04,
}

SIGNAL_SOURCES: tuple[str, ...] = (
    "white_box_logit",
    "black_box_api",
    "self_privileged",
    "self_pure",
    "self_external_feedback",
)

DOMAINS: tuple[str, ...] = (
    "long_context",
    "vision_language",
    "autonomous_driving",
    "multi_turn_agents",
    "continual_learning",
    "safety_alignment",
    "protein_design",
    "diffusion_llms",
)


def methods() -> tuple[Method, ...]:
    return METHODS


def on_policy_methods() -> list[Method]:
    return [m for m in METHODS if m.on_policy]


def privileged_info_methods() -> list[Method]:
    return [m for m in METHODS if m.privileged_info]


def loss_share_total() -> float:
    """Total of the loss-family shares (should be ~1.0)."""
    return float(sum(LOSS_SHARES.values()))


def as_records() -> list[dict[str, object]]:
    return [asdict(m) for m in METHODS]


def markdown_table() -> str:
    header = "| Method | Year | Signal source | Divergence | On-policy | Privileged info |\n"
    sep = "| --- | --- | --- | --- | --- | --- |\n"
    rows = "".join(
        f"| {m.acronym} | {m.year} | {m.signal_source} | {m.divergence} | "
        f"{'yes' if m.on_policy else 'no'} | {'yes' if m.privileged_info else 'no'} |\n"
        for m in METHODS
    )
    return header + sep + rows


def build_payload() -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "method_count": len(METHODS),
        "on_policy_count": len(on_policy_methods()),
        "privileged_info_count": len(privileged_info_methods()),
        "methods": as_records(),
        "loss_shares": dict(LOSS_SHARES),
        "loss_share_total": loss_share_total(),
        "signal_sources": list(SIGNAL_SOURCES),
        "domains": list(DOMAINS),
    }
