# GNN conformance

`gnn conformance (pinned)` is the display name of the `release-gate` job in
[`workflows/ci.yml`](workflows/ci.yml). The job key is `release-gate`; the
workflow name is `on-policy-distillation-ci`.

## The pin

The canonical pin file is [`../gnn/upstream.json`](../gnn/upstream.json), schema
`gnn-importer-pin/v1` (there is no `.github/gnn-pin.json`). It records:

| Field | Value |
| --- | --- |
| `repository` | `https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation` |
| `commit` | `75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf` |
| `tag` / `version` | `v5.1.0` / `5.1.0` |
| `parser_module` / `parser_class` | `gnn.parsers.markdown_parser` / `MarkdownGNNParser` |

`tests/test_gnn_upstream_conformance.py` pins the pin itself (`CANONICAL_TAG` /
`CANONICAL_COMMIT`), so a silent re-pin fails instead of passing unnoticed.

## What the job validates

The pin's shape, schema, repository identity, this pointer and the shipped
specifications are validated by the estate's shared reader,
`src/gnn/importers.py` in the pinned upstream release (the
[GNN-FEP contract](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/workflows/gnn-fep.md)).
The arm runs it from the pinned revision:

```
python -m gnn.importers check --repo . --require-pointer \
    --workflow .github/workflows/ci.yml --job release-gate
```

The `src/gnn` tree is extracted from the pinned commit with `git archive` onto
`PYTHONPATH` and executed by the pinned checkout's own interpreter, so the reader
and the parser it validates are the pinned release's bytes rather than a live
working tree's. `--require-pointer` makes this file checkable: it must name the
pin file, the pinned revision, `ci.yml` and the `release-gate` job key.

The arm then runs `tests/test_gnn_upstream_conformance.py` and
`tests/test_gnn.py`. The first extracts `src/gnn` from the pinned commit with
`git archive`, runs the pinned `gnn.parsers.markdown_parser.MarkdownGNNParser`
under the pinned checkout's own interpreter, and compares normalized digests
against the project-owned parser in [`../src/gnn/parser.py`](../src/gnn/parser.py)
for every shipped `gnn/*.gnn.md` spec — `bernoulli_toy`, `graph_world`,
`si_tmaze` — plus a leniency mutant (the doubled-space
`## ActInf  Ontology  Annotation` heading) as the non-vacuity control. The digest
comparison is the member's own evidence: the shared reader validates the pin and
the specification syntax, not digest equality with the project parser.

## How the job provisions it

Check steps invoke arms of [`../scripts/gate.py`](../scripts/gate.py);
setup remains in the workflow, and check argv is owned by the entry point.

```
uv run --extra dev python scripts/gate.py gnn     # provision/select + conformance tests
uv run --extra dev python scripts/gate.py full    # release coverage gate, same checkout
```

The `gnn` and `full` arms honor an explicit `ON_POLICY_DISTILLATION_GNN_ROOT`
selection (empty values fail). Without it, a usable sibling
`Generalized_Notation_Notation` checkout is read-only input, otherwise
`output/gnn-pin/` is provisioned. The sibling slot is never a provisioning
destination. Occupied unusable destinations are refused, not repaired.
Provisioning fetches the pin and its tag, creates a Python 3.12 environment,
and installs `numpy`, `defusedxml`, and `psutil` there.

The workflow sets `ON_POLICY_DISTILLATION_GNN_ROOT` at job level, so the `full`
arm runs the conformance tests against the same checkout: an explicit selection
makes an unavailable or divergent checkout a failure rather than a skip, and the
90% coverage gate never silently loses the pinned-parser half. The arm also
appends `gnn-version=5.1.0` to `$GITHUB_STEP_SUMMARY`, and prints the tag,
version, commit, and checkout path.

## Action pins

The workflow uses `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1`
(v7.0.1) and `astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2`
(v10.3.3, `python-version: "3.14"`). It does **not** use the estate composite
action. Its estate pin is
`ActiveInferenceInstitute/.github/.github/actions/setup-python-uv@7159e67315330aac8e414aebae0ad1e999a41448`.
