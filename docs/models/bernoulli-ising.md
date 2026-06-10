# The Bernoulli / Ising Analytical Oracle

The analytical track in [`../../src/analytical/`](../../src/analytical/) is the
closed-form core of the teacher–student correspondence. It is the smallest model
in which a teacher's privileged variable and the answer a student must emit are
entangled by a single tunable coupling `λ`. Because every observable here has a
literal algebraic form, the track serves as the project's *oracle*: a source of
exact numbers that the executable simulators are checked against.

Manuscript home:
[`../../manuscript/05_methods_analytical.md`](../../manuscript/05_methods_analytical.md),
[`../../manuscript/10_results_mi_sweep.md`](../../manuscript/10_results_mi_sweep.md),
and [`../../manuscript/11_results_free_energy.md`](../../manuscript/11_results_free_energy.md).

## The two-spin coupling λ

Two binary streams `π₁, π₂` stand for the teacher and student policies. The
uncoupled baseline is the product measure `q₀(π₁,π₂) = q₁(π₁)q₂(π₂)` with both
marginals uniform `(½, ½)` — the finite mean-field variational family. The
entangled joint deforms that baseline by a symmetric Ising coupling:

```
q_λ(π₁,π₂) = Z_λ⁻¹ · q₀(π₁,π₂) · exp(λ J(π₁,π₂))
```

with `J = 1` on agreement and `0` otherwise. In code the coupling matrix is
`ising_coupling()` in
[`bernoulli_toy.py`](../../src/analytical/bernoulli_toy.py)
(the fixed `[[0.5, -0.5], [-0.5, 0.5]]` form), the uniform prior is
`symmetric_mean_field_prior()`, and the entangled joint is assembled by
`ising_joint_posterior(lam)`, which delegates to `entangled_posterior(...)` in
[`coupling.py`](../../src/analytical/coupling.py). `λ` is the dial of how
privileged the teacher is: at `λ = 0` the streams are independent (nothing to
transfer); as `λ → ∞` the teacher fully determines the student target.

## Closed-form mutual information I(λ)

With `σ(λ)` the probability the two streams agree and `H_b` the binary entropy
in nats, the teacher–student mutual information is

```
I(λ) = log 2 − H_b(σ(λ))
```

implemented directly as `ising_mutual_information(lam)`. It vanishes at `λ = 0`
(the SFT-style off-policy limit) and saturates toward `log 2` as `λ → ∞` (the
self-distillation limit). The grid maximum on the measured sweep is reported in
the manuscript as `{{ising_mi_saturation}}` nats. The complementary observable —
the conditional policy entropy `H(π₂ | π₁) = H_b(σ(λ))` — carries the exact
identity `I(λ) + H(π₂ | π₁) = log 2`.

## Free-energy gap vs the mean-field baseline

The free-energy machinery lives in
[`free_energy.py`](../../src/analytical/free_energy.py) (`free_energy`,
`marginal_free_energy`, `total_correlation`, `kl_divergence`) and the Theorem-5.1
entanglement decomposition in
[`decomposition.py`](../../src/analytical/decomposition.py)
(`entanglement_decomposition_rhs`, `free_energy_against_entangled_prior`,
`decomposition_identity_holds`).

Two cases are deliberately kept apart:

- Against its **own** normalized entangled target, the entangled posterior gives
  `F(q_λ; p_λ) = 0` to numerical tolerance — the finite self-distillation limit
  where the student family has exactly recovered the target. The residual is
  reported as `{{free_energy_exact_target_max_abs}}`.
- Against the **independent mean-field** prior `q₀`, the penalty is the
  information gap, which for this symmetric toy equals `I(λ)`. The manuscript
  reports the gap maximum `{{free_energy_mean_field_gap_max}}` nats matching MI
  to within `{{free_energy_gap_equals_mi_max_abs}}` nats, with the minimum at
  `λ = {{free_energy_argmin_lambda}}`.

The decomposition splits the exact-target zero into per-stream marginal free
energies, a coupling-cost term, a coupling-prior term, and a total-correlation
gain; for the symmetric toy the coupling-prior term equals `−I(λ)` and cancels
the `+I(λ)` total-correlation gain exactly.

## The reverse/forward KL finite-support contrast

