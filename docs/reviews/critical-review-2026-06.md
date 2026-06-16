# Critical-review disposition ledger (2026-06)

This page maps the critical-review hardening request received on 2026-06-12 to
repository evidence. Dispositions are file-backed:

- **LANDED** — implemented; evidence file(s) named.
- **DEFERRED** — accepted in principle but blocked on an explicit future decision.
- **REJECTED** — not adopted, with the reason stated.

## Disposition Matrix

| Review item | Disposition | Evidence |
|---|---|---|
| Retitle the manuscript to a finite-scope active-inference framing, now "On-Policy Distillation as Active Inference in Finite Variational Models" | **LANDED** | `manuscript/config.yaml`; `README.md`; `docs/reference/README.md`; `docs/reference/notation-supplement.md` |
| Reframe abstract, introduction, discussion, and conclusion around finite-model reading/correspondence rather than a universal identity | **LANDED** | `manuscript/00_abstract.md`; `manuscript/sections/imrad/intro_motivation/prose.md`; `manuscript/sections/imrad/intro_contributions/prose.md`; `manuscript/sections/imrad/discussion_outlook/prose.md`; `manuscript/17_conclusion.md`; `docs/manuscript/claims-and-scope.md` |
| Preserve VFE/EFE separation and existing finite-object proposition | **LANDED** | `manuscript/00_abstract.md`; `manuscript/sections/imrad/intro_contributions/prose.md`; `docs/manuscript/claims-and-scope.md` |
| Add deterministic finite sequential distribution-shift artifact | **LANDED** | `src/firstprinciples/sequential_shift.py`; `src/firstprinciples/artifacts.py`; `src/manuscript/variables.py`; `src/artifact_contracts.py`; `src/gates/output_checks.py` |
| Bind the sequential-shift artifact into manuscript results and visualization | **LANDED** | `figures.yaml`; `src/visualizations/figures_firstprinciples.py`; `src/visualizations/figures.py`; `manuscript/sections/imrad/results_si_tmaze/prose.md`; `src/roadmap_tracks/integration_audit_artifacts.py` |
| Add positive and negative verifier controls for the new artifact and source-map binding | **LANDED** | `tests/test_firstprinciples_sequential_shift.py`; `tests/test_firstprinciples_artifacts.py`; `tests/test_figures.py`; `tests/gates/test_output_gates.py`; `data/claim_ledger.yaml` |
| Add requested primary citation anchors where absent | **LANDED** | `manuscript/references.bib`; `src/roadmap_tracks/scholarship/sources_review.py`; `src/roadmap_tracks/scholarship/schema.py`; `manuscript/sections/imrad/methods_sheaf/scholarship.md` |
| Do not duplicate Lopez-Paz | **LANDED** | `manuscript/references.bib` retains the existing `lopezpaz2016unifying` row; no new Lopez-Paz key was added |
| Treat Qwen, Thinking Machines, RLHF, STaR, and FAIR/reproducibility sources as external context unless locally reproduced | **LANDED** | `manuscript/00_abstract.md`; `manuscript/sections/imrad/discussion_outlook/prose.md`; `src/roadmap_tracks/scholarship/sources_review.py`; `docs/manuscript/claims-and-scope.md` |
| Do not perform DOI, Zenodo, public archive, or GitHub release publication | **DEFERRED** | `manuscript/config.yaml` still has empty DOI fields; `src/roadmap_tracks/scholarship/sources_review.py` marks FAIR as context only; this ledger records release/archive work as requiring an explicit future publish decision |
| Do not promote biological, production-LLM, or empirical OPD claims from the toy artifacts | **LANDED** | `manuscript/00_abstract.md`; `manuscript/sections/imrad/results_si_tmaze/prose.md`; `manuscript/sections/imrad/discussion_outlook/prose.md`; `manuscript/17_conclusion.md`; `docs/manuscript/claims-and-scope.md` |

## Maintenance Note

Release/archive requests are deliberately not converted into TODO-free claims
here. A future publish run must re-verify DOI, archive, repository, and public
release metadata against its own release checklist before changing this
disposition.
