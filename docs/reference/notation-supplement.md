# Notation & Formalism Supplement

**A Finite-Model Active-Inference Reading of On-Policy Distillation.**

This supplement gives the integrated notation and the formal identities behind
that scoped title. It is the human-readable companion to the executable
[`firstprinciples`](../../src/firstprinciples/) package: every definition here
has a tested implementation, and every implementation cites a definition here.
All divergences are in **nats**.

---

## 1. One objective, three names

Maximum-entropy / KL-regularised reinforcement learning maximises

$$
J(\pi) \;=\; \mathbb{E}_{y\sim\pi}\!\big[R(y)\big] \;-\; \beta\, D_{\mathrm{KL}}\!\big(\pi \,\|\, \pi_{\mathrm{ref}}\big).
$$

Its unique maximiser is the **reward-tilted (Gibbs) target**

$$
\pi^{*}(y) \;=\; \frac{1}{Z}\,\pi_{\mathrm{ref}}(y)\,\exp\!\Big(\tfrac{R(y)}{\beta}\Big),
\qquad Z=\sum_{y}\pi_{\mathrm{ref}}(y)\,\exp\!\big(R(y)/\beta\big).
$$

Up to the additive constant $\log Z$, maximising $J$ is identical to minimising
the **variational free energy** of $\pi$ against $\pi^{*}$,

$$
F(\pi) \;=\; D_{\mathrm{KL}}\!\big(\pi \,\|\, \pi^{*}\big) \;=\; \frac{\log Z - J(\pi)}{\beta}.
$$

When the target is a *teacher policy* $\pi_T$ rather than a reward-tilted prior,
$F$ becomes the **reverse-KL distillation loss** $D_{\mathrm{KL}}(\pi_S \| \pi_T)$.
The same quadratic-free functional is therefore the active-inference free energy,
the KL-regularised RL objective, and the on-policy distillation loss inside the
declared finite objects. This is the scoped content of the title, and it is checked numerically in
`firstprinciples.reward_tilting.free_energy_against_tilted` (zero at the target)
and `verify_optimality` (the target beats all perturbations).

References: @levine2018rlinference, @abdolmaleki2018mpo,
@todorov2008duality, @toussaint2009trajectory_inference, @ziebart2008maxent_irl,
@millidge2020active_control, @haarnoja2018sac, @ziegler2019humanprefs,
@rafailov2023dpo, @friston2006fep, @friston2010fep, @parr2022active.

---

## 2. Notation dictionary

| Symbol | Active inference | On-policy distillation |
| --- | --- | --- |
| $p(o,s)$ | generative model | teacher policy $\pi_T(y\mid x, I)$ |
| $q(s)$ | approximate posterior | student policy $\pi_S(y\mid x)$ |
| $o$ | observations | generated tokens / trajectory $y$ |
| $s$ | hidden states | latent reasoning / hidden context |
| $I$ | privileged sensory access | privileged information (hint, verified trace, feedback) |
| $F$ | variational free energy | reverse-KL distillation loss |
| $G$ | expected free energy | distillation + reward (KL+RL) objective |
| $\gamma$ | precision / inverse temperature | distillation temperature $1/\beta$ |
| Markov blanket | conditional-independence boundary | teacher/student context asymmetry |
| predictive-coding hierarchy | top-down prediction / bottom-up error | teacher target / student residual correction |
| control-as-inference posterior | reward-tilted policy posterior | KL-constrained RLHF / OPD target |
| epistemic value | information gain | teacher signal on novel student states |
| pragmatic value | prior preference $\log p(o)$ | reward tilt $\exp(R/\beta)$ |

The machine-readable version of this dictionary is
`firstprinciples.mapping.CORRESPONDENCES` (audited: no empty fields, unique keys).

---

## 3. Divergence geometry

For categorical $p,q$ on the same support, with $D_{\mathrm{KL}}(q\|p)=\sum_i q_i\log\frac{q_i}{p_i}$, the primitive is the Kullback-Leibler information divergence [@kullback1951information], and the use of a tractable $q$ follows the variational-inference tradition [@jordan1999variational; @blei2017variational]:

