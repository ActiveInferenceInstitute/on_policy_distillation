# Reproducibility docs

Everything a reader needs to regenerate this project's outputs and the PDF, and
to understand why the result is deterministic and auditable. These pages are the
quickstart layer over the authoritative contract in
[`../reference/rendering-reproducibility.md`](../reference/rendering-reproducibility.md).

| Page | Read it when you need to |
| --- | --- |
| [`artifacts.md`](artifacts.md) | Understand the `output/` layout, what is regeneratable, deterministic seeds, and the validation pass. |
| [`rendering.md`](rendering.md) | Render the PDF — the two render paths, exact commands, and common failure modes. |
| [`standalone-vs-template.md`](standalone-vs-template.md) | Know when the project renders standalone vs. when it needs the sibling template infra. |
| [`AGENTS.md`](AGENTS.md) | Get the short agent rules for this directory. |

## The one command

Almost everything is downstream of one convergent runner:

```bash
uv run python scripts/run_full_chain.py
```

It runs the canonical analysis chain in the order declared by
`manuscript/config.yaml` `analysis.scripts`, validates, then re-runs the
attestation tail until the validation report is green and stable. Add `--render`
to also build the PDF. Exit code is honest: 0 only when the final
`validate_outputs` pass exits 0.

## Core principle

Authored fragments and configuration produce deterministic data, figures,
composed Markdown, hydrated Markdown, PDF, web, and copied root outputs.
**Do not hand-edit generated artifacts to make a claim pass; regenerate the
producer that owns the artifact.** Everything under
[`../../output/`](../../output/) is regeneratable.
