```{=latex}
\phantomsection
\addcontentsline{toc}{section}{Methods}
\section*{Methods}
```

# Teacher and student coupling: the analytical model {#sec:methods_analytical}

<!-- sheaf-track:prose -->

We instantiate a minimal **K={{bernoulli_state_count}} Bernoulli / Ising** coupling as the analytical core of the teacher-student correspondence: it is the smallest model in which the privileged variable a teacher conditions on and the answer a student must emit are entangled by a single tunable coupling. The entangled joint [@eq:entangled_joint] places the teacher's privileged variable and the answer in one distribution governed by the coupling, exactly as a privileged teacher policy $\pi_T(y\,|\,x,I)$ binds the hint $I$ to its output while the student family $\pi_S(y\,|\,x)$ sees only $x$. This is the finite probabilistic analogue of learning using privileged information [@vapnik2009lupi] and of the distillation/privileged-information bridge [@lopezpaz2016unifying], with the Markov-blanket asymmetry made explicit rather than left as an informal teacher/student story.

The closed-form mutual information $I(\lambda)$ is therefore the teacher-student mutual information — the bits the privileged channel injects that a factorised, mean-field student cannot recover — and the coupling $\lambda$ is the dial that sets how privileged the teacher actually is. The free energy of fitting an approximate posterior to this joint is the distillation objective in the active-inference sense [@friston2010fep; @parr2019generalised; @parr2022active]: minimising $F = D_{\mathrm{KL}}(q\,\|\,p) - \log p(o)$ over the student family is the per-token reverse-KL distillation loss, mode-seeking and collapsing toward the self-distillation limit [@gu2024minillm; @agarwal2024gkd], whereas the mode-covering forward KL recovers the supervised-fine-tuning limit on teacher-generated data [@hinton2015distilling]. The same coupling thus interpolates the divergence families catalogued across the on-policy distillation landscape [@awesomeopd2026; @song2026opdsurvey], and the entangled-versus-factorised gap in $I(\lambda)$ is the information a model leaves on the table when it distils toward itself conditioned on privileged context rather than the unconditioned family [@zhao2026opsd; @liu2026sdpg]. The free-energy terminology is scoped to these finite variational calculations in the sense of mathematical reviews of the free-energy principle [@buckley2017mathreview], and we read this Bernoulli-Ising oracle strictly as a minimal-model demonstration of the correspondence — not a claim about production language models — supplying the exact $I(\lambda)$ against which an independent recomputation (via total correlation) and the GNN round-trips in [@sec:results_mi_sweep] ([@fig:gnn_ontology_concordance]) are checked.

Measured sweep grid points: {{param_sweep_grid_points}}. Invariants passed: {{invariants_passed}} / {{invariants_total}}.

<!-- sheaf-track:formalism -->

In the distillation reading, the two binary streams $\pi_1,\pi_2$ are the teacher and student policies, and the coupling $\lambda$ measures how strongly the teacher's privileged variable is tied to the answer the student must reproduce. The entangled joint over the pair satisfies

