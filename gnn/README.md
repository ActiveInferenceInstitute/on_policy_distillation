# GNN model specifications

Generalized Notation Notation (GNN) source specifications — the canonical,
human- and machine-readable description of each Active Inference model.

- `bernoulli_toy.gnn.md` — the Bernoulli coupling toy model.
- `si_tmaze.gnn.md` — the sophisticated-inference T-maze model.
- `graph_world.gnn.md` — the deterministic four-node graph-world model
  (start → cue → choice → goal; see `../docs/models/graph-world.md`).
- `upstream.json` — custody pin: canonical upstream release tag and commit
  (Generalized_Notation_Notation v5.0.3), plus the upstream parser module and
  class the conformance check exercises.

Parsed by `../src/gnn/parser.py`; concordance with the other tracks is checked by
`../src/gnn/concordance.py`. Use the canonical `## ActInfOntologyAnnotation`
section heading (the spaced variant is accepted only as a historical alias).

Conformance: `tests/test_gnn_upstream_conformance.py` runs the pinned upstream
parser against every shipped specification and requires digest equality. The
upstream parser is executed with the GNN checkout's own interpreter, with the
pinned commit's `src/gnn` extracted from Git onto `PYTHONPATH`, so the bytes
under test are the pinned release's bytes rather than the live working tree's.
When the sibling checkout is unavailable the test skips with an explicit
reason; set `ON_POLICY_DISTILLATION_GNN_ROOT` to select a checkout explicitly.

Model authoring starts from the GNN
[template library](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/templates/README.md)
and the
[syntax reference](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/gnn/reference/gnn_syntax.md);
the
[framework integration guide](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/gnn/integration/framework_integration_guide.md)
covers running a specification through the upstream render/execute pipeline
instead of this project's reader.
