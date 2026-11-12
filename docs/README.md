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

For a flat list of every maintained page under `docs/`, including local
instructions and section indexes, use the [documentation index](documentation-index.md).

| Area | Pages | Read when you need |
| --- | --- | --- |
| [`architecture/`](architecture/README.md) | [overview](architecture/overview.md) · [pipeline](architecture/pipeline.md) · [sheaf compose contract](architecture/sheaf-compose-contract.md) · [gates & validation](architecture/gates-and-validation.md) · [formal layers](architecture/formal-layers.md) | how the system fits together; how a number travels generator → artifact → token → PDF; what the Lean/GNN/ontology layers do and do not prove |
| [`models/`](models/README.md) | [bernoulli-ising](models/bernoulli-ising.md) · [tmaze-pymdp](models/tmaze-pymdp.md) · [classroom](models/classroom.md) · [privilege-sweep](models/privilege-sweep.md) · [graph-world](models/graph-world.md) | the executable model zoo: what each toy model witnesses, generates, and explicitly does *not* claim |
| [`manuscript/`](manuscript/README.md) | [section guide](manuscript/section-guide.md) · [claims & scope](manuscript/claims-and-scope.md) · [citation map](manuscript/citation-map.md) · [hydration tokens](manuscript/hydration-tokens.md) · [figures](manuscript/figures.md) | what each section carries; the precise scope contract (what is and is not claimed); the bibliography by function; the `{{token}}` system; figure provenance |
| [`reviews/`](reviews/README.md) | [deep-review 2026-06 disposition](reviews/deep-review-2026-06.md) · [critical-review 2026-06 disposition](reviews/critical-review-2026-06.md) · [redteam scholarship/visualization 2026-06 disposition](reviews/redteam-scholarship-visualization-2026-06.md) | how external review items were dispositioned, with file-level evidence |
| [`development/`](development/README.md) | [gate](development/gate.md) · [testing](development/testing.md) · [conventions](development/conventions.md) · [extending](development/extending.md) | the gate's arms and measured wall times; test suites/markers/fast lanes; code conventions and the writer/validator boundary; how to add a track, model, figure, or section |
| [`reproducibility/`](reproducibility/README.md) | [artifacts](reproducibility/artifacts.md) · [rendering](reproducibility/rendering.md) · [standalone vs template](reproducibility/standalone-vs-template.md) · [test-isolation soak 2026-06-13](reproducibility/test-isolation-soak-2026-06-13.md) | the `output/` contract and determinism; render quickstart and failure modes; when the sibling template checkout is needed |
| [`reference/`](reference/README.md) | [method inventory](reference/method-inventory.md) (generated) · [configuration & extension](reference/configuration-and-extension.md) · [rendering-reproducibility contract](reference/rendering-reproducibility.md) · [notation supplement](reference/notation-supplement.md) | exhaustive references: every `def`/`class`, every config key, the authoritative rendering contract, notation |
| top level | [glossary](glossary.md) · [faq](faq.md) | term definitions as *this project* uses them; honest answers to the obvious questions |

## Quick start

Run the gate (the fast arm first, the full arm authoritative). Every arm is one
entry point, [`../scripts/gate.py`](../scripts/gate.py), so this page does not
restate a command; `python scripts/gate.py --list` prints each arm's argv:

```bash
uv run --extra dev python scripts/gate.py          # fast arm (default)
uv run --extra dev python scripts/gate.py chain    # build the artifact tree
uv run --extra dev python scripts/gate.py full     # release coverage gate
uv run --extra dev python scripts/gate.py all      # the CI sequence
```

The fast arm excludes tests that perform full fixed-point artifact writes or
mutate shared generated artifacts, and also the expensive rendering, animation,
rollout, and large-compose checks. The full coverage arm remains authoritative.
Arm table and measured wall times: [`development/gate.md`](development/gate.md).
Details: [`development/testing.md`](development/testing.md).

Render the validated project-local PDF through the canonical full chain:

```bash
uv run --extra dev python scripts/gate.py chain
uv run --extra dev python scripts/gate.py render
```

This composes, regenerates, validates, converges the fixed-point attestation, and
emits `output/pdf/on_policy_distillation.pdf`. See
[`reproducibility/rendering.md`](reproducibility/rendering.md) for the optional
sibling-template polish path and common failure modes.

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