$$
q_\lambda(\pi) \propto E(\pi)\,\exp(\lambda J(\pi)),
$$ {#eq:entangled_joint}

with symmetric Ising coupling $J$ and deformation parameter $\lambda$. Reading $q_\lambda$ as the generative model $p(o,s)$ that a tractable student must approximate, $\lambda$ controls exactly the teacher--student dependence that on-policy distillation exists to transfer: at $\lambda=0$ the student gains nothing from the teacher, while at large $\lambda$ the teacher's privileged information $I$ is fully informative about the target. This is the minimal model of the coupling that reverse-KL distillation objectives [@gu2024minillm; @agarwal2024gkd] and their self-distillation descendants [@zhao2026opsd; @liu2026sdpg] are built to exploit. Let $\sigma(\lambda)=q_\lambda(\pi_1=\pi_2)$ be the probability that the two streams agree (the diagonal mass of the $2\times2$ joint) — equivalently, the probability that an on-policy student rollout matches the privileged teacher; by symmetry both marginals are uniform. With binary entropy $H_b(p)=-p\log p-(1-p)\log(1-p)$ in nats, the joint entropy is $H(q_\lambda)=\log 2 + H_b(\sigma(\lambda))$ while each marginal contributes $\log 2$, so the teacher--student mutual information is

$$
I(\lambda)=\sum_k H(q_k)-H(q_\lambda)=\log 2 - H_b(\sigma(\lambda)),
$$ {#eq:mutual_information}

[@eq:mutual_information] vanishes at $\lambda=0$ ($\sigma=\tfrac12$, independent streams — the teacher conveys no privileged signal, the SFT-style off-policy limit [@hinton2015distilling]) and saturates at $\log 2$ as $\lambda\to\infty$ ($\sigma\to1$, perfectly entangled — the teacher fully determines the student target, the self-distillation limit). $I(\lambda)$ is therefore the quantity an on-policy distiller transfers per token: it is the epistemic value of teacher feedback on student-generated states, and it upper-bounds the reverse-KL signal that the executable classroom demonstration reports. These claims are limited to this analytical model and its companion artifacts; they are a faithful minimal-model demonstration of the correspondence, not a measurement on production LLMs. These symbols are the rows of `analytical_assumption_index.json`, so the derivation is auditable rather than asserted.

<!-- sheaf-track:simulation -->

The analytical track writes a parameter sweep comparing closed-form mutual information with an independent exact recomputation of it (via total correlation) across $\lambda \in [0, {{lambda_max}}]$ on {{param_sweep_grid_points}} grid points ([@sec:results_mi_sweep], [@fig:ising_mi_curve]).

<!-- sheaf-track:assumption_index -->

The `assumption_index` fragment makes the analytical equations inspectable as a generated artifact instead of relying on prose labels. `output/data/analytical_assumption_index.json` indexes {{analytical_equation_count}} finite-model equation identifiers and {{analytical_assumption_count}} rows; the hydrated pass flag is `{{analytical_assumptions_indexed}}`.

The index is deliberately narrow. It covers the Bernoulli-Ising toy equations, their finite binary state assumptions, and the generated artifacts that test the same symbols. Any missing equation identifier or empty assumption list fails the toy-sweep validation gate.

<!-- sheaf-track:visualization -->

![Closed-form $I(\lambda)$ and an independent exact recomputation via total correlation for the symmetric Bernoulli-Ising toy across {{param_sweep_grid_points}} grid points up to $\lambda_{\max}$ = {{lambda_max}}; grid maximum {{ising_mi_saturation}} nats. Both estimators are deterministic (no sampling), so the right panel is a cross-implementation agreement check (max residual {{sweep_max_residual}} nats), not a sampling residual.](../output/figures/ising_mi_curve.png){#fig:ising_mi_curve width=90% fig-alt="Two-panel plot of mutual information versus coupling strength lambda for the symmetric Bernoulli-Ising toy. Left panel shows the closed-form curve (solid dark line) and an independent exact recomputation via total correlation (dashed blue line) with lambda on the x-axis and mutual information in nats on the y-axis. Right panel shows the recompute-minus-closed-form residual versus lambda with a zero reference line; the two deterministic estimators agree to machine precision."}

![Divergence geometry for the teacher/student categorical toy: reverse KL {{divergence_reverse_kl:.3f}} nats, forward KL {{divergence_forward_kl:.3f}} nats, Jensen-Shannon {{divergence_jensen_shannon:.3f}} nats, alpha-divergence {{divergence_alpha_0_5:.3f}} nats, and clipped reverse KL {{divergence_clipped_reverse_kl:.3f}} nats from `output/data/firstprinciples/divergence_demo.json`.](../output/figures/distillation_divergence_geometry.png){#fig:distillation_divergence_geometry width=92% fig-alt="Two-panel source-backed divergence geometry figure. The left panel compares teacher and student categorical policy mass over four modes. The right panel shows reverse KL, forward KL, Jensen-Shannon, alpha-divergence, and clipped reverse KL values in nats, generated from the first-principles divergence artifact."}

![GNN $\leftrightarrow$ ontology concordance for the Bernoulli–Ising toy ({{gnn_spec_version}}).](../output/figures/gnn_ontology_concordance.png){#fig:gnn_ontology_concordance width=90% fig-alt="Layered concordance diagram linking analytical symbols, GNN variables from bernoulli_toy.gnn.md ({{gnn_spec_version}}), and Active Inference Ontology terms."}

<!-- sheaf-track:gnn -->

The Bernoulli toy is declared in `gnn/bernoulli_toy.gnn.md` ({{gnn_spec_version}}), following the GNN notation role described by Smekal and Friedman [@gnn2023]. [@fig:gnn_ontology_concordance] links GNN variables to Active Inference Ontology terms bound in the analytical ontology fragment; round-trip parity is checked before render.

Measured MI and sweep artifacts in [@sec:results_mi_sweep] ground the same symbol map used in the concordance diagram.

<!-- sheaf-track:ontology -->

### Ontology bindings

- `E1` → **Stream1HabitPrior**
- `E2` → **Stream2HabitPrior**
- `J` → **CrossStreamCouplingPotential**
- `gamma` → **SophisticationWeight**
- `lam` → **EntanglementDeformationParameter**
- `pi1` → **Stream1PolicyVector**
- `pi2` → **Stream2PolicyVector**
- `q_joint` → **EntangledJointPosterior**

