# GitHub configuration

Repository automation: workflow definitions in `workflows/`, plus the branch and
PR policy that the release gate enforces. The workflow file is the only
executable artifact here; everything else is documentation for the humans and
agents who change it.

The release gate runs on every push to `main` and every pull request. It is one
job (`release-gate`, displayed as `gnn conformance (pinned)`) whose check steps
invoke [`../scripts/gate.py`](../scripts/gate.py): after one locked sync,
`lint`, `docs`, `gnn`, `chain`, and `full`. The workflow does not duplicate
check argv; `python scripts/gate.py --list` prints the argv of every
arm, and `docs/development/gate.md` records the measured wall times. A workflow
change is a release-gate change, so validate it in a pull request rather than on
`main`.

The pinned GNN parser revision, the provisioning path, and what the conformance
test parses are recorded in [`GNN.md`](GNN.md).

Dependency updates are configured in `dependabot.yml`: weekly, grouped pull
requests for the pinned workflow actions and for the Python manifest.
