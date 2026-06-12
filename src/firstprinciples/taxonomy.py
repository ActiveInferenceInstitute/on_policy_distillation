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
        "Model Compression", "MC", 2006, "bucila2006model_compression",
        "teacher_predictions", "supervised_model_compression", False, False,
        "Pre-Hinton compression lineage: replace a larger model with a smaller student trained on teacher outputs.",
    ),
    Method(
        "Sequence-Level Knowledge Distillation", "SeqKD", 2016, "kim2016sequence_kd",
        "sequence_teacher", "sequence_level_forward_kl", False, False,
        "Moves KD from token labels to teacher-generated sequences; the off-policy sequence baseline OPD revisits.",
    ),
    Method(
        "Policy Distillation", "PD", 2016, "rusu2016policy_distillation",
        "policy_teacher", "policy_kl", False, False,
        "Reinforcement-learning policy distillation ancestor: transfer action distributions across tasks or agents.",
    ),
    Method(
        "Distilling Policy Distillation", "DPD", 2019, "czarnecki2019distilling_policy",
        "policy_teacher", "policy_distillation_loss", False, False,
        "Clarifies the policy-distillation objective family before the LLM on-policy formulation.",
    ),
    Method(
        "Direct Preference Optimization", "DPO", 2023, "rafailov2023dpo",
        "preference_pairs", "reward_tilted_posterior", False, False,
        "Preference posterior context: the KL-regularised reward tilt used in OPD/RLHF correspondences.",
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
        "DistiLLM", "DistiLLM", 2024, "ko2024distillm",
        "mixed_teacher_student", "skew_kl", False, False,
        "Efficient middle path: skew KL plus adaptive off-policy reuse of student-generated outputs.",
    ),
    Method(
        "DistiLLM-2", "DistiLLM-2", 2025, "ko2025distillm2",
        "contrastive_teacher_student", "contrastive_logit_distillation", False, False,
        "Contrastive KD caveat: teacher and student-generated responses may need different objective pressure.",
    ),
    Method(
        "Speculative Knowledge Distillation", "SpecKD", 2024, "xu2024speculative_kd",
        "interleaved_teacher_student", "speculative_sequence_kd", True, False,
        "Contextual neighbor: interleaved teacher/student sampling addresses the teacher-student gap.",
    ),
    Method(
        "Black-Box On-Policy Distillation", "GAD", 2025, "ye2025blackbox_opd",
        "black_box_api", "black_box_gradient_approximation", True, False,
        "Black-box OPD context: on-policy supervision when only API-level teacher access is available.",
    ),
    Method(
        "Learning by Distilling Context", "ContextDistill", 2022, "snell2022context_distillation",
        "context_conditioned_teacher", "context_distillation", False, True,
        "LM precedent for internalizing instructions, scratchpads, or examples that are absent at inference.",
    ),
    Method(
        "On-Policy Context Distillation for Language Models", "OPCD", 2026, "ye2026context_distillation",
        "context_conditioned_teacher", "reverse_kl", True, True,
        "Direct bridge: student rollouts scored by a context-conditioned teacher.",
    ),
    Method(
        "EDGE-OPD", "EDGE-OPD", 2026, "lazaridis2026edge_opd",
        "evidence_masked_privilege", "evidence_masked_reverse_kl", True, True,
        "Privileged context must be localized to transferable evidence rather than side effects.",
    ),
    Method(
        "DeepSeek-R1", "DeepSeek-R1", 2025, "deepseek2025r1",
        "rl_reasoning", "kl_plus_rl_reasoning", True, False,
        "Reasoning-distillation context only; no DeepSeek benchmark is reproduced by this project.",
    ),
    Method(
        "Qwen3 Technical Report", "Qwen3", 2025, "qwen2025technical_report",
        "reasoning_distillation_report", "opd_rl_comparison", True, False,
        "Direct source for the literature-reported OPD-vs-RL reasoning benchmark rows.",
    ),
    Method(
        "Mitigating Exposure Bias in LLM Distillation", "IL-Distill", 2025, "pozzi2025exposure_distill",
        "student_rollout_imitation", "imitation_learning", True, False,
        "Distillation framed as imitation learning to control exposure bias over generated continuations.",
    ),
    Method(
        "KL for a KL: On-Policy Distillation with Control Variate Baseline", "vOPD", 2026, "oh2026vopd",
        "control_variate_teacher", "variance_reduced_reverse_kl", True, False,
        "Stabilization neighbor: control-variate baselines reduce noisy on-policy KL gradients.",
    ),
    Method(
        "Trust Region On-Policy Distillation", "TrOPD", 2026, "xing2026tropd",
        "trust_region_teacher", "trust_region_reverse_kl", True, False,
        "Stabilization neighbor: restricts OPD to reliable teacher-supervision regions.",
    ),
    Method(
        "Stable On-Policy Distillation through Adaptive Target Reformulation", "Veto", 2026, "jang2026veto",
        "adaptive_target", "adaptive_target_reformulation", True, False,
        "Stabilization neighbor: reforms unreliable targets under teacher/student distribution mismatch.",
    ),
    Method(
        "Rethinking On-Policy Distillation of Large Language Models", "OPD-Recipe", 2026, "li2026rethinking_opd",
        "compatibility_diagnostics", "reverse_kl_with_recovery_recipe", True, False,
        "Mechanism paper: OPD success depends on teacher-student compatibility and genuinely new teacher capability.",
    ),
    Method(
        "Demystifying OPD", "StableOPD", 2026, "luo2026demystifying_opd",
        "rollout_mixture_teacher", "reference_constrained_reverse_kl", True, False,
        "Failure-mode paper: length inflation and truncation collapse require stabilization.",
    ),
    Method(
        "Adaptive Teacher Exposure for Self-Distillation in LLM Reasoning", "ATESD", 2026, "han2026adaptive_teacher_exposure",
        "adaptive_privileged_exposure", "exposure_controlled_reverse_kl", True, True,
        "Treats how much privileged reasoning the teacher sees as a learnable training-time control.",
    ),
    Method(
        "f-OPD: Stabilizing Long-Horizon On-Policy Distillation with Freshness-Aware Control",
        "f-OPD",
        2026,
        "chen2026freshness_opd",
        "freshness_aware_async_buffer",
        "freshness_weighted_reverse_kl",
        True,
        False,
        "Asynchronous long-horizon OPD pressure case: tracks rollout and supervision staleness rather than a local toy benchmark.",
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
    Method(
        "Entropy-Aware On-Policy Distillation", "EOPD", 2026, "jin2026entropy_opd",
        "white_box_logit", "entropy_gated_forward_reverse_kl", True, False,
        "Teacher-entropy gate adds forward KL in high-uncertainty regions to preserve diversity.",
    ),
    Method(
        "Hybrid Policy Distillation", "HPD", 2026, "zhu2026hpd",
        "hybrid_rollout", "hybrid_forward_reverse_kl", True, False,
        "Unifies forward- and reverse-KL policy distillation as a stability/efficiency trade-off.",
    ),
    Method(
        "SOD: Step-wise On-policy Distillation for Small Language Model Agents", "SOD", 2026, "zhong2026sod",
        "stepwise_agent_rollout", "step_weighted_reverse_kl", True, False,
        "Agentic long-horizon OPD: attenuates misleading teacher signals when step divergence grows.",
    ),
    Method(
        "OPSDL", "OPSDL", 2026, "zhang2026opsdl",
        "long_context_self_teacher", "pointwise_reverse_kl", True, True,
        "Long-context self-distillation: short-context evidence supervises long-context rollouts.",
    ),
    Method(
        "ViCuR", "ViCuR", 2026, "tian2026vicur",
        "recoverable_visual_privilege", "visual_privilege_opd", True, True,
        "Multimodal future-work neighbor: recoverable visual cues as privileged training signal.",
    ),
    Method(
        "Visual-Advantage On-Policy Distillation", "VA-OPD", 2026, "liu2026visual_advantage_opd",
        "visual_advantage_teacher", "visual_advantage_weighted_kl", True, True,
        "Vision-language OPD caveat: only a minority of high-visual-advantage tokens carry the visual signal.",
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
    "teacher_predictions",
    "sequence_teacher",
    "policy_teacher",
    "preference_pairs",
    "black_box_api",
    "mixed_teacher_student",
    "contrastive_teacher_student",
    "interleaved_teacher_student",
    "context_conditioned_teacher",
    "evidence_masked_privilege",
    "control_variate_teacher",
    "trust_region_teacher",
    "adaptive_target",
    "compatibility_diagnostics",
    "rollout_mixture_teacher",
    "adaptive_privileged_exposure",
    "freshness_aware_async_buffer",
    "rl_reasoning",
    "reasoning_distillation_report",
    "student_rollout_imitation",
    "self_privileged",
    "self_pure",
    "self_external_feedback",
    "hybrid_rollout",
    "stepwise_agent_rollout",
    "long_context_self_teacher",
    "recoverable_visual_privilege",
    "visual_advantage_teacher",
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
    """Build the canonical `firstprinciples.opd_taxonomy` artifact payload."""
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
