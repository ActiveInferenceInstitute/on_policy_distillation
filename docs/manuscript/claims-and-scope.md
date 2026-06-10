# Claims and Scope

The scope contract for the manuscript. This page states precisely what the paper
claims, what it does **not** claim, the variational/expected free-energy separation,
and how external empirical context is handled. It is derived from
[`../../manuscript/00_abstract.md`](../../manuscript/00_abstract.md),
[`../../manuscript/03_intro_contributions.md`](../../manuscript/03_intro_contributions.md),
[`../../manuscript/05_methods_analytical.md`](../../manuscript/05_methods_analytical.md),
[`../../manuscript/15_discussion_outlook.md`](../../manuscript/15_discussion_outlook.md),
and [`../../manuscript/17_conclusion.md`](../../manuscript/17_conclusion.md).

If you are about to describe a result more broadly than this page allows, the broader
statement is out of scope.

## (a) What IS claimed

A **constructive, finite correspondence** between on-policy distillation (OPD) and
active inference, *exact only under the stated assumptions* (A1–A4 below), on the
explicitly constructed toy objects:

- **Teacher ↔ generative model.** The intractable teacher policy `π_T(y | x, I)`
  plays the role of the generative model `p(o, s)`.
- **Student ↔ posterior.** The tractable student family `π_S(y | x)` plays the role of
  the approximate posterior `q(s)`.
- **Reverse-KL loss ↔ VFE (up to the evidence constant).** The per-token reverse-KL
  distillation loss equals the variational free energy
  `F = D_KL(q ‖ p) − log p(o)`, an algebraic identity of the declared objects. The
  `−log p(o)` evidence term is invariant to the student parameters.
- **On-policy rollouts ↔ active sampling.** On-policy student rollouts are the active
  sampling by which the posterior generates the observations it is then scored on.

It is substantiated three ways, kept distinct (see the Proposition): **proved in
closed form**, **proved and verified two-route** (independent recomputation to machine
precision), and **demonstrated numerically** (gradient descent on the reverse-KL
objective and on VFE drive the same student to the same posterior). A fourth leg —
reading rollouts as active sampling and differential cue reliability as privileged
information — is explicitly labeled **interpretive**, a correspondence built on the
first three, not an additional theorem.

The other genuine contribution is a **discipline**: a sheaf-indexed compose contract
binds fragment tracks into flat IMRAD sections, every reported number is hydrated from
a generated artifact, every cross-track claim is machine-checked before render, and the
gates fail closed so no figure or statistic can drift from its producing artifact.

## (b) What is NOT claimed

The manuscript states these non-claims repeatedly and explicitly:

- **No universal theorem about OPD or active inference.** Outside A1–A4 — sequence
  models, learned families, production-scale distillation — the correspondence is a
  *structured analogy / family resemblance*, not a proof.
- **No production-LLM measurements.** All quantitative findings are from the analytical
  toy, the T-maze rollout, the dynamic simulators, and the classroom artifact. The toy
  results *demonstrate the correspondence*; they assert nothing about production LLMs.
- **No biological / Markov-blanket metaphysics.** The Markov-blanket and predictive-coding
  readings are used only as a constrained probabilistic interpretation
  (conditional-independence screening; top-down target plus bottom-up residual). No
  physical, cortical, or biological boundary claim is made; the contested status of
  blanket-based inferential readings is acknowledged.
- **No gridworld benchmark.** The graph-world artifacts are finite topology stress tests
  and Lean/model-checking witnesses. "No gridworld result is reported or claimed."
- **No universal reverse-vs-forward-KL law.** The reverse/forward-KL contrast on the
  finite support is a "divergence-direction intuition," not a universal statement that
  one direction always yields one LLM behavior; the alpha/f-divergence and KL-geometry
  literature is cited as the guardrail.
- **Lean proves only finite boundaries.** It does not prove a general theorem about
  pymdp's `q_π` posterior, production language models, or all SI planners.
