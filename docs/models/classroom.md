# The Two-Agent Classroom

The classroom in
[`../../src/firstprinciples/classroom.py`](../../src/firstprinciples/classroom.py)
is the executable heart of the thesis: it runs two
[pymdp T-maze](tmaze-pymdp.md) agents side by side and reads the single-agent
rollout as a teacher/student pair. A **privileged teacher** gets a near-perfect
cue; an **on-policy student** gets an uninformative one. The per-decision reverse
KL between their first-action distributions is the distillation signal the
student would descend to absorb the teacher's privileged belief.

Manuscript home:
[`../../manuscript/12_results_si_tmaze.md`](../../manuscript/12_results_si_tmaze.md).

## The two agents

`run_classroom(project_root, ClassroomConfig(...))` builds two configs from the
canonical [`pymdp.yaml`](../../pymdp.yaml) via `_agent_config`, overriding only
`environment.cue_validity`, then runs `run_si_tmaze` for each. The defaults in
`ClassroomConfig` are:

- `teacher_cue_validity = 0.98` — the privileged cue that all but reveals the
  latent reward location, so the teacher's `q(π)` commits confidently.
- `student_cue_validity = 0.5` — the uninformative cue; the student must generate
  its own observations and infer against the teacher.
- `steps = 3`, `seed = 0`.

The teacher and student therefore differ only in cue access. `run_classroom`
requires pymdp (it drives two real sophisticated-inference rollouts); the metric
helpers (`align_distributions`, `distillation_metrics`, `summarize_steps`) are
pure and testable without pymdp.

## Teacher cue validity vs student

The asymmetry is the whole construction. In the manuscript the teacher runs at
cue validity `{{classroom_teacher_cue_validity}}` against a student at
`{{classroom_student_cue_validity}}`. `validate_classroom_payload` enforces that
the persisted teacher cue validity is not below the student's, that the two agents
have **different** config hashes, and that the runtime planner is
`sophisticated_inference` with positive policy counts for both — a forged or
identical-agent payload fails closed.

## Belief-entropy advantage

The measured advantage is **posterior sharpness, not task success**. The teacher's
stronger cue channel yields belief entropy
`{{classroom_teacher_belief_entropy_formatted}}` nats versus the student's
`{{classroom_student_belief_entropy_formatted}}` nats. `privileged_advantage` is
set to `teacher.mean_belief_entropy <= student.mean_belief_entropy + 1e-9`, and
the validator binds the reported means to the raw per-rollout entropy series — the
gap claim is tied to its data, not to a flag. The manuscript is explicit that on
this short rollout the sharper privileged posterior did **not** translate into
goal attainment: it records teacher goal-reached `{{classroom_teacher_goal_reached}}`
and student goal-reached `{{classroom_student_goal_reached}}`, and claims only
what the entropy series measures.

## Mean reverse-KL distillation signal

`distillation_metrics` aligns the teacher and student first-action distributions
on the union of action names and computes, per decision, the reverse KL, forward
KL, and Jensen–Shannon divergence (helpers from
`src/firstprinciples/divergences.py`). The headline quantity is the mean reverse
KL, reported as `{{classroom_mean_reverse_kl_formatted}}` nats — the finite toy
objective that maps onto the variational free energy `F = D_KL(q ‖ p) − log p(o)`.
This is the per-decision divergence signal evaluated along the **student's own
trajectory**, which is the active-inference principle of scoring beliefs on
visited states rather than the teacher's idealized path.

## Deterministic outputs

The run is deterministic: fixed `seed = 0`, the canonical SI planner, and
`action_selection: deterministic` in `pymdp.yaml`. `build_payload` /
`write_classroom_artifact` write
`output/data/firstprinciples/classroom.json` (schema
`firstprinciples.classroom.v1`) with the per-step records, the three mean
divergences, both belief-entropy series, the goal flags, and the two config
hashes. The figure `output/figures/classroom_distillation_signal.png` plots the
per-step divergences and a teacher-minus-student action-probability heatmap.

Generate it with:

```bash
uv run python scripts/generate_firstprinciples.py
```

## Scope

The classroom keeps **internal self-distillation separate from external
privileged-information distillation**: method families like OISD are cited as
analogues, but this figure's numbers come only from
`output/data/firstprinciples/classroom.json`. The effect shown is a toy
posterior-sharpness gap induced by the teacher's stronger cue channel — not a
prediction that a Markov blanket numerically fixes entropy in general, and not a
production measurement. The single comparison is generalized into a dose-response
curve by the [privilege sweep](privilege-sweep.md).
