# Hydration Tokens

How the `{{token}}` system works: where tokens are defined, the fail-closed behavior on
missing or malformed tokens, the format-spec syntax, and the invariant that no
hand-written number may appear in prose. Derived from
[`../../scripts/inject_variables.py`](../../scripts/inject_variables.py),
[`../../scripts/z_generate_manuscript_variables.py`](../../scripts/z_generate_manuscript_variables.py),
[`../../src/manuscript/hydrate.py`](../../src/manuscript/hydrate.py), and
[`../../manuscript/SYNTAX.md`](../../manuscript/SYNTAX.md).

This is the mechanism that makes [`claims-and-scope.md`](claims-and-scope.md)'s "every
reported number is hydrated from a generated artifact" enforceable rather than aspirational.

## The single hydration boundary

There is exactly one hydration entry point.
[`../../scripts/inject_variables.py`](../../scripts/inject_variables.py) is a thin forwarder
that execs [`../../scripts/z_generate_manuscript_variables.py`](../../scripts/z_generate_manuscript_variables.py),
which calls `hydrate_manuscript_fixed_point()` in
[`../../src/orchestration/artifact_pipeline.py`](../../src/orchestration/artifact_pipeline.py).
The fixed point runs repeated passes until the variable set converges (it raises
`RuntimeError("artifact fixed point did not converge …")` if it cannot), because some
tokens are derived from artifacts that themselves embed tokens.

Composition (`scripts/compose_manuscript.py`) may emit `{{token}}` placeholders, but
**only hydration substitutes them**. The flow is: generate data → write
`output/data/manuscript_variables.json` → substitute into composed sections → write
`output/manuscript/*.md` → render. Numbers are generated first, injected second, rendered
last.

## Where tokens are defined

- **Values** live in `output/data/manuscript_variables.json`, produced by the variable
  generator from the project's analysis artifacts (`output/data/*.json`,
  `output/reports/*.json`). They are *generated*, never hand-written.
- **Substitution** is performed by `substitute_snake_case_tokens()` and
  `write_resolved_manuscript()` in
  [`../../src/manuscript/hydrate.py`](../../src/manuscript/hydrate.py), which reads each
  `manuscript/*.md`, replaces tokens, and writes the resolved copy to
  `output/manuscript/`.
- **Figure captions and alt text** carry tokens too; they are resolved at figure-render
  time by `render_figure_markdown()` in
  [`../../src/visualizations/figure_registry.py`](../../src/visualizations/figure_registry.py)
  using the same `substitute_snake_case_tokens()`. See [`figures.md`](figures.md).

## Token syntax

The token grammar is the regex `_TOKEN_RE` in `hydrate.py`:

```python
re.compile(r"\{\{([a-z][a-z0-9_]*)(?::([+]?)\.(\d+)([efg]))?\}\}")
```

So a token name is **snake_case** (`[a-z][a-z0-9_]*`) wrapped in double braces:

- Plain string: `{{pymdp_planner}}`, `{{classroom_teacher_cue_validity}}`.
- With a **format spec**: `{{name:[sign].PRECISION[TYPE]}}` where `PRECISION` is digits
  and `TYPE` is one of `e`, `f`, `g`, with an optional leading `+` sign flag.
  - `{{sweep_rmse_mi:.1e}}` → scientific notation, 1 digit (e.g. `5.0e-13`).
  - `{{energy_complexity:.3f}}` → fixed point, 3 decimals.
  - `{{privilege_sweep_first_nonzero_kl:.3g}}` → general format, 3 significant figures.
  - `{{privilege_sweep_top_gap:+.3f}}` → signed fixed point.

The format spec is applied in `substitute_snake_case_tokens()` as
`f"{float(value):{sign}.{int(precision)}{fmt}}"`. If the value cannot be coerced to
`float`, the raw string value is substituted instead (a `ValueError` fallback), so a
non-numeric value with a numeric spec degrades to its string form rather than crashing.

Some values are pre-formatted in `format_variables()` (e.g.
`si_tmaze_mean_belief_entropy_formatted`) and used **without** a spec — these
`*_formatted` tokens carry their own precision so prose can write `{{…_formatted}}` plainly.

## Fail-closed behavior

The system is fail-closed on three failure modes:

1. **Unknown / unresolved tokens.** If a `{{token}}` has no matching key in the variable
   set, `write_resolved_manuscript()` collects it and raises
   `ValueError(f"unresolved manuscript tokens: …")` after processing all files. The PDF
   is not produced. (`validate_manuscript_tokens()` exposes the same check as a sorted
   list of unknown names for pre-flight validation.)
2. **Malformed single-brace tokens.** A single-brace pattern like `{name}` (typo of
   `{{name}}`) is caught by `_SINGLE_BRACE_TOKEN_RE` / `collect_malformed_token_names()`,
   raising `ValueError(f"malformed single-brace tokens in {file}: …")`. This catches the
   common brace-count typo before it silently survives into the rendered prose.
3. **Non-convergent artifacts.** If the hydration fixed point cannot stabilize, the
   pipeline raises rather than emitting a partially-hydrated manuscript.

`--allow-draft` (forwarded to the generator) relaxes only the *requirement that analysis
outputs exist* (`require_analysis_outputs=False`) for non-pipeline draft work; it does
not relax the unresolved/malformed-token gates.

## The no-hand-written-number rule

Because every reported value is a generated token, **no hand-written number may appear in
prose**. From [`../reference/rendering-reproducibility.md`](../reference/rendering-reproducibility.md):
"Volatile counts, run facts, semantic restrictions, and figure captions must enter
through `output/data/manuscript_variables.json`, never hard-coded prose." The audit
surfaces a `{{hardcoded_variable_issue_count}}` token reporting hard-coded variable
issues found in the generated audit (referenced in `multi_track_architecture`'s caption),
so the count of violations is itself a hydrated, checkable number.

Practical consequence for editors: to change a number in the manuscript, fix the producer
that owns the artifact and regenerate — do not edit the prose. See
[`AGENTS.md`](AGENTS.md) and [`section-guide.md`](section-guide.md) for which tokens each
section uses.

## Excluded files

`write_resolved_manuscript()` skips files in `EXCLUDED_DOC_FILENAMES` (documentation
files such as `SYNTAX.md`, `README.md`, `AGENTS.md` under `manuscript/`) and copies
`config.yaml`, `preamble.md`, and `*.bib` through unchanged. Only the section markdown is
token-substituted.
