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
        "Zero iff student matches teacher; mode-seeking; the OPD loss is F.",
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
        "Pragmatic value (prior preference)",
        "Reward-tilted distillation target",
        "exp(R / beta) tilt of the prior",
        "Reward-tilting is the preference prior of expected free energy.",
    ),
    Correspondence(
        "Markov blanket",
        "Teacher/student context asymmetry",
        "conditional-independence boundary",
        "The privileged context I is sensed by the teacher, screened from the "
        "student.",
    ),
    Correspondence(
        "Privileged sensory access",
        "Privileged information I (hint, trace, feedback)",
        "conditioning variable absent at inference",
        "LUPI: training-time-only information accelerates learning.",
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
        "Homeostasis (preserving priors while adapting)",
        "Continual learning without forgetting (SDFT)",
        "free-energy minimisation against a moving model",
        "On-policy self-distillation accumulates skills without regression.",
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
