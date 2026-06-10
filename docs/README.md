# active_inference_on_policy_distillation — documentation

Modular documentation for the project: a manuscript-plus-code artifact that
establishes a **scoped correspondence between on-policy distillation (OPD) and
active inference** in finite, explicitly declared models (analytical
Bernoulli-Ising oracle, pymdp T-maze, two-agent classroom, graph-world stress
tests), composed into a sheaf-indexed manuscript where every reported number is
hydrated from a generated, machine-checked artifact.

Start with the project root [`README.md`](../README.md) for the overview and
[`AGENTS.md`](../AGENTS.md) for agent guidance; per-directory
`README.md`/`AGENTS.md` pairs document each component.

## Map

| Area | Pages | Read when you need |
| --- | --- | --- |
| [`architecture/`](architecture/README.md) | [overview](architecture/overview.md) · [pipeline](architecture/pipeline.md) · [sheaf compose contract](architecture/sheaf-compose-contract.md) · [gates & validation](architecture/gates-and-validation.md) · [formal layers](architecture/formal-layers.md) | how the system fits together; how a number travels generator → artifact → token → PDF; what the Lean/GNN/ontology layers do and do not prove |
| [`models/`](models/README.md) | [bernoulli-ising](models/bernoulli-ising.md) · [tmaze-pymdp](models/tmaze-pymdp.md) · [classroom](models/classroom.md) · [privilege-sweep](models/privilege-sweep.md) · [graph-world](models/graph-world.md) | the executable model zoo: what each toy model witnesses, generates, and explicitly does *not* claim |
| [`manuscript/`](manuscript/README.md) | [section guide](manuscript/section-guide.md) · [claims & scope](manuscript/claims-and-scope.md) · [citation map](manuscript/citation-map.md) · [hydration tokens](manuscript/hydration-tokens.md) · [figures](manuscript/figures.md) | what each section carries; the precise scope contract (what is and is not claimed); the bibliography by function; the `{{token}}` system; figure provenance |
| [`reviews/`](reviews/README.md) | [deep-review 2026-06 disposition](reviews/deep-review-2026-06.md) | how external review items were dispositioned, with file-level evidence |
| [`development/`](development/README.md) | [testing](development/testing.md) · [conventions](development/conventions.md) · [extending](development/extending.md) | test suites/markers/fast lanes; code conventions and the writer/validator boundary; how to add a track, model, figure, or section |
| [`reproducibility/`](reproducibility/README.md) | [artifacts](reproducibility/artifacts.md) · [rendering](reproducibility/rendering.md) · [standalone vs template](reproducibility/standalone-vs-template.md) | the `output/` contract and determinism; render quickstart and failure modes; when the sibling template checkout is needed |
| [`reference/`](reference/README.md) | [method inventory](reference/method-inventory.md) (generated) · [configuration & extension](reference/configuration-and-extension.md) · [rendering-reproducibility contract](reference/rendering-reproducibility.md) · [notation supplement](reference/notation-supplement.md) | exhaustive references: every `def`/`class`, every config key, the authoritative rendering contract, notation |
| top level | [glossary](glossary.md) · [faq](faq.md) | term definitions as *this project* uses them; honest answers to the obvious questions |

## Quick start

Run the suite (fast lane first, full gate authoritative):

```bash
uv run --extra dev python -m pytest tests/ -m "not artifact_slow and not render_slow" --no-cov
uv run --extra dev python -m pytest tests/ -m "not artifact_slow" --no-cov
uv run python -m pytest tests -q
uv run python scripts/validate_outputs.py
```

The fast lane excludes tests that perform full fixed-point artifact writes or
mutate shared generated artifacts. The tighter edit loop also excludes expensive
rendering, animation, rollout, and large-compose checks. The full coverage gate
remains authoritative. Details: [`development/testing.md`](development/testing.md).

Render through the sibling template checkout after linking sidecar projects:

```bash
cd ../../../template
uv run python -m infrastructure.orchestration link-projects
uv run python scripts/03_render_pdf.py --project working/active_inference_on_policy_distillation
```

See [`reproducibility/rendering.md`](reproducibility/rendering.md) for the
standalone path and common failure modes.

## The one-paragraph scope contract

The manuscript's claim is constructive and finite: a teacher-conditioned
target defines the generative-model term, a tractable student family is the
approximate posterior, and the reverse-KL objective on student-induced
rollouts equals variational free energy up to the evidence constant — exact
for the declared toy objects, *not* a universal theorem about OPD, LLMs, or
biology. Expected free energy enters only on the planning side (the pymdp
agent). External Qwen/Thinking Machines numbers are literature-reported
context, never reproduced results. The full statement with assumptions lives
in [`manuscript/claims-and-scope.md`](manuscript/claims-and-scope.md).
