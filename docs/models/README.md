# The Executable Model Zoo

This directory documents the concrete, runnable models that carry the thesis of
the project — *on-policy distillation is a scoped instance of active inference* —
from prose into measured artifacts. Each model is small and finite by design.
The point is not scale; it is that every claim is either a closed-form identity
or a deterministic rollout whose numbers can be regenerated and re-derived along
an independent route.

Read these pages as a map from "what the manuscript asserts" to "which module
witnesses it, and what it deliberately does *not* claim." None of the models
here is a production language model, a benchmark, or a statistical study. They
are minimal-model demonstrations of a correspondence.

## The zoo

| Model | Module(s) | Witnesses | Scope note |
| --- | --- | --- | --- |
| [Bernoulli / Ising](bernoulli-ising.md) | `src/analytical/` | The closed-form oracle: mutual information `I(λ)`, the free-energy gap against the mean-field baseline, the two-route recomputation discipline. | An algebraic identity on a 2×2 joint, not a universal KD law. |
| [pymdp T-maze](tmaze-pymdp.md) | `src/simulation/` | The on-policy student: a sophisticated-inference agent that generates its own observations and seeks a privileged cue. | An analogue of on-policy data collection, *not* an OPD algorithm. |
| [Classroom](classroom.md) | `src/firstprinciples/classroom.py` | Two agents (privileged teacher, on-policy student); belief-entropy advantage and the mean reverse-KL distillation signal. | Posterior-sharpness gap on a short rollout, not task success or a general law. |
| [Privilege sweep](privilege-sweep.md) | `src/roadmap_tracks/toy_sweep.py`, `src/firstprinciples/privilege.py` | The dose-response of the distillation signal to teacher privilege, with an identical-agent control. | A deterministic toy sweep, not inferential statistics. |
| [Graph-world](graph-world.md) | `scripts/simulate_si_graph_world.py`, `src/simulation/graph_world.py` | Topology stress tests for the on-policy reading. | Not a gridworld benchmark. |

## How the models relate

The Bernoulli / Ising toy is the **analytical core**: it gives a closed-form
ceiling `I(λ)` and proves the per-decision reverse-KL distillation loss equals
the variational free energy up to the evidence constant. The pymdp T-maze makes
the *on-policy* half executable — an agent acting to sample a privileged channel.
The classroom puts two T-maze agents side by side to read the single-agent
rollout as a teacher/student pair. The privilege sweep turns that single
comparison into a dose-response curve with a built-in wiring check. The
graph-world models vary the topology to confirm the on-policy story is not an
artifact of one fixed maze.

## Where the numbers live

Every quantity in the manuscript is a hydration token (e.g.
`{{classroom_mean_reverse_kl_formatted}}`) resolved from
`output/data/manuscript_variables.json` at render time. These pages never
hard-code values; they point at the producing artifact path instead. See
[`../reference/rendering-reproducibility.md`](../reference/rendering-reproducibility.md)
for the single hydration boundary and the producer order.

## Related references

- [`../reference/method-inventory.md`](../reference/method-inventory.md) — generated coverage for every `def`/`class`.
- [`../reference/notation-supplement.md`](../reference/notation-supplement.md) — the shared notation dictionary.
- [`../reference/configuration-and-extension.md`](../reference/configuration-and-extension.md) — knob→consumer map and add-a-model recipes.
