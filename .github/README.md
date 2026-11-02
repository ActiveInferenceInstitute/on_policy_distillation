# GitHub configuration

Repository automation: workflow definitions in `workflows/`, plus the branch and
PR policy that the release gate enforces. The workflow file is the only
executable artifact here; everything else is documentation for the humans and
agents who change it.

The release gate runs on every push to `main` and every pull request. It is the
same chain documented in the repository `README.md`: lock check, locked sync,
byte-compile, the bounded artifact chain, and the release coverage gate. A
workflow change is a release-gate change, so validate it in a pull request
rather than on `main`.
