# GitHub automation agent guide

- The release gate is defined in `workflows/ci.yml`; keep it in sync with the
  commands in the repository `README.md`.
- Pin third-party actions by commit SHA with a `# vX.Y.Z` comment; do not use
  floating major tags.
- The suite is not self-contained: it reads the generated artifact tree, so the
  workflow must build the tree (`scripts/run_full_chain.py --max-passes 4`)
  before running `pytest`.
- Do not add a separate `scripts/validate_outputs.py` step; the chain already
  runs it and a workflow cannot validate a tree it never built.
- `pandoc` is required by the typography contract test, so the workflow installs
  it before the coverage gate. Keep the install step if you keep that test.
- Validate workflow edits in a pull request; the release gate is what proves the
  change.
