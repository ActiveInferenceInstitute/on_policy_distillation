# Glossary

Project-specific definitions. Each entry is grounded in how *this* manuscript
uses the term — the scoped correspondence between on-policy distillation (OPD)
and active inference demonstrated on finite, executable toy models. For the
formal notation, see
[`reference/notation-supplement.md`](reference/notation-supplement.md).

### Variational free energy (VFE)

The distillation objective in this project. The per-token reverse-KL
distillation loss is the variational free energy
$F = D_{\mathrm{KL}}(q\,\|\,p) - \log p(o)$, where the teacher policy is the
generative model $p(o,s)$ and the student policy is the approximate posterior
$q(s)$. It is evaluated on the student's own rollouts — the posterior is scored
on the observations it caused.

### Expected free energy (EFE)

The planning/action-selection objective, kept distinct from VFE throughout. The
pymdp T-maze agent chooses its actions by minimizing expected free energy; the
distillation *loss*, by contrast, is variational free energy on realized
rollouts. The manuscript deliberately keeps the two objectives apart.

### Sophisticated inference (SI)

The canonical pymdp planner used for the T-maze rollout (config token
`{{pymdp_planner}}`, SI search horizon `{{si_tmaze_planning_horizon}}`). The SI
agent generates its own observations and acts to minimize expected free energy
under a privileged cue. Vanilla planner rows exist only as validation-comparison
evidence, not as the canonical rollout.

### Privileged information / LUPI

Information available to the teacher (during training) but not to the student at
inference — the channel by which a teacher informs the student. In the toy
models this is a cue observation; the lineage is Learning Using Privileged
Information (LUPI) and the distillation literature, where train-time-only signal
plays the same role.

### On-policy distillation (OPD)

Distillation in which the student is trained on its *own* generated rollouts (the
on-policy condition) rather than a fixed teacher-data distribution. In the active
inference reading, this is "a variational posterior generating its own
observations under a generative model conditioned on privileged beliefs."

### Reverse / forward KL

The two divergence directions that organize the design space. The reverse-KL
side concentrates on teacher-supported mass (mode-seeking); the forward-KL side
covers teacher-data mass (mass-covering); skew, entropy-aware, contrastive, and
hybrid objectives occupy intermediate points. In this project the reverse/forward
KL contrast is a finite-support divergence-direction intuition, **not** a
universal law about LLM training. The distillation loss studied here is the
reverse-KL form.

### Sheaf track

A fragment type in the manuscript composition system. Authored fragments are
indexed by track (prose, formalism, simulation, pymdp, ontology, Lean,
visualization, provenance, etc.) and composed into flat IMRAD sections. The
registry of tracks lives in `manuscript/sheaf/tracks.yaml`; this project binds
`{{sheaf_track_count}}` fragment tracks into `{{composed_section_count}}`
sections.

### Compose contract

The sheaf-indexed discipline binding fragments into sections before rendering.
The claim is finite and falsifiable: registry tracks must be typed by renderer,
manifest bindings must resolve to existing fragments, coverage must have zero
gray cells on a clean tree, and `{{sheaf_law_count}}` sheaf axioms are verified
before composition. It is the methodological contribution — a discipline, not a
domain finding.

### Hydration token

A `{{token}}` placeholder substituted with a generated value at the single
hydration boundary (`scripts/z_generate_manuscript_variables.py`). Every reported
number is hydrated from a generated artifact so no figure or statistic can drift
from the artifact that produced it. Unknown tokens and single-brace typos fail
closed.

### Negative control / counterexample

A test that proves a verifier-like gate actually bites by exhibiting a case the
gate must reject. The project keeps `{{counterexample_count}}` negative controls
live so each failure path stays exercised; every promoted artifact must carry one.

### Invariant check

An analytical or simulation consistency check merged across tracks
(`{{invariants_passed}}` / `{{invariants_total}}` pass). Examples: closed-form
and independently recomputed mutual-information sweeps must agree to machine
precision (RMSE `{{sweep_rmse_mi:.1e}}` nats).

### Evidence constant

The $-\log p(o)$ term in $F = D_{\mathrm{KL}}(q\,\|\,p) - \log p(o)$. The
conclusion states the reverse-KL distillation loss is variational free energy
*up to the evidence constant* — the correspondence holds modulo this term.

### Mean-field baseline

The student that cannot condition on the teacher's privileged variable. Its
mean-field free-energy gap (relative to the entangled posterior) is the cost paid
for lacking privileged information — in the Bernoulli-Ising oracle, that gap is
the distillation objective.

### Cue validity

The reliability of the privileged cue an agent observes, a tunable knob in
`pymdp.yaml`. The classroom run contrasts a privileged teacher (cue validity
`{{classroom_teacher_cue_validity}}`) against an on-policy student (cue validity
`{{classroom_student_cue_validity}}`).

### Epistemic / pragmatic value

The two components of expected free energy. Epistemic value drives
information-seeking (cue disambiguation in the T-maze); pragmatic value drives
goal-reaching. In the discussion, RL's sparse end-of-rollout scalar is framed as
an impoverished *pragmatic* signal versus OPD's dense per-token target.

### Markov blanket (scoped-reading caveat)

A conditional-independence boundary separating internal from external states.
This project uses the Markov-blanket reading **only as a constrained
probabilistic interpretation of the toy models** — blanket-based inferential
readings are technically delicate and not uncontested, so no biological or
cortical claim is made.

### Exposure bias

The train/inference mismatch in which a model conditioned on its own generations
drifts from the teacher-data distribution it was trained on. Here it is a
*motivational* framing, not a universal diagnosis: its empirical severity is
task-dependent and autoregressive models can self-recover.

## See also

- [`faq.md`](faq.md) — honest answers about scope and claims.
- [`reference/notation-supplement.md`](reference/notation-supplement.md) — formal symbols.
- [`reference/method-inventory.md`](reference/method-inventory.md) — generated code coverage.
