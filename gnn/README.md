# GNN model specifications

Generalized Notation Notation (GNN) source specifications — the canonical,
human- and machine-readable description of each Active Inference model.

- `bernoulli_toy.gnn.md` — the Bernoulli coupling toy model.
- `si_tmaze.gnn.md` — the sophisticated-inference T-maze model.
- `graph_world.gnn.md` — the deterministic four-node graph-world model
  (start → cue → choice → goal; see `../docs/models/graph-world.md`).

Parsed by `../src/gnn/parser.py`; concordance with the other tracks is checked by
`../src/gnn/concordance.py`.
