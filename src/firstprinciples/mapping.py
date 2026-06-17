"""The formal correspondence between active inference and on-policy distillation.

This is the structural core of the paper's thesis. Each :class:`Correspondence`
row pairs an active-inference construct with its on-policy-distillation
counterpart and names the *shared formal object* that makes them the same thing
rather than an analogy. The table is queryable, renders to a manuscript table,
and validates (no empty fields, unique keys) so the gate machinery can treat the
mapping as an audited artifact rather than prose.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

__all__ = [
    "Correspondence",
    "CORRESPONDENCES",
    "correspondences",
    "as_records",
    "lookup",
    "markdown_table",
    "validate_mapping",
    "SCHEMA",
    "build_payload",
]

SCHEMA = "firstprinciples.correspondence_map.v1"


@dataclass(frozen=True)
class Correspondence:
    """One audited row of the active-inference <-> OPD dictionary."""

    ai_component: str
    opd_counterpart: str
    shared_object: str
    note: str


CORRESPONDENCES: tuple[Correspondence, ...] = (
    Correspondence(
        "Kullback-Leibler information divergence",
        "Teacher/student distribution discrepancy",
        "directional KL between two categorical laws",
        "KL is the common primitive underneath variational free energy, forward KD, reverse-KL OPD, and preference tilts.",
    ),
    Correspondence(
        "Mean-field variational family",
        "Student policy family pi_S(y | x)",
        "tractable approximate posterior family",
        "The variational-inference approximation is the same modelling move as restricting the student to its deployable policy class.",
    ),
    Correspondence(
        "Generative model p(o, s)",
        "Teacher policy pi_T(y | x, I)",
        "intractable target distribution",
        "The teacher is the posterior the student cannot directly sample; in "
        "self-distillation it is the same network conditioned on privileged I.",
    ),
    Correspondence(
        "Approximate posterior q(s)",
        "Student policy pi_S(y | x)",
        "variational distribution being optimised",
        "Both are the tractable family fit by minimising a KL to the target.",
    ),
    Correspondence(
        "Variational free energy F = D_KL(q || p) - log p(o)",
        "Per-token reverse-KL distillation loss",
        "reverse Kullback-Leibler divergence",
        "Zero iff student matches teacher in the finite target family; reverse-KL concentration is an optimization-dependent finite-model intuition.",
    ),
    Correspondence(
        "Active sampling to minimise F",
        "On-policy student rollouts",
        "the posterior generates its own observations",
        "Off-policy/passive updating leaves the visited-state mismatch that "
        "becomes exposure bias.",
    ),
    Correspondence(
        "Epistemic value (information gain)",
        "Teacher signal on novel student states",
        "expected-free-energy exploration term",
        "Dense supervision precisely where the student is uncertain.",
    ),
    Correspondence(
        "Expected free energy risk/ambiguity split",
        "Mode-seeking versus coverage-preserving distillation pressure",
        "decomposition of future loss into preference risk and uncertainty/ambiguity terms",
        "The diversity and adaptive-divergence artifacts treat pure reverse KL as incomplete when coverage is load-bearing.",
    ),
    Correspondence(
        "Expected free energy action selection (active sampling)",
        "On-policy choice of which states to roll out and distil on",
        "EFE-minimising data-collection policy; epistemic value equals the closeable student-teacher gap",
        "Formalised in the active-selection demo (sec:active_selection): minimising expected free energy "
        "selects the cue-visiting policy and closes the distillation gap exactly, while a pragmatic-only rule "
        "leaves it open. This is the active complement to the realized-rollout (VFE) reading: the identity "
        "gap_closed = epistemic is exact in this finite toy.",
    ),
    Correspondence(
        "Pragmatic value (prior preference)",
        "Reward-tilted distillation target",
        "exp(R / beta) tilt of the prior",
        "Reward-tilting is the preference prior of expected free energy and the "
        "KL-regularised preference objective of max-entropy RL/RLHF.",
    ),
    Correspondence(
        "Control-as-inference posterior",
        "KL-constrained RLHF / OPD target",
        "Boltzmann policy posterior proportional to pi_ref exp(R / beta)",
        "Control-estimation duality, trajectory inference, maximum-entropy IRL, active inference, maximum-entropy RL, "
        "DPO/RLHF, and reward-tilted OPD share this normalised target.",
    ),
    Correspondence(
        "RL-as-inference caveat",
        "When reward-tilted posteriors stop matching deployable policy learning",
        "modelled optimality variable plus approximation assumptions",
        "The manuscript uses RL-as-inference as a finite target identity, not a claim that all RL algorithms are inference procedures.",
    ),
    Correspondence(
        "Maximum-entropy trajectory posterior",
        "Student rollout distribution under reward tilt",
        "path distribution proportional to reference dynamics times exp(return / beta)",
        "The Ziebart/Toussaint/Todorov lineage is the trajectory-level version of the same posterior target.",
    ),
    Correspondence(
        "Direct preference posterior",
        "DPO-style preference target for distillation",
        "reference policy tilted by an implicit reward model",
        "Preference optimisation supplies a reward-model posterior, while OPD supplies dense teacher targets on sampled states.",
    ),
    Correspondence(
        "Markov blanket",
        "Teacher/student context asymmetry",
        "conditional-independence boundary",
        "The privileged context I is sensed by the teacher and statistically "
        "screened from the student; the boundary is informational, not physical.",
    ),
    Correspondence(
        "Predictive-coding hierarchy",
        "Teacher predictions and student prediction-error correction",
        "top-down target and bottom-up residual",
        "The teacher supplies a privileged top-down target while the student "
        "updates from the residual on its own generated trajectory.",
    ),
    Correspondence(
        "Privileged sensory access",
        "Privileged information I (hint, trace, feedback)",
        "conditioning variable absent at inference",
        "LUPI: training-time-only information accelerates learning.",
    ),
    Correspondence(
        "Context-conditioned teacher",
        "Teacher scored with instructions, scratchpads, demonstrations, or verified traces removed at deployment",
        "training-time conditioning context",
        "Context distillation and on-policy context distillation make the privileged-information channel explicit for language models.",
    ),
    Correspondence(
        "Transferable versus shortcut privilege",
        "Evidence-localized OPD updates",
        "evidence mask over token positions supported by privileged context",
        "Privileged information can induce side effects; evidence masks and exposure schedules localize what the student should internalize.",
    ),
    Correspondence(
        "Perception-action loop",
        "generate rollout -> distill -> update policy",
        "iterated variational optimisation",
        "Each OPD step is one turn of the active-inference cycle.",
    ),
    Correspondence(
        "Sophisticated inference (beliefs about beliefs)",
        "Teacher conditioned on verified student traces",
        "recursive expected free energy",
        "OPSD/SDPG condition the self-teacher on the student's own outputs.",
    ),
    Correspondence(
        "Precision / inverse temperature gamma",
        "Distillation temperature beta",
        "confidence weighting of the target",
        "Both sharpen or flatten the target distribution.",
    ),
    Correspondence(
        "Divergence direction and estimator reliability",
        "Forward-KL, reverse-KL, skew-KL, trust-region, and control-variate OPD variants",
        "choice of projection geometry and gradient estimator under distribution mismatch",
        "Recent OPD stabilizers are reliability controls around the same KL geometry; alpha/f-divergence work makes the coverage story a design space, not a universal law.",
    ),
    Correspondence(
        "Long-horizon teacher reliability",
        "Step-wise, long-context, and agentic OPD filters",
        "state-dependent trust in dense teacher targets",
        "Dense token supervision helps only where teacher targets remain compatible and reliable under the student's induced trajectory.",
    ),
    Correspondence(
        "Homeostasis (preserving priors while adapting)",
        "Continual learning without forgetting (SDFT)",
        "free-energy minimisation against a moving model",
        "On-policy self-distillation accumulates skills without regression.",
    ),
    Correspondence(
        "Sheaf local-to-global gluing",
        "Manuscript artifact contract and verifier composition",
        "finite consistency law over local evidence fragments",
        "Applied sheaf language is used to keep heterogeneous artifacts coherent, not to assert unmeasured cohomology.",
    ),
)


def correspondences() -> tuple[Correspondence, ...]:
    """Return the immutable correspondence table."""
    return CORRESPONDENCES


def as_records() -> list[dict[str, str]]:
    """Return the table as a list of plain dicts (for JSON artifacts)."""
    return [asdict(row) for row in CORRESPONDENCES]


def lookup(ai_component: str) -> Correspondence:
    """Return the row whose active-inference component matches (case-folded)."""
    key = ai_component.strip().casefold()
    for row in CORRESPONDENCES:
        if row.ai_component.casefold() == key:
            return row
    raise KeyError(f"no correspondence for active-inference component {ai_component!r}")


def markdown_table() -> str:
    """Render the correspondence table as GitHub-flavoured markdown."""
    header = "| Active inference | On-policy distillation | Shared formal object |\n"
    sep = "| --- | --- | --- |\n"
    rows = "".join(
        f"| {r.ai_component} | {r.opd_counterpart} | {r.shared_object} |\n" for r in CORRESPONDENCES
    )
    return header + sep + rows


def validate_mapping() -> list[str]:
    """Return a list of integrity issues (empty list means the map is sound)."""
    issues: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(CORRESPONDENCES):
        for field_name in ("ai_component", "opd_counterpart", "shared_object", "note"):
            if not getattr(row, field_name).strip():
                issues.append(f"row {index} has empty {field_name}")
        key = row.ai_component.casefold()
        if key in seen:
            issues.append(f"duplicate ai_component at row {index}: {row.ai_component!r}")
        seen.add(key)
    return issues


def build_payload() -> dict[str, object]:
    """Assemble the validated correspondence-map artifact."""
    issues = validate_mapping()
    return {
        "schema": SCHEMA,
        "row_count": len(CORRESPONDENCES),
        "rows": as_records(),
        "issues": issues,
        "ok": not issues,
    }
