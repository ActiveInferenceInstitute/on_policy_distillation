# Sheaf Track Coverage {#sec:sheaf_coverage}

This page summarizes which **sheaf fragment tracks** are bound for each IMRAD row in `manuscript/sheaf/manifest.yaml`. The matrix is regenerated at compose time.

**Totals:** {{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing (gray).

| Color | Meaning |
| --- | --- |
| Black | Track **present** (bound and fragment exists) |
| White | **Absent** (not bound for this row) |
| Gray | **Missing** (bound but fragment file absent) |

## Introduction

- **Introduction** *(group)*
-   **Motivation and scope**
-   **Contributions**
## Methods

- **Methods** *(group)*
-   **Teacher and student coupling: the analytical model**
-   **On-policy student: pymdp sophisticated inference**
-   **Machine-checked correspondence (Lean)**
-   **Reproducibility methodology**
## Results

- **Results** *(group)*
-   **Teacher and student mutual information**
-   **Free-energy decomposition**
-   **On-policy student rollout (T-maze)**
-   **Validation invariants and statistics**
## Discussion

- **Discussion** *(group)*
-   **Limitations and outlook**
## Appendix

- **Appendix** *(group)*
-   **Supplementary material: reproducibility and full coverage**

![Sheaf track coverage matrix: {{imrad_manifest_rows}} IMRAD rows × {{sheaf_track_count}} fragment columns. Black = present (P), white = absent (—), gray = missing (M). Counts: {{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing.](../output/figures/sheaf_coverage_heatmap.png){#fig:sheaf_coverage_heatmap width=95% fig-alt="Heatmap matrix of IMRAD manuscript rows versus {{sheaf_track_count}} sheaf fragment track columns. Black cells mean the track is bound and the fragment file exists; white cells mean the track is not bound; gray cells mean bound but missing. Rows are grouped by IMRAD block with indented subsection labels; column headers list track ids."}

Appendix row `16_appendix_full_sheaf.md` binds {{appendix_sheaf_track_count}} fragment track types as a composability proof (registry defines {{sheaf_track_count}} types; generated `layers` included).
