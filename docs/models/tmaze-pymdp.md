# The pymdp T-maze On-Policy Student

The simulation track in [`../../src/simulation/`](../../src/simulation/) makes
the *on-policy* half of the thesis executable. Where the
[Bernoulli / Ising oracle](bernoulli-ising.md) is a static closed form, the
T-maze is a real pymdp **sophisticated-inference** agent that generates its own
observations through rollouts and is scored against a privileged target. It is
the minimal executable model of an on-policy student.

Manuscript home:
[`../../manuscript/06_methods_pymdp.md`](../../manuscript/06_methods_pymdp.md)
and [`../../manuscript/12_results_si_tmaze.md`](../../manuscript/12_results_si_tmaze.md).
Runtime contract: [`../../pymdp.yaml`](../../pymdp.yaml).

## The agent

The canonical rollout is driven by `run_si_tmaze(project_root, ...)` in
[`si_loop.py`](../../src/simulation/si_loop.py), which builds the generative
model with `build_tmaze_generative_model` from
[`tmaze_model.py`](../../src/simulation/tmaze_model.py), constructs a pymdp
`Agent`, and calls pymdp's `rollout`. The generative process has location
states/actions, two reward-location states, and three observation modalities
(`location`, `outcome`, `cue`). Each rollout step is recorded as an `SIRunResult`
carrying the per-step belief entropy, the policy posterior rows `q_π`, the
marginal first-action probabilities, selected action names, modality-specific
observations, and the SI tree metadata — the on-policy trajectory the student
writes and is then scored against.

Policy selection is in
[`si_policy.py`](../../src/simulation/si_policy.py)
(`select_policy_action`): it calls `agent.infer_policies(qs)` to get the policy
posterior `q_π` and negative expected free energy, samples an action, and records
the selected policy index and EFE. If pymdp's policy inference is unavailable it
falls back to a transparent expected-utility scorer with an explicit
`fallback_reason` — the fallback is never silent.

## Planner configuration

The planner is configured by `PymdpConfig` and its nested dataclasses in
[`pymdp_config.py`](../../src/simulation/pymdp_config.py), loaded from
[`pymdp.yaml`](../../pymdp.yaml). The canonical profile is
`full_tmaze_sophisticated_inference` and the only supported canonical planner is
`sophisticated_inference` (a legacy `mode` key, or any other profile/planner,
raises `ValueError`). Key knobs in the shipped `pymdp.yaml`:

- `planning_horizon` and the matching `si_search.horizon` (the
  beliefs-about-beliefs search depth).
- `timesteps` (rollout length).
- `agent.si_policy_len` (the SI Agent policy length) and `agent.gamma`.
- `environment.cue_validity` — the strength of the privileged channel.
- `environment.reward_condition`, `reward_probability`, `punishment_probability`.
- `si_search.max_nodes`, `max_branching`, and the pruning thresholds.

The manuscript reads SI search horizon `{{si_tmaze_planning_horizon}}`, rollout
length `{{si_tmaze_steps}}`, agent `policy_len = {{si_tmaze_policy_len}}`, cue
validity `{{si_tmaze_cue_validity}}`, and reward condition
`{{si_tmaze_reward_condition}}` — all from the config snapshot, never hard-coded.
`config_hash` (the first 16 hex of a SHA-256 over the sorted config snapshot)
stamps every artifact so runs are traceable to their exact configuration.

## The cue as a privileged-information channel

The `cue` observation modality is the privileged information `I` of the
distillation correspondence: it is the hint, verified trace, or feedback channel
available in training but not guaranteed at inference, and `cue_validity` sets how
reliable that channel is. This makes the teacher/student asymmetry operational:
the teacher has privileged sensory access, whereas the on-policy student must
*act* to sample the channel and is then evaluated on the trajectory it actually
induced. Because the cue is informative, the agent that acts to observe it drives
its posterior entropy down — the epistemic value of seeking privileged
information made quantitative. The initial `q_π` first-action marginal assigns
probability `{{si_tmaze_first_action_cue_probability}}` to the cue-directed
action: the student elects, from its own beliefs, to sample the privileged
channel first.

## Artifacts

`write_si_artifacts` and `run_and_persist` in
[`si_artifacts.py`](../../src/simulation/si_artifacts.py) write:

| Artifact (under `output/`) | Contents |
| --- | --- |
| `data/si_tmaze_summary.json` | Steps, mean belief entropy, actions, observations by modality, `q_π` rows, action probabilities, goal/reward flags, config snapshot. |
| `data/si_tmaze_trace.json` | Per-step `q_π`, first-action marginals, modality observations, belief entropy, SI tree metadata. |
| `data/si_tmaze_model_matrices.json` | Labeled `A/B/C/D` factor shapes, dependencies, normalization checks, preferences. |
| `reports/si_tmaze_run_report.json` | Config hash, seed, horizon, log record count, goal flag. |
| `data/si_policy_comparison.json` | SI alongside a **comparison-only** vanilla planner. |
| `data/pymdp_policy_posterior_grid.json` | Step-level policy-posterior normalization evidence. |
| `logs/pymdp_runs.jsonl` | Per-step JSONL run log. |

The vanilla planner is recorded only as `vanilla_role: comparison_only` and
never replaces the canonical SI summary — it exists to show the contrast between
an agent that acts on what it can learn and a myopic baseline that does not.

## Generating it

```bash
uv run python scripts/simulate_si_tmaze.py
```

This drives the rollout and writes all of the artifacts above; the figures
(`si_belief_entropy_curve.png`, `si_obs_action_trace.png`, `si_tmaze_actions.png`,
`tmaze_schematic.png`, `si_tmaze_model_matrices.png`, `policy_posterior_grid.png`,
`parallel_convergence.png`) are produced by `scripts/generate_figures.py`, and
the hydration values land in `output/data/manuscript_variables.json`.

## What it is an analogue OF — and what it is NOT

This rollout is an analogue of **on-policy data collection**: an agent that
generates the very observations it is then scored against, the active-sampling
counterpart of student rollouts in on-policy distillation. The induced-distribution
contrast against the vanilla baseline mirrors the behavioral-cloning /
exposure-bias argument that a learner must be trained on the states it actually
causes.

It is **not an OPD algorithm**. There is no teacher network, no student network
being optimized by gradient descent in this rollout, and no distillation loss
being minimized here — that executable equivalence is shown separately in the
"one scenario, two frameworks" jax demonstration
(`output/data/firstprinciples/parallel_demo.json`,
`figures/parallel_convergence.png`) and in the
[classroom](classroom.md) two-agent run. The T-maze witnesses the *on-policy
sampling structure* the correspondence relies on; the claims are limited to this
pymdp model and its artifacts, not to production LLM systems.
