# Development docs

Task-oriented guidance for working *on* this project — its test system, code
conventions, and how to extend it without tripping the integration gates. These
pages are the developer's-eye companion to the reader-facing contracts under
[`../reference/`](../reference/).

| Page | Read it when you need to |
| --- | --- |
| [`testing.md`](testing.md) | Understand the suites, markers, fast lanes, the no-mocks policy, the 90% coverage floor, and the chunked runner. |
| [`conventions.md`](conventions.md) | Follow the thin-orchestrator pattern, type-hint/docstring expectations, the ruff + mypy gates, and the writer/validator separation. |
| [`extending.md`](extending.md) | Add a new track, model, figure, or section (a quickstart that links to the full reference). |
| [`AGENTS.md`](AGENTS.md) | Get the short agent rules for this directory. |

## First commands

The project is self-contained: copy it out of the monorepo and it runs on its
own (see [`../reproducibility/standalone-vs-template.md`](../reproducibility/standalone-vs-template.md)).
From the project root:

```bash
# fast edit-loop lane (no slow artifact/render tests, no coverage gate)
uv run --extra dev python -m pytest tests/ -m "not artifact_slow and not render_slow" --no-cov

# regenerate everything in canonical order, then validate
uv run python scripts/run_full_chain.py

# the authoritative coverage gate
uv run python -m pytest tests -q
```

## Where things live

- Business logic: [`../../src/`](../../src/) (see [`../../src/AGENTS.md`](../../src/AGENTS.md)).
- Orchestration: [`../../scripts/`](../../scripts/) (see [`../../scripts/AGENTS.md`](../../scripts/AGENTS.md)).
- Generated artifacts: [`../../output/`](../../output/) (regeneratable; see
  [`../reproducibility/artifacts.md`](../reproducibility/artifacts.md)).
- The full configuration/extension reference:
  [`../reference/configuration-and-extension.md`](../reference/configuration-and-extension.md).
- The rendering/reproducibility contract:
  [`../reference/rendering-reproducibility.md`](../reference/rendering-reproducibility.md).
