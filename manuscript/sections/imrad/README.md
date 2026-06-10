# IMRAD Fragment Sources

Editable per-section sources for the sheaf-composed manuscript.

- `../../sheaf/manifest.yaml` maps each section to its track fragments and
  composed output name.
- `../../sheaf/tracks.yaml` defines track order, renderers, and optional tracks.
- Run `uv run python scripts/compose_manuscript.py --validate-only --strict` from
  the repo root after fragment or manifest changes.
