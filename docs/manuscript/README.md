# Manuscript Documentation

Modular reader-facing documentation for the manuscript at
[`../../manuscript/`](../../manuscript/): a scoped, machine-checked correspondence
between on-policy distillation (OPD) and active inference, demonstrated on finite
executable toy models.

This directory is documentation-only. It describes the manuscript's structure,
scope, citation surface, hydration system, and figure provenance. It does not
restate scientific claims; those live in the section files, and their scope is
governed by [`claims-and-scope.md`](claims-and-scope.md).

## Pages

| Page | Purpose |
| --- | --- |
| [`section-guide.md`](section-guide.md) | Per-section map: file, IMRAD role, claim carried, key hydration tokens, feeding sheaf tracks. |
| [`claims-and-scope.md`](claims-and-scope.md) | The scope contract: what is claimed, what is **not**, the VFE/EFE separation, and external-context handling. Quotes the scoped-correspondence Proposition (A1–A4). |
| [`citation-map.md`](citation-map.md) | The 117-entry bibliography organized by function, with per-group role statements and per-key claim notes. |
| [`hydration-tokens.md`](hydration-tokens.md) | The `{{token}}` system: where tokens are defined, fail-closed behavior, format-spec syntax, and the no-hand-written-number rule. |
| [`figures.md`](figures.md) | Figure inventory and provenance: source-map discipline, caption/alt-text discipline, output location, and the audit gates binding figures to data. |
| [`AGENTS.md`](AGENTS.md) | Short agent guidance for editing the manuscript. |

## Where things actually live

The manuscript is a composed, hydrated artifact, not a set of hand-edited prose
files. The authoritative sources are:

- **Fragments** — [`../../manuscript/sections/imrad/`](../../manuscript/sections/imrad/),
  bound to IMRAD rows by [`../../manuscript/sheaf/manifest.yaml`](../../manuscript/sheaf/manifest.yaml).
- **Track registry** — [`../../manuscript/sheaf/tracks.yaml`](../../manuscript/sheaf/tracks.yaml)
  declares the fragment-track types, renderers, and compose order.
- **Composed sections** — `manuscript/0*.md` … `manuscript/2*.md` are **outputs** of
  [`../../scripts/compose_manuscript.py`](../../scripts/compose_manuscript.py).
  The exceptions hand-authored directly are `00_abstract.md`, `17_conclusion.md`,
  and `99_references.md` (see [`../../manuscript/AGENTS.md`](../../manuscript/AGENTS.md)).
- **Hydration** — `{{token}}` placeholders are resolved by
  [`../../scripts/z_generate_manuscript_variables.py`](../../scripts/z_generate_manuscript_variables.py)
  from `output/data/manuscript_variables.json`.
- **Figures** — [`../../figures.yaml`](../../figures.yaml) is the source of truth for
  figure ids, captions, alt text, widths, and section bindings; PNGs land in
  `output/figures/`.

## Related contracts

- [`../reference/rendering-reproducibility.md`](../reference/rendering-reproducibility.md)
  — the render/replay/figure-registry/copied-output contract this directory complements.
- [`../reference/notation-supplement.md`](../reference/notation-supplement.md) — integrated notation.
- [`../../manuscript/SYNTAX.md`](../../manuscript/SYNTAX.md) — equation/section/figure labels and token substitution.