- **The small-sample statistics are not significance.** The teacher/student entropy-gap
  confidence interval includes zero and the permutation test cannot reject the null;
  reported as honest machinery and the *sign* of the effect, not confirmatory evidence.

## (c) The VFE vs EFE separation

The manuscript keeps two active-inference objectives apart, and this distinction is
load-bearing:

- **Variational free energy (VFE)** is the distillation loss on **realized rollouts**.
  `F = complexity − accuracy = D_KL[q(s) ‖ p(s)] − E_q[ln p(o|s)]`, equivalently the
  negative log-evidence offset by the posterior gap. This is the static distillation
  objective; minimizing `F` tightens the reverse KL between student and privileged
  teacher up to the evidence constant `−ln p(o)`.
- **Expected free energy (EFE)** is the **planning-side analogue only**. It extends the
  ledger forward over the student's own future rollouts and is how the pymdp agent
  *selects actions*. EFE splits two equivalent ways:
  `G = risk + ambiguity = −(epistemic + pragmatic)`. The pragmatic term is the
  active-inference image of reward-tilting; the epistemic term is the active-sampling
  pressure.

The Proposition's clause (iv) makes the separation formal: "planning/action in the
pymdp witness is selected by *expected* free energy rather than by the realized-rollout
objective in (i)." The distillation-loss = VFE identity is the claim; EFE is the
planning analogue, not the loss.

## (d) External context handling

The OPD-vs-RL empirical numbers (AIME-24 accuracy, GPU-hours, replication steps,
efficiency factors) are **literature-reported, not reproduced**. They come from the
Qwen3 technical report (`@qwen2025technical_report`) as relayed and discussed by
Thinking Machines (`@thinkingmachines2025opd`). The manuscript states: "We did **not**
measure any of the following ourselves … reproduced here only as external context."
The Thinking Machines source is a non-archival blog/Connectionism post and is treated
as such; the bibliography's source-kind classification keeps the preprint/archival
distinction machine-readable
(`output/data/scholarship_source_matrix.json`). See
[`citation-map.md`](citation-map.md) → *External empirical context*.

## The Proposition, verbatim

Quoted exactly from
[`../../manuscript/05_methods_analytical.md`](../../manuscript/05_methods_analytical.md)
(the assumptions A1–A4 and the four-part conclusion). Token placeholders appear as in
source; their resolved values come through hydration (see
[`hydration-tokens.md`](hydration-tokens.md)).

> **Proposition (scoped correspondence).** *Assume* (A1) finite state, observation, and
> policy spaces as declared in the state-space catalog; (A2) the generative model is the
> explicitly constructed object — the entangled joint $q_\lambda$ here, or the pymdp
> T-maze generative model in [@sec:methods_pymdp]; (A3) the student/posterior family is
> the declared tractable family (the mean-field product family here; the categorical
> pymdp posterior there); (A4) the student is evaluated on its own realized rollouts.
> *Then*: (i) **proved in closed form** — the per-decision reverse-KL distillation loss
> equals the variational free energy up to the evidence constant,
> $F = D_{\mathrm{KL}}(q\,\Vert\,p) - \log p(o)$, an algebraic identity of the declared
> objects; (ii) **proved in closed form, verified two-route** — the information
> identities [@eq:mutual_information] and [@eq:conditional_entropy], with both derivation
> routes agreeing to {{observable_sweep_max_residual:.1e}} nats; (iii) **demonstrated
> numerically** — gradient descent on the reverse-KL objective and on the variational
> free energy drive the same student to the same posterior (maximum absolute
> disagreement {{parallel_max_abs_difference:.1e}}, [@sec:results_free_energy]);
> (iv) **interpretive** — reading on-policy rollouts as active sampling, and differential
> cue reliability as privileged information, is a correspondence built on (i)–(iii), not
> an additional theorem, and planning/action in the pymdp witness is selected by
> *expected* free energy rather than by the realized-rollout objective in (i). Outside
> (A1)–(A4) — sequence models, learned families, production-scale distillation — the
> correspondence is a structured analogy whose limits [@sec:discussion_outlook] states
> explicitly.
