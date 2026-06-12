"""Tests for sheaf layers markdown tables."""

from __future__ import annotations

import json
from pathlib import Path

from manuscript.sheaf.coverage import build_coverage_matrix
from manuscript.sheaf.layers_report import (
    render_binding_matrix_table,
    render_semantic_restrictions_table,
    render_sheaf_layers_markdown,
    render_track_improvement_scope_table,
    render_track_registry_table,
)
from manuscript.sheaf.manifest import load_manifest
from manuscript.sheaf.models import coverage_cell_symbol
from manuscript.sheaf.registry import load_track_registry


def test_coverage_cell_symbol_maps_colors() -> None:
    assert coverage_cell_symbol("black") == "P"
    assert coverage_cell_symbol("gray") == "M"
    assert coverage_cell_symbol("white") == "—"


def test_track_registry_table_row_count(project_root: Path) -> None:
    manifest = load_manifest(project_root / "manuscript" / "sheaf" / "manifest.yaml", project_root=project_root)
    registry = load_track_registry(project_root / manifest.registry_path)
    table = render_track_registry_table(registry)
    assert "<!-- sheaf-layers:registry -->" in table
    assert "## Sheaf fragment track registry" in table
    assert table.count("| `") >= len(registry.tracks)
    assert "**Track count:** {{sheaf_track_count}} registered fragment types." in table


def test_binding_matrix_totals_use_tokens(project_root: Path) -> None:
    manifest = load_manifest(project_root / "manuscript" / "sheaf" / "manifest.yaml", project_root=project_root)
    registry = load_track_registry(project_root / manifest.registry_path)
    matrix = build_coverage_matrix(registry, manifest, project_root)
    table = render_binding_matrix_table(matrix, manifest, project_root=project_root)
    assert "<!-- sheaf-layers:binding-matrix -->" in table
    assert "## IMRAD binding matrix" in table
    assert "{{coverage_present}} present" in table
    assert "{{coverage_bound}} bound" in table
    assert "{{coverage_missing}} missing" in table
    assert table.count("| P |") >= 1
    assert "—" in table


def test_render_sheaf_layers_markdown(project_root: Path) -> None:
    md = render_sheaf_layers_markdown(project_root)
    assert "Sheaf fragment track registry" in md
    assert "IMRAD binding matrix" in md
    assert "<!-- sheaf-layers:legend -->" in md
    assert "<!-- sheaf-layers:section-status -->" in md
    assert "<!-- sheaf-layers:track-status -->" in md
    assert "<!-- sheaf-layers:render-log -->" in md
    assert "| Symbol | Coverage color | Meaning |" in md


def test_track_improvement_scope_table_renders_all_live_rows(project_root: Path) -> None:
    payload = json.loads((project_root / "output" / "data" / "track_improvement_scope.json").read_text(encoding="utf-8"))

    table = render_track_improvement_scope_table(project_root)

    assert "<!-- sheaf-layers:track-improvement-scope -->" in table
    for row in payload["improvement_roadmap"]:
        assert f"`{row['track_id']}`" in table
    assert f"**Improvement rows:** {payload['improvement_row_count']}." in table


def test_semantic_restrictions_table_replaces_missing_values_with_status(project_root: Path) -> None:
    table = render_semantic_restrictions_table(project_root)

    assert "<!-- sheaf-layers:semantic-restrictions -->" in table
    assert "| Semantic certificate ok |" in table
    assert "`None`" not in table
