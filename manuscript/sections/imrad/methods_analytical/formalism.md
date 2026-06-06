In the distillation reading, the two binary streams $\pi_1,\pi_2$ are the teacher and student policies, and the coupling $\lambda$ measures how strongly the teacher's privileged variable is tied to the answer the student must reproduce. The entangled joint over the pair satisfies

$$
q_\lambda(\pi) \propto E(\pi)\,\exp(\lambda J(\pi)),
$$ {#eq:entangled_joint}

with symmetric Ising coupling $J$ and deformation parameter $\lambda$. Reading $q_\lambda$ as the generative model $p(o,s)$ that a tractable student must approximate, $\lambda$ controls exactly the teacher--student dependence that on-policy distillation exists to transfer: at $\lambda=0$ the student gains nothing from the teacher, while at large $\lambda$ the teacher's privileged information $I$ is fully informative about the target. This is the minimal model of the coupling that reverse-KL distillation objectives [@gu2024minillm; @agarwal2024gkd] and their self-distillation descendants [@zhao2026opsd; @liu2026sdpg] are built to exploit. Let $\sigma(\lambda)=q_\lambda(\pi_1=\pi_2)$ be the probability that the two streams agree (the diagonal mass of the $2\times2$ joint) — equivalently, the probability that an on-policy student rollout matches the privileged teacher; by symmetry both marginals are uniform. With binary entropy $H_b(p)=-p\log p-(1-p)\log(1-p)$ in nats, the joint entropy is $H(q_\lambda)=\log 2 + H_b(\sigma(\lambda))$ while each marginal contributes $\log 2$, so the teacher--student mutual information is

$$
I(\lambda)=\sum_k H(q_k)-H(q_\lambda)=\log 2 - H_b(\sigma(\lambda)),
$$

vanishing at $\lambda=0$ ($\sigma=\tfrac12$, independent streams — the teacher conveys no privileged signal, the SFT-style off-policy limit [@hinton2015distilling]) and saturating at $\log 2$ as $\lambda\to\infty$ ($\sigma\to1$, perfectly entangled — the teacher fully determines the student target, the self-distillation limit). $I(\lambda)$ is therefore the quantity an on-policy distiller transfers per token: it is the epistemic value of teacher feedback on student-generated states, and it upper-bounds the reverse-KL signal that the executable classroom demonstration reports. These claims are limited to this analytical model and its companion artifacts; they are a faithful minimal-model demonstration of the correspondence, not a measurement on production LLMs. These symbols are the rows of `analytical_assumption_index.json`, so the derivation is auditable rather than asserted.