| Name | Definition | Behaviour | OPD role | Module |
| --- | --- | --- | --- | --- |
| Forward KL | $D_{\mathrm{KL}}(p_T\|q_S)$ | mode-covering | SFT / vanilla KD limit (@hinton2015distilling) | `divergences.forward_kl` |
| Reverse KL | $D_{\mathrm{KL}}(q_S\|p_T)$ | mode-seeking | self-distillation / free energy (@gu2024minillm) | `divergences.reverse_kl` |
| Jensen–Shannon | $\tfrac12 D_{\mathrm{KL}}(p\|m)+\tfrac12 D_{\mathrm{KL}}(q\|m)$, $m=\tfrac{p+q}{2}$ | symmetric, bounded | DistiLLM family (@ko2024distillm) | `divergences.jensen_shannon` |
| Skew KL | $D_{\mathrm{KL}}\!\big(p\,\|\,(1-\alpha)p+\alpha q\big)$ | finite under zeros | stabilised KD / DistiLLM (@ko2024distillm) | `divergences.skew_kl` |
| $\alpha$-divergence | $\tfrac{1-\sum_i p_i^{\alpha}q_i^{1-\alpha}}{\alpha(1-\alpha)}$ | interpolates FKL/RKL | adaptive, entropy-aware, and hybrid objectives (@jin2026entropy_opd; @zhu2026hpd) | `divergences.alpha_divergence` |
| Clipped pointwise KL | $\sum_i \mathrm{clip}\!\big(q_i(\log q_i-\log p_i),\,\pm c\big)$ | bounds per-token mass | OPSD (@zhao2026opsd) | `divergences.clipped_pointwise_kl` |

**Why reverse KL is the default.** It is mode-seeking, it is exactly zero iff
$q_S=p_T$, and it is "unhackable": the student cannot lower it by spreading mass
into low-quality teacher regions. These are precisely the properties active
inference derives for free-energy minimisation. The 2026 loss-family shares
(@awesomeopd2026) are KL+RL 23%, reverse-KL 23%, forward-KL 21%, symmetric/JSD
13%, advantage-weighted 16%, preference/$f$-divergence 4%
(`firstprinciples.taxonomy.LOSS_SHARES`).

---

## 4. The reward-tilted target

Stationarity of $J(\pi)-\lambda(\sum_y\pi(y)-1)$ gives
$R(y)-\beta(\log\pi(y)-\log\pi_{\mathrm{ref}}(y)+1)-\lambda=0$, i.e.
$\pi(y)\propto\pi_{\mathrm{ref}}(y)\exp(R(y)/\beta)$ — the Gibbs target above.
Active inference recovers the same expression with $R=\log p(o)$ (prior
preference) and $\beta=1/\gamma$. Implemented (numerically stable, log-domain) in
`firstprinciples.reward_tilting.reward_tilted_target`.

---

## 5. SDPG: a single model conditioned on privileged beliefs

Self-Distilled Policy Gradient (@liu2026sdpg; code @lauyikfung2026sdpgcode)
makes one network its own teacher and student through context asymmetry:

$$
\mathcal{L}
\;=\; \underbrace{\mathcal{L}_{\mathrm{clip}}}_{\text{clipped PG}}
\;+\; \beta\, D_{\mathrm{KL}}\!\big(\pi_\theta(\cdot\mid x)\,\big\|\,\pi_\theta(\cdot\mid c, x)\big)
\;+\; \alpha\, D_{\mathrm{KL}}\!\big(\pi_\theta(\cdot\mid x)\,\big\|\,\pi_{\mathrm{ref}}(\cdot\mid x)\big).
$$

The middle term is the title made literal: the **generative model is the same
policy conditioned on privileged context $c$**, and the student (no context)
descends the reverse KL toward it. Crucially this signal is *dense* — a gradient
component at every vocabulary entry where teacher and student disagree — whereas
a scalar reward supplies exactly one. That density (quantified in
`firstprinciples.sdpg.signal_density`) is the mechanism-level reason the
literature-reported Qwen table can show OPD above RL at lower compute
(@qwen2025technical_report: 74.4% vs 67.6% AIME'24, 1,800 vs 17,920 GPU-hours,
as relayed by @thinkingmachines2025opd). Thinking Machines' own contextual
replication is separate: about 70% AIME'24 in roughly 150 steps, framed as a
9-30x efficiency range. Default hyperparameters mirror the reference implementation
($\beta=\alpha=10^{-3}$; `KL_MODE` $\in\{$fkl, rkl, ufkl, urkl$\}$).

---

## 6. Exposure bias = the failure of passive updating

