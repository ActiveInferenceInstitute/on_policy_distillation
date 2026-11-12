# GitHub automation agent guide

- Check steps in `workflows/ci.yml` invoke arms of `scripts/gate.py`.
  Never restate an arm's argv in the workflow — add or change
  the arm, then point the step at it.
- Keep the job key (`release-gate`) and its display name
  (`gnn conformance (pinned)`) stable; `GNN.md` quotes them.
- Pin third-party actions by commit SHA with a `# vX.Y.Z` comment; do not use
  floating major tags.
- The suite is not self-contained: it reads the generated artifact tree, so the
  workflow must run the `chain` arm before `full`.
- Set `ON_POLICY_DISTILLATION_GNN_ROOT` at job level so `gnn` and `full`
  use the same provisioned checkout.
- Do not add a separate `scripts/validate_outputs.py` step; the chain already
  runs it and a workflow cannot validate a tree it never built.
- `pandoc` is required by the typography contract test, so the workflow installs
  it before the arms that run tests. Keep the install step if you keep that test.
- Validate workflow edits in a pull request; the release gate is what proves the
  change.