The methods section frames the reverse-KL minimisation `F = D_KL(q ‖ p) − log p(o)`
over the student family as the per-token reverse-KL distillation loss, and the
mode-covering forward KL as the supervised-fine-tuning limit on teacher data.
The supporting figure
(`output/figures/distillation_divergence_geometry.png`) scores one fixed
teacher/student pair under five divergences (reverse KL, forward KL,
Jensen–Shannon, α-divergence, clipped reverse KL) from
`output/data/firstprinciples/divergence_demo.json`.

This contrast is **explicitly scoped as intuition, not a universal law**. The
manuscript states the concentration behaviour is "support-, parameterisation-,
and optimization-dependent rather than a universal LLM law," and the figure
caption notes it illustrates "objective geometry rather than asserting a
universal KL outcome." Treat the reverse/forward distinction here as a finite,
full-support illustration of how objective choice weights support mismatch — not
as a claim about production knowledge distillation.

## The independent recomputation discipline

The oracle's credibility rests on **two genuinely independent routes** agreeing
to machine precision:

1. The literal closed form (`ising_mutual_information`, and the analytic
   `σ`/`tanh`/`H_b` expressions in
   [`toy_sweep.py`](../../src/roadmap_tracks/toy_sweep.py)).
2. An exact recomputation that enumerates the entangled `2×2` joint and computes
   total correlation: `empirical_mutual_information(lam)` in
   [`bernoulli_toy.py`](../../src/analytical/bernoulli_toy.py).

Despite the historical name, `empirical_mutual_information` is a *deterministic
exact recomputation*, not a Monte Carlo estimate — its own docstring insists the
manuscript describe it as an "exact recomputation," never as a sampled estimate.
The agreement check is enforced by `inv_empirical_matches_closed_form` in
[`invariants.py`](../../src/analytical/invariants.py), which sweeps the `λ` grid
and requires the gap to stay under `bernoulli_verification_tolerance`. The
manuscript reports the maximum residual as `{{sweep_max_residual}}` nats —
"machine precision, not exact zero."

The `CORE_INVARIANTS` registry in `invariants.py` also pins: MI is zero at
`λ = 0`, MI saturates to `log 2` at large `λ`, the decomposition identity holds
at `λ = 1.5`, the joint is a valid PMF at `λ = 2.0`, and the joint factorizes
(is mean-field) at `λ = 0`. A perturbed sweep row fails the gate even if the
stored summary scalar is left untouched (see the residual re-derivation in
`validate_toy_sweep_artifacts`).

## Which scripts generate which artifacts

| Script | Produces (under `output/`) |
| --- | --- |
| `scripts/run_analytical_sweep.py` | `data/parameter_sweep.csv` — the `λ` sweep of closed-form vs recomputed MI. |
| `scripts/generate_toy_sweep_tracks.py` | `data/analytical_observable_sweep.json` (five observables, two routes per row, residual ≤ 1e-12), `data/analytical_assumption_index.json` (equation/assumption rows). |
| `scripts/generate_firstprinciples.py` | `data/firstprinciples/divergence_demo.json`, `data/firstprinciples/energy_demo.json`. |
| `scripts/generate_figures.py` | `figures/ising_mi_curve.png`, `figures/free_energy_curve.png`, `figures/energy_decomposition.png`, `figures/distillation_divergence_geometry.png`, `figures/gnn_ontology_concordance.png`. |
| `scripts/z_generate_manuscript_variables.py` | `data/manuscript_variables.json` — the hydration values for every token above. |

The GNN declaration `gnn/bernoulli_toy.gnn.md` and the ontology bindings in
[`05_methods_analytical.md`](../../manuscript/05_methods_analytical.md) make the
symbol map machine-checkable: the concordance diagram certifies the manuscript
symbols, the GNN spec, and the Active Inference Ontology terms all name the same
entities.

## What this model is, and is not

It **is** a faithful minimal-model demonstration that the reverse-KL distillation
objective and the variational free energy are the same algebraic object on a
finite coupled pair, with an interpretable information ceiling `I(λ)`. It **is
not** a measurement on production language models and **not** a general
communication-theoretic bound beyond this `2×2` construction. The Proposition in
the methods section scopes the claim to finite spaces, the explicitly constructed
generative model, the declared tractable family, and on-rollout evaluation.