Train a student only on teacher/ground-truth trajectories (off-policy) and it
never visits the off-distribution states its own sampling produces; errors
compound and it cannot recover. This is the behavioral-cloning/imitation-learning
failure mode before it is the LLM exposure-bias failure mode
(@pomerleau1989alvinn; @ross2010efficient_imitation; @ross2011dagger;
@bengio2015scheduled; @arora2022exposure; @pozzi2025exposure_distill), and it
also marks the limit of model compression, sequence KD, and policy distillation
when the student is never trained on states it induces
(@bucila2006model_compression; @hinton2015distilling; @kim2016sequence_kd;
@rusu2016policy_distillation; @czarnecki2019distilling_policy). Active inference makes the same
diagnosis for passive Bayesian updating. Modelling on-track/off-track as a two-state chain
(`firstprinciples.exposure_bias`), the off-policy survival probability decays
geometrically toward zero while the on-policy student — which *generates its own
observations* and learns to recover — converges to a positive plateau
$r/(1-a+r)$. This is the finite operational reading of "the variational posterior
generates its own observations."

---

## 7. The two-agent classroom (executable)

`firstprinciples.classroom` runs two pymdp sophisticated-inference agents on the
canonical T-maze. The **teacher** sees a near-perfect cue (`cue_validity` $\approx
0.98$): privileged information that all but reveals the latent reward location,
so its policy posterior $q(\pi)$ commits confidently. The **student** sees an
uninformative cue (`cue_validity` $\approx 0.5$) and must infer on-policy. The
per-decision **reverse KL** between the student's and teacher's action
distributions is the variational free energy the student descends to absorb the
teacher's privileged belief. Measured: teacher belief entropy $0.247$ nats $<$
student $0.347$ nats (privileged advantage), mean distillation signal $6.28$
nats. The cue is the Markov blanket (@kirchhoff2018markov); the rollout is the
posterior generating its own observations; the reverse KL is the loss — the
title, instantiated and measured. The teacher/student entropy gap is a local toy
measurement, not a reproduction of entropy-aware OPD results (@jin2026entropy_opd).

---

## 8. Dynamic distillation simulators (executable)

Five further modules make the *dynamics* of distillation measurable, not just the
static objects above.

**8.1 On-policy GKD vs off-policy (`firstprinciples.gkd`).** The GKD objective is
the per-token divergence averaged under a *visitation distribution* over
token-states. Off-policy/SFT averages under the teacher's visitation $d_T$;
on-policy/GKD averages under the student's visitation $d_S$:

$$
\mathcal{L}_{\mathrm{GKD}}^{\mathrm{on}} = \sum_{s} d_S(s)\, D_{\mathrm{KL}}\!\big(\pi_S(\cdot\mid s)\,\|\,\pi_T(\cdot\mid s)\big),
\qquad
\mathcal{L}^{\mathrm{off}} = \sum_{s} d_T(s)\, D_{\mathrm{KL}}\!\big(\pi_S(\cdot\mid s)\,\|\,\pi_T(\cdot\mid s)\big).
$$

A student that drifts on the states *it* prefers has $\mathcal{L}^{\mathrm{on}} \ge
\mathcal{L}^{\mathrm{off}}$ — the measurable signature of exposure bias that GKD
corrects by putting loss mass exactly where the posterior generates its own
observations.

**8.2 Variational EM / $\pi$-Distill (`firstprinciples.variational_em`).** The
MPO/EM cycle alternates an E-step (improve a non-parametric target by the
advantage relative to $\pi_{\mathrm{ref}}$, $A = R - \beta\log(\pi_S/\pi_{\mathrm{ref}})$,
so the target is the reward-tilted $\pi^{*}$ for *any* current student) and an
M-step (reverse-KL projection of $\pi_S$ onto it). The variational free energy
$D_{\mathrm{KL}}(\pi_S\|\pi^{*})$ decreases monotonically to zero — an executable,
audited certificate of the perception/action loop.

**8.3 Diversity collapse, Pass@1 vs Pass@k (`firstprinciples.diversity`).** With a
temperature-sharpened student $\pi_\tau \propto \pi_T^{1/\tau}$ and correct mass
$c(\tau)$, sampling Pass@k $= 1-(1-c)^k$ is **concave** in $c$. Sharpening pushes
each problem's $c$ toward $0$ or $1$; by Jensen this *lowers* aggregate Pass@k
across a problem ensemble even as it raises greedy Pass@1 — the documented
mode-seeking diversity tradeoff, reproduced as an ensemble effect.

**8.4 Adaptive divergence (`firstprinciples.adaptive`).** Per token, choose the
direction from the student's local uncertainty: reverse KL where confident
(entropy below the batch median — commit), forward KL where uncertain (explore).
This is precision-weighting of the epistemic/pragmatic balance applied
token-wise; the adaptive objective lies between the all-forward and all-reverse
extremes (AKL/ToDi family), and is the toy analogue of entropy-aware and hybrid
OPD design choices (@jin2026entropy_opd; @zhu2026hpd).

