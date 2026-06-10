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

## Results

- **Results** *(group)*
-   **Teacher and student mutual information**
-   **Free-energy decomposition**
-   **On-policy student rollout (T-maze)**

## Discussion

- **Discussion** *(group)*
-   **Limitations and outlook**

## Appendix

- **Appendix** *(group)*
-   **Supplementary material: full coverage and concordance**
-   **Supplementary material: reproducibility methodology**
-   **Supplementary material: validation invariants and statistics**

![Sheaf track coverage matrix mapping {{imrad_manifest_rows}} IMRAD manuscript rows against {{sheaf_track_count}} composable fragment-track columns: black = present (P), white = absent (—), gray = bound-but-missing (M), with counts {{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing. The figure shows the science-bearing track subset; build-machinery columns are omitted and the full matrix appears in the supplement. The matrix is the gluing record showing which evidence fragment is locally attached to each manuscript section. Reading it as a sheaf condition, a consistent (fully present, zero-missing) column set is what licenses gluing the local toy results, Lean witnesses, and pymdp rollouts into one globally coherent active-inference argument about on-policy distillation.](../output/figures/sheaf_coverage_heatmap.png){#fig:sheaf_coverage_heatmap width=95% fig-alt="Heatmap matrix of IMRAD manuscript rows versus {{sheaf_track_count}} sheaf fragment track columns. Black cells mean the track is bound and the fragment file exists; white cells mean the track is not bound; gray cells mean bound but missing. Rows are grouped by IMRAD block with indented subsection labels; column headers list track ids."}

Appendix row `18_supplement_full_coverage.md` binds {{appendix_sheaf_track_count}} fragment track types as a composability proof (registry defines {{sheaf_track_count}} types; generated `layers` included).
