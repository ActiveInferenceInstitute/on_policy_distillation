# FAQ

Honest answers about what this project does and does not claim. Terms in **bold**
are defined in [`glossary.md`](glossary.md).

### Is this claiming on-policy distillation literally *is* active inference?

No — it is a *scoped constructive correspondence*, not a universal identity. The
conclusion states it plainly: in the finite artifacts studied here, the teacher
policy is the privileged generative model, the student policy is the tractable
posterior, the reverse-KL distillation loss is variational free energy up to the
**evidence constant**, and the student's own rollouts are the active samples on
which that posterior is corrected — and then:

> That is stronger than a slogan and narrower than a universal theorem. It is a
> claim about declared toy models, generated artifacts, and machine-checked
> manuscript bindings.

Within the explicit finite models, the correspondence is strongly supported and
made unusually auditable; outside them, it is a structured family resemblance
whose limits the manuscript states directly.

### Are the Qwen numbers reproduced?

No. The Qwen3 OPD-vs-RL table and Thinking Machines' replication context are
**external context**, not reproduced results. The manuscript did not measure
them; the values are relayed from the published reports and reproduced only to
explain *why* the correspondence matters. The abstract is explicit: "Qwen's
OPD-vs-RL table and Thinking Machines' replication context remain external
context rather than reproduced results." All measured claims stay inside the
project's own generated artifacts.

### Why reverse KL?

Because the per-token distillation loss studied here is the reverse-KL form, and
in the finite examples the reverse-KL side concentrates on teacher-supported
mass — the **mode-seeking** direction. The manuscript treats the reverse/forward
KL contrast as a finite-support divergence-direction *intuition*, not a universal
law: it is the loss whose variational role the toy artifacts make explicit, while
forward-KL, skew, entropy-aware, contrastive, and hybrid objectives are mapped as
neighboring design points. See [reverse / forward KL](glossary.md#reverse--forward-kl).

### Is the T-maze agent an OPD algorithm?

No — it is an **executable analogue**. The pymdp T-maze is an on-policy active
inference rollout: a **sophisticated-inference** agent that generates its own
observations and acts to minimize **expected free energy** under a privileged
cue. The cue stands in for privileged information available in training but not
at inference. It is an epistemic-foraging toy that *instantiates* the variational
roles — not evidence that an LLM student will discover useful hidden structure at
scale, and not a gridworld benchmark.

### Why so much provenance machinery?

Because the methodological contribution *is* the discipline. The **compose
contract** binds fragment tracks into IMRAD sections, every reported number is a
**hydration token** drawn from a generated artifact, every cross-track claim is
machine-checked before rendering, and **negative controls** keep each failure
path live. The point is that no figure or statistic can drift from the artifact
that produced it, and toy results cannot masquerade as empirical scale claims.
The machinery is what lets the scoped correspondence be *auditable* rather than
asserted. See [`reproducibility/artifacts.md`](reproducibility/artifacts.md).

### Can I run it without Ollama or LaTeX?

Yes for the analysis and tests — the default exemplar path has no network or LLM
calls, so Ollama is not required. Generating data, figures, the composed
manuscript, and running the validation gates and test suite needs only the
project's Python dependencies (numpy, scipy, matplotlib, pyyaml,
`inferactively-pymdp`). LaTeX is required only to render the PDF: the standalone
renderer (`scripts/render_pdf.py`) needs the external `pandoc` and `xelatex`
tools. You can do everything except produce the PDF without them. See
[`reproducibility/standalone-vs-template.md`](reproducibility/standalone-vs-template.md).

### Where do the numbers in the PDF come from?

From **hydration tokens** resolved against generated artifacts. Composition emits
`{{token}}` placeholders; the single hydration boundary
(`scripts/z_generate_manuscript_variables.py`) substitutes them from
`output/data/manuscript_variables.json`, which the producer scripts populate.
Volatile counts, run facts, and figure captions enter only through that file —
never as hand-typed prose — and unknown or mistyped tokens **fail closed** rather
than rendering a wrong value. That is why this documentation states gate floors
and token names instead of snapshot numbers. See
[`reproducibility/rendering.md`](reproducibility/rendering.md).

## See also

- [`glossary.md`](glossary.md) — project term definitions.
- [`reference/rendering-reproducibility.md`](reference/rendering-reproducibility.md) — the reproducibility contract.
- The project root [`README.md`](../README.md) and [`AGENTS.md`](../AGENTS.md).
