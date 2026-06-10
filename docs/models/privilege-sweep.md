# The Teacher-Privilege Dose-Response Sweep

The privilege sweep in
[`../../src/firstprinciples/privilege.py`](../../src/firstprinciples/privilege.py)
turns the single [classroom](classroom.md) comparison into a dose-response
experiment: it holds the student fixed and uninformative, varies the teacher's
cue privilege across a grid, and reports how the belief-entropy advantage and the
reverse-KL distillation signal scale. It carries its own identical-agent control.

Manuscript home:
[`../../manuscript/12_results_si_tmaze.md`](../../manuscript/12_results_si_tmaze.md).
The deterministic toy-sweep artifacts that frame the analytical grid alongside it
live in
[`../../src/roadmap_tracks/toy_sweep.py`](../../src/roadmap_tracks/toy_sweep.py).

## Sweep design

`run_privilege_sweep(project_root, PrivilegeSweepConfig(...))` runs the real
pymdp classroom (`run_classroom`) once per teacher cue-validity level. The
`PrivilegeSweepConfig` defaults are:

- `teacher_cue_validities = (0.5, 0.7, 0.9, 0.98)`
- `student_cue_validity = 0.5` (fixed, uninformative)
- `steps = 2`, `seed = 0`

Each level records the mean reverse KL, the teacher and student belief
entropies, the `privileged_advantage` flag, and the derived `entropy_gap`
(student minus teacher). The sweep is framed as a Science-style experiment with
explicit hypotheses encoded in the payload: `h1_entropy_falls_with_privilege`,
`h2_signal_grows_with_privilege`, `h3_gap_grows_with_privilege`, and
`h4_baseline_gap_zero`, plus the Spearman `rank_correlation` of validity against
signal, entropy, and gap. Because it drives real pymdp rollouts (two per level),
it requires pymdp and is not part of the default fast pipeline.

## The identical-agent control

When the teacher's cue validity equals the student's (`0.5 == 0.5` at the first
grid point), the two agents run **identical configs**, so the entropy gap is
exactly zero by construction. This `baseline_gap` is a wiring / fabrication check
— identical configurations cannot differ — not a control for the effect itself.
A nonzero baseline gap would falsify the harness. The manuscript reports it as
`{{privilege_sweep_baseline_gap}}` and is careful to describe it as a wiring
check rather than an effect control.

## Noise floor

Reverse-KL values at low cue validity sit at the level of float noise from the
deterministic rollouts (on the order of `1e-7` nats). The manuscript applies a
`1e-3`-nat floor — four orders of magnitude above that observed rollout noise —
before treating any signal as real. The reported "first appreciable value" is the
first level whose mean reverse KL clears that floor
(`{{privilege_sweep_first_nonzero_kl}}` nats at cue validity
`{{privilege_sweep_first_nonzero_validity}}`).

## The nonlinearity finding and its honest framing

The belief-entropy advantage appears only at the top of the grid: it stays at
zero through cue validity `{{privilege_sweep_last_flat_validity}}` and is
`{{privilege_sweep_top_gap}}` nats at `{{privilege_sweep_top_validity}}`. The
manuscript does **not** claim a sharp threshold versus a steep slope, because the
grid has a single level between those two points — the onset is *resolution-
limited*. It claims only that the advantage is "strongly nonlinear in cue
validity." The mean reverse-KL signal is the more sensitive detector: it rises
monotonically across the sweep (gap/validity rank correlation
`{{privilege_sweep_gap_rank_correlation}}`), and the claim rests on that monotone
rise rather than any single level. Across all of this the framing is explicit:

> these are deterministic toy measurements, not significance claims.

There is no sampling, no random seed beyond the fixed `seed = 0`, and therefore
no uncertainty intervals — the rank correlation is a description of a fixed grid,
not an inferential statistic.

## Artifact and generation

The sweep payload (schema `firstprinciples.privilege_sweep.v1`) is written to
`output/data/firstprinciples/privilege_sweep.json` and visualized in
`output/figures/privilege_dose_response.png`. Generate via:

```bash
uv run python scripts/generate_firstprinciples.py
```

## Scope

A deterministic dose-response over a four-level cue-validity grid with a built-in
wiring check. It witnesses that the reverse-KL distillation signal registers
privilege that posterior-entropy summaries miss — exactly what the thesis
predicts if the reverse-KL loss is the free-energy gradient the student descends.
It is not inferential statistics, not a threshold estimate, and not a production
result.
