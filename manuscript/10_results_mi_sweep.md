```{=latex}
\phantomsection
\addcontentsline{toc}{section}{Results}
\section*{Results}
```

# Mutual-information parameter sweep {#sec:results_mi_sweep}

<!-- sheaf-track:prose -->

Under the correspondence of this paper, the coupling strength $\lambda$ is the degree to which the teacher's privileged variable is bound to the answer the student must produce: at $\lambda=0$ the teacher's hint and the answer are independent, so there is nothing privileged to transfer, while as $\lambda$ grows the teacher acquires a strictly informative channel that the on-policy student lacks at inference time. The mutual information $I(\lambda)$ is therefore exactly the teacher--student mutual information of the entangled joint, the upper bound on how much the privileged generative model $p(o,s)$ can communicate to the tractable posterior $q(s)$ being fit [@friston2010fep; @parr2022active]. We sweep coupling strength $\lambda$ on a grid of {{param_sweep_grid_points}} points up to $\lambda_{\max} = {{lambda_max}}$, tracing this coupling curve from the decoupled limit to maximal entanglement. Closed-form mutual information from [@eq:entangled_joint] is cross-checked against an independent exact recomputation via total correlation from the analytical module ([@sec:methods_analytical]); both are deterministic (no sampling) and agree to {{sweep_max_residual}} nats.

The curve rises monotonically in $\lambda$: more coupling means more transferable information, the analytic analogue of the empirical finding that on-policy distillation closes the teacher--student gap far more cheaply than reinforcement learning when the teacher signal is genuinely informative [@thinkingmachines2025opd]. The free energy of the entangled posterior measured against a mean-field factorised prior is the distillation objective itself: minimising it with the reverse, mode-seeking $D_\mathrm{KL}(q\|p)$ drives the student toward the high-density mode of the teacher rather than averaging over all modes, which is precisely the self-distillation limit pursued by reverse-KL on-policy methods [@gu2024minillm; @agarwal2024gkd; @zhao2026opsd; @liu2026sdpg]. The mode-covering forward direction, by contrast, recovers the supervised-fine-tuning limit of teacher-generated data with its attendant exposure bias [@hinton2015distilling]. The classroom simulation makes the same mechanism executable, a privileged teacher at high cue validity transferring its advantage to an on-policy student through a reverse-KL signal, and the analytical $I(\lambda)$ curve is the closed-form ceiling that simulation approaches. These results are a minimal-model demonstration of the correspondence between the variational and distillation objectives, not a claim about production language models; they hold for the analytical toy and its artifacts.

Measured invariant checks: {{invariants_passed}} / {{invariants_total}} passed on the clean tree.

<!-- sheaf-track:formalism -->

The sweep reuses the entangled joint defined in [@eq:entangled_joint] ([@sec:methods_analytical]). Mutual information $I(\lambda)=\log 2 - H_b(\sigma(\lambda))$ is evaluated on the same $\lambda$ grid as the analytical oracle and its independent exact recomputation.

<!-- sheaf-track:simulation -->

Both estimators are deterministic (no sampling, no RNG) and are evaluated on the same $\lambda$ grid as the closed-form sweep ([@sec:methods_analytical], [@fig:ising_mi_curve]).

<!-- sheaf-track:visualization -->

![](../output/figures/ising_mi_curve.png){width=90%}

*Reproduced from [@fig:ising_mi_curve]. Closed-form $I(\lambda)$ and an independent exact recomputation via total correlation for the symmetric Bernoulli-Ising toy across {{param_sweep_grid_points}} grid points up to $\lambda_{\max}$ = {{lambda_max}}; grid maximum {{ising_mi_saturation}} nats. Both estimators are deterministic (no sampling), so the right panel is a cross-implementation agreement check (max residual {{sweep_max_residual}} nats), not a sampling residual.*