**8.5 Sequential shift (`firstprinciples.sequential_shift`).** A four-state,
two-action finite witness compares teacher-forced train visitation with the
student-induced test visitation before and after a deterministic on-policy
correction. The artifact records normalized visitations, teacher/student
policies, per-state reverse KL, train loss, induced test loss, shift mass, and
gap closed. It is a distribution-shift accounting check, not an empirical OPD
benchmark.

---

## 9. Energy-based formulation: VFE and EFE (`firstprinciples.energy`)

Active inference is an energy-based model; on-policy distillation reads off both
free-energy functionals on a categorical generative model
$p(s)\,p(o\mid s)$ with preferences $p(o)$.

**Variational free energy** of the student $q(s)$ given observation $o$ has three
algebraically equal forms (verified to machine precision):

$$
F[q] = \underbrace{\mathbb{E}_q[-\ln p(o,s)]}_{\text{energy}} - \underbrace{H[q]}_{\text{entropy}}
     = \underbrace{D_{\mathrm{KL}}(q(s)\,\|\,p(s))}_{\text{complexity}} - \underbrace{\mathbb{E}_q[\ln p(o\mid s)]}_{\text{accuracy}}
     = \underbrace{D_{\mathrm{KL}}(q(s)\,\|\,p(s\mid o))}_{\text{divergence}} - \underbrace{\ln p(o)}_{\text{log-evidence}}.
$$

The third (divergence − log-evidence) form is the OPD identity: with $q=\pi_S$
(student) and the exact privileged posterior $p(s\mid o)=\pi_T$ (teacher), the
reverse-KL distillation loss $D_{\mathrm{KL}}(\pi_S\|\pi_T)$ **is** the variational
free energy up to the data-fixed constant $-\ln p(o)$. Minimising the distillation
loss therefore maximises model evidence; the exact posterior attains
$F=-\ln p(o)$ (the global minimum), which `energy.build_payload` certifies.

**Expected free energy** of a policy has two equal forms:

$$
G = \underbrace{D_{\mathrm{KL}}(q(o)\,\|\,p(o))}_{\text{risk}} + \underbrace{\mathbb{E}_{q(s)}[H[p(o\mid s)]]}_{\text{ambiguity}}
  = -\underbrace{I(o;s)}_{\text{epistemic}} - \underbrace{\mathbb{E}_{q(o)}[\ln p(o)]}_{\text{pragmatic}}.
$$

Risk is the reward-tilt / KL+RL term (pragmatic value); the epistemic term is the
state–observation mutual information that on-policy rollouts harvest from the
novel states the student visits. `energy.efe_report` verifies the two forms agree.

---

## 10. Statistics and Science protocol (`firstprinciples.statistics`, `.privilege`)

Sample-level claims are reported with a percentile **bootstrap** mean CI, a paired
**permutation** test and exact **sign** test, and **Cohen's $d$** effect size — all
seeded and deterministic [@cohen1988power]. The privileged-teacher advantage
(student belief entropy exceeds teacher belief entropy) is confirmed with a
strictly positive bootstrap CI on the paired difference, $n=6$ matched classroom
pairs, a two-sided paired permutation test with 5,000 seeded permutations, and
$d>0$. These are toy-classroom inferential summaries, not population claims about
production LLM distillation.

**Privilege-sweep experiment** (`firstprinciples.privilege`, a *Science* cycle):
*Hypotheses* — (H1) teacher belief entropy falls and (H2) the reverse-KL
distillation signal grows as the teacher cue becomes more privileged.
*Method* — sweep teacher `cue_validity` over a grid (student fixed,
uninformative) and run the real pymdp sophisticated-inference classroom at each
level. *Measure* — Spearman rank correlation of `cue_validity` against teacher
belief entropy (expect $\le 0$) and against the distillation signal (expect
$\ge 0$). The sweep is deterministic per seed.

---

## 11. How the manuscript's toy experiments map onto the thesis

| Experiment (this repo) | Reading under the correspondence |
| --- | --- |
| Bernoulli–Ising coupling $\lambda$, $I(\lambda)$ | teacher↔student coupling; mutual information transferable by distillation |
| Free energy of entangled posterior vs mean-field prior | the distillation objective landscape |
| pymdp T-maze sophisticated-inference rollout | the on-policy student generating its own observations |
| Privileged-teacher vs student classroom | the privileged generative model and the distillation gap |
| Sheaf composition + validation gates | the gate-checked, drift-free manuscript itself |

All numbers in the manuscript are hydrated from generated artifacts and
machine-checked before rendering, so the correspondence is demonstrated on
auditable minimal models — not asserted about production language models.
