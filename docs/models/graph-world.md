# Graph-World Topology Stress Tests

The graph-world models vary the *topology* of the on-policy environment to
confirm that the [T-maze](tmaze-pymdp.md) on-policy story is not an artifact of
one fixed maze. They are deterministic extension artifacts: small node-and-edge
worlds whose walks are computed, not sampled.

Producers:
[`../../scripts/simulate_si_graph_world.py`](../../scripts/simulate_si_graph_world.py)
→ [`../../src/simulation/graph_world.py`](../../src/simulation/graph_world.py)
for the canonical four-node world, and the topology family in
[`../../src/roadmap_tracks/toy_sweep.py`](../../src/roadmap_tracks/toy_sweep.py).
Manuscript home:
[`../../manuscript/06_methods_pymdp.md`](../../manuscript/06_methods_pymdp.md)
and [`../../manuscript/12_results_si_tmaze.md`](../../manuscript/12_results_si_tmaze.md).
Declared in [`../../tracks.yaml`](../../tracks.yaml) under
`extension_tracks.graph_world`, with the node list also in
[`../../pymdp.yaml`](../../pymdp.yaml) (`graph_world.nodes`,
`graph_world.deterministic: true`).

## The canonical four-node world

`write_graph_world_artifacts(project_root)` in
[`graph_world.py`](../../src/simulation/graph_world.py) emits a fixed
`start → cue → choice → goal` path with a monotonically decreasing belief-entropy
series and the action sequence `observe_cue → advance → commit_goal → stay_goal`.
It writes:

- `output/data/si_graph_world_summary.json` — node/edge/step counts, start, goal,
  `goal_reached`, mean belief entropy, and the policy.
- `output/data/si_graph_world_trace.json` — per-step node, action, belief entropy,
  and goal probability.

The manuscript reads `{{si_graph_world_node_count}}` nodes,
`{{si_graph_world_steps}}` steps, and goal-reached flag
`{{si_graph_world_goal_reached}}` from these artifacts. Generate with:

```bash
uv run python scripts/simulate_si_graph_world.py
```

## The topology family

[`toy_sweep.py`](../../src/roadmap_tracks/toy_sweep.py) builds a family of
deterministic topologies — `linear4`, `branch4`, `loop5`, `diamond5` — through
`build_graph_world_topology_sweep`, `build_graph_world_topology_traces`, and
`build_graph_world_invariants`. For each topology a deterministic walk is laid
out (`_topology_trace`) and cross-checked: the per-topology summary node/step
counts must agree with the full trace (`all_summary_trace_agree`,
`all_trace_summary_agree`), and the manuscript reports
`{{si_graph_world_topology_trace_count}}` topology traces with agreement flag
`{{si_graph_world_topology_traces_agree}}`.

## What they stress-test

`_graph_world_trace_invariants` computes three falsifiable invariants from the
actual trace (not hardcoded `True`):

- **reachability** — the walk ends at `goal`.
- **transition_determinism** — no node is ever assigned two different successors.
- **terminal_absorbing** — once `goal` is reached, every later node is `goal`.

A malformed topology — one whose walk never reaches `goal`, revisits a node with
a different successor, or leaves `goal` after arriving — yields `False` on the
corresponding invariant, and `validate_toy_sweep_artifacts` re-derives
`all_passed` from the rows so a tampered summary over a failing row still fails
closed. These topologies also feed the `state_space_catalog`, the
`causal_ablation_matrix`, and the `sensitivity_sweep` grids, all written by
`write_toy_sweep_artifacts` to `output/data/` (invariants to
`output/reports/graph_world_invariants.json`).

Generate the topology artifacts with:

```bash
uv run python scripts/generate_toy_sweep_tracks.py
```

## The explicit non-claim

These are **not a gridworld benchmark**. They do not measure agent performance,
sample efficiency, or reward against any baseline, and they are not a navigation
challenge. They are deterministic structural stress tests: the on-policy
correspondence should hold across more than one topology, and the invariants
should remain falsifiable rather than asserted. As the methods section states,
they are "a minimal-model demonstration of the on-policy-distillation/active-
inference correspondence — claims are limited to these pymdp models and
artifacts, not to production LLM systems."
