# Visualizations

Registry-driven figures for analytical, simulation, and sheaf tracks.

| Module | Role |
| --- | --- |
| [`figures.yaml`](../../figures.yaml) | Style palette, per-figure alt/caption, `section_figures` bindings |
| [`figure_style.py`](figure_style.py) | `load_figure_style`, `apply_style`, font-role and palette-contrast reports |
| [`figure_registry.py`](figure_registry.py) | `FigureSpec`, markdown rendering, `figure_output_path` |
| [`figure_io.py`](figure_io.py) | `save_figure_png` — RGB-normalized PNG save for PDF pipeline |
| [`figures.py`](figures.py) | Analytical + SI generators, `FIGURE_GENERATORS`, `run_figure`, `generate_all_figures` |
| [`figures_sheaf*.py`](figures_sheaf.py) | Coverage heatmap payload, draw helpers, layers overview |

All analytical/SI PNGs route through `figure_io.save_figure_png` via `_save_styled_figure`.
Free-energy plots use `lambda_grid()` from `analytical/hyperparameters.py` (same SSOT as
`parameter_sweep.csv`). Sheaf heatmap colors derive from `figures.yaml` palette roles when
`load_coverage_config(..., project_root=root)` is used. Shared palette roles are semantic:
blue for analytical structure, teal for student/on-policy signals, amber for
teacher/privilege/context, purple for finite energy terms, green for validation, and red
only for failure/risk.

The cover generator (`figures_abstract.py`) is a source-bound technical schematic. It must
state the finite-model active-inference reading/correspondence and must not reintroduce
the obsolete equality slogan `OPD = Active Inference`. It is also intentionally
quantitative-free: no nats, cue values, losses, counts, or metric badges belong on the
cover. Detailed quantitative evidence belongs in the registered body figures and tables.

`output/reports/visualization_quality_audit.json` records readable/nonblank pixels,
source binding, caption scope, cover wording, cover quantitative-free status,
`palette_contrast_report`, and `font_role_report`;
`validate_outputs.visualization_quality_audit_schema` fails if any of those row-level
checks drift.

Entry point: `scripts/generate_figures.py` → `generate_all_figures()`.
