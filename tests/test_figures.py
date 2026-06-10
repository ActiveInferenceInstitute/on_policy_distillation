from pathlib import Path
import csv
import inspect
import json
import re

import pytest
from PIL import Image

from analytical.hyperparameters import lambda_grid, load_hyperparameters
from visualizations.figure_registry import figure_output_path, load_figure_registry, render_figure_markdown
from visualizations.figures import (
    FIGURE_GENERATORS,
    figure_distillation_divergence_geometry,
    figure_diversity_tradeoff,
    figure_energy_decomposition,
    figure_free_energy_curve,
    figure_graphical_abstract,
    figure_ising_mi_curve,
    figure_scholarship_source_map,
    generate_all_figures,
    run_figure,
)
from visualizations.figures_sheaf import coverage_heatmap_payload, figure_sheaf_layers_overview


def _assert_png(path: Path, *, min_width: int = 400, min_height: int = 200) -> None:
    assert path.exists(), f"missing figure: {path}"
    assert path.stat().st_size > 5_000, f"figure too small: {path}"
    with Image.open(path) as img:
        width, height = img.size
        assert width >= min_width, f"{path.name} width {width} < {min_width}"
        assert height >= min_height, f"{path.name} height {height} < {min_height}"
        assert img.mode == "RGB", f"expected RGB after normalization, got {img.mode} for {path.name}"


def _assert_nonblank_png(path: Path) -> None:
    with Image.open(path) as img:
        extrema = img.convert("L").getextrema()
    assert extrema[0] < extrema[1], f"expected nonblank figure pixels for {path.name}"


def test_figure_generators_match_registry(project_root: Path) -> None:
    registry = load_figure_registry(project_root)
    assert set(FIGURE_GENERATORS) == set(registry)


def test_figure_registry_fail_closed_on_unknown_token(project_root: Path) -> None:
    with pytest.raises(ValueError, match="unresolved figure tokens"):
        render_figure_markdown(
            project_root,
            "sheaf_coverage_heatmap",
            variables={"sheaf_track_count": "30"},
        )


@pytest.mark.timeout(30)
@pytest.mark.render_slow
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_all_generators_write_png(project_root: Path) -> None:
    from analysis import run_analysis
    from manuscript.sheaf.coverage import emit_coverage_artifacts
    from simulation.si_runner import pymdp_available, run_and_persist

    run_analysis(project_root)
    if not pymdp_available():
        pytest.skip("pymdp not installed")
    run_and_persist(project_root)
    emit_coverage_artifacts(project_root)

    for figure_id in FIGURE_GENERATORS:
        path = run_figure(figure_id, project_root)
        assert path == figure_output_path(project_root, figure_id)
        _assert_png(path)


def test_free_energy_grid_matches_ssot(project_root: Path) -> None:
    from analysis import run_analysis

    run_analysis(project_root)
    sweep_path = project_root / "output" / "data" / "parameter_sweep.csv"
    rows = list(csv.DictReader(sweep_path.open(newline="", encoding="utf-8")))
    grid = lambda_grid(load_hyperparameters())
    assert len(rows) == len(grid)


def test_free_energy_figure_distinguishes_exact_target_from_mean_field_gap() -> None:
    source = inspect.getsource(figure_free_energy_curve)
    assert "exact_values" in source
    assert "mean_field_gaps" in source
    assert "kl_divergence(q, mf_joint)" in source
    assert "ising_mutual_information" in source
    assert "Mean-field students pay the missing-coupling gap" in source
    assert "Free energy against entangled prior" not in source


@pytest.mark.timeout(30)
@pytest.mark.render_slow
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_generate_all_figures_complete(project_root: Path) -> None:
    from analysis import run_analysis
    from simulation.si_runner import pymdp_available, run_and_persist

    run_analysis(project_root)
    if not pymdp_available():
        pytest.skip("pymdp not installed")
    run_and_persist(project_root)

    paths = generate_all_figures(project_root)
    registry = load_figure_registry(project_root)
    expected_names = {spec.filename for spec in registry.values()}
    written_names = {path.name for path in paths if path.suffix == ".png"}
    assert expected_names.issubset(written_names)
    assert any(p.name == "sheaf_coverage_matrix.json" for p in paths)
    assert any(p.name == "figure_registry.json" for p in paths)


def test_figure_registry_json_matches_yaml(project_root: Path) -> None:
    from visualizations.figure_registry import write_figure_registry_json

    registry = load_figure_registry(project_root)
    path = write_figure_registry_json(project_root)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert set(payload) == {f"fig:{figure_id}" for figure_id in registry}
    for figure_id, spec in registry.items():
        record = payload[f"fig:{figure_id}"]
        assert record["filename"] == spec.filename
        assert record["generated_by"] == f"visualizations.figures::{figure_id}"


@pytest.mark.timeout(300)
def test_figure_source_map_has_registry_parity_and_data_backing(project_root: Path) -> None:
    from roadmap_tracks.integration_audit import _figure_source_rows_complete, build_figure_source_map

    registry = load_figure_registry(project_root)
    payload = build_figure_source_map(project_root)
    rows = payload.get("rows") or []
    rows_by_id = {row["figure_id"]: row for row in rows}

    assert payload["schema"] == "template_active_inference.figure_source_map.v1"
    assert set(rows_by_id) == set(registry)
    assert payload["registry_figure_ids"] == sorted(registry)
    assert payload["all_figures_mapped"] is True
    assert payload["all_figure_metadata_complete"] is True
    assert _figure_source_rows_complete(project_root, payload) is True

    for figure_id, spec in registry.items():
        row = rows_by_id[figure_id]
        assert row["label"] == f"fig:{figure_id}"
        assert row["output"] == f"output/figures/{spec.filename}"
        assert (project_root / row["output"]).is_file()
        assert row["generator"] == f"visualizations.figures::{figure_id}"
        assert row["caption"] == spec.caption
        assert row["alt"] == spec.alt
        assert row["width"] == spec.width
        assert row["metadata_complete"] is True
        assert row["image_width_px"] >= 400
        assert row["image_height_px"] >= 200
        assert row["variable_tokens"] == sorted(set(row["variable_tokens"]))
        assert row["caption_token_count"] >= 0
        assert row["alt_token_count"] >= 0
        assert row["sources"]
        assert row["source_fields"]
        assert row["source_field_count"] == len(row["source_fields"])
        assert row["validation_gates"]
        assert row["validation_gate_count"] == len(row["validation_gates"])
        assert row["source_paths_exist"] is True
        assert row["mapped"] is True
        assert set(row["source_path_status"]) == set(row["sources"])
        assert all((project_root / rel).exists() for rel in row["sources"])

    tmaze_row = rows_by_id["tmaze_schematic"]
    assert {
        "pymdp.yaml",
        "output/data/si_tmaze_summary.json",
        "output/data/si_tmaze_model_matrices.json",
    } <= set(tmaze_row["sources"])
    assert {
        "pymdp.yaml:planning_horizon",
        "pymdp.yaml:agent.si_policy_len",
        "output/data/si_tmaze_summary.json:$.planning_horizon",
        "output/data/si_tmaze_summary.json:$.policy_len",
        "output/data/si_tmaze_model_matrices.json:$.A_shapes",
        "output/data/si_tmaze_model_matrices.json:$.B_shapes",
        "output/data/si_tmaze_model_matrices.json:$.environment",
    } <= set(tmaze_row["source_fields"])
    assert {
        "validate_outputs.si_summary_schema",
        "validate_outputs.si_tmaze_model_matrices_schema",
        "test_figures.tmaze_schematic_uses_configured_horizon",
    } <= set(tmaze_row["validation_gates"])


def test_figure_ising_mi_curve_dimensions(project_root: Path) -> None:
    from analysis import run_analysis

    run_analysis(project_root)
    source = inspect.getsource(figure_ising_mi_curve)
    assert "label=\"exact recompute\"" not in source
    assert "ax_main.plot(\n            lambdas,\n            empirical" not in source
    registry = load_figure_registry(project_root)
    figure_text = registry["ising_mi_curve"].alt + "\n" + registry["ising_mi_curve"].caption
    assert "solid and dashed" not in figure_text
    assert "dashed) for the symmetric Bernoulli-Ising toy" not in figure_text
    assert "recompute-minus-closed-form residuals" in figure_text
    path = figure_ising_mi_curve(project_root)
    _assert_png(path, min_width=600, min_height=250)


def test_interpretive_figures_expose_formula_signs_and_caveats(project_root: Path) -> None:
    registry = load_figure_registry(project_root)
    diversity_source = inspect.getsource(figure_diversity_tradeoff)
    divergence_source = inspect.getsource(figure_distillation_divergence_geometry)
    energy_source = inspect.getsource(figure_energy_decomposition)
    scholarship_source = inspect.getsource(figure_scholarship_source_map)

    assert "Pass@k = 1 - (1 - p)^k" in diversity_source
    assert "$Pass@k = 1-(1-p)^k$" in registry["diversity_tradeoff"].caption
    assert "not a universal KL law" in divergence_source
    assert "universal KL outcome" in registry["distillation_divergence_geometry"].caption
    assert "G = risk + ambiguity - value" in energy_source
    assert "G = risk + ambiguity - epistemic - pragmatic" in registry["energy_decomposition"].caption
    assert "max_display_families = 12" in scholarship_source
    assert "print-condensed" in registry["scholarship_source_map"].caption


def test_figure_sheaf_layers_overview_dimensions(project_root: Path) -> None:
    from manuscript.sheaf.coverage import emit_coverage_artifacts

    emit_coverage_artifacts(project_root)
    payload = coverage_heatmap_payload(project_root)
    assert payload is not None
    path = figure_sheaf_layers_overview(project_root)
    assert path is not None
    _assert_png(path, min_width=900, min_height=500)


@pytest.mark.render_slow
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_graphical_abstract_is_cover_quality_near_square_png(project_root: Path) -> None:
    path = run_figure("graphical_abstract", project_root)

    assert path.name == "graphical_abstract.png"
    _assert_png(path, min_width=1350, min_height=1350)
    _assert_nonblank_png(path)
    with Image.open(path) as img:
        width, height = img.size
    aspect_ratio = width / height
    assert 0.92 <= aspect_ratio <= 1.08


@pytest.mark.render_slow
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_graphical_abstract_uses_full_bleed_cover_background(project_root: Path) -> None:
    path = run_figure("graphical_abstract", project_root)

    with Image.open(path) as img:
        rgb = img.convert("RGB")
        width, height = rgb.size
        sampled_corners = [
            rgb.getpixel((20, 20)),
            rgb.getpixel((width - 21, 20)),
            rgb.getpixel((20, height - 21)),
            rgb.getpixel((width - 21, height - 21)),
        ]

    assert all(pixel != (255, 255, 255) for pixel in sampled_corners)


def test_graphical_abstract_represents_artifact_validation_spine(project_root: Path) -> None:
    source = inspect.getsource(figure_graphical_abstract)
    registry = load_figure_registry(project_root)
    metadata = registry["graphical_abstract"].alt + "\n" + registry["graphical_abstract"].caption
    assert "Lean + gates" in source
    assert "proof_extraction_theorem_count" in source
    combined = source + "\n" + metadata
    for forbidden in ("Empirical", "Qwen", "AIME", "GPU-hours"):
        assert forbidden not in combined


def test_tmaze_schematic_uses_configured_horizon(project_root: Path) -> None:
    from simulation.pymdp_config import load_pymdp_config
    from simulation.tmaze_model import spec_from_config
    from visualizations.figures_diagrams import figure_tmaze_schematic

    source = inspect.getsource(figure_tmaze_schematic)
    assert "TMazeSpec()" not in source
    assert "load_pymdp_config(root)" in source
    assert "spec_from_config(config)" in source

    config = load_pymdp_config(project_root)
    spec = spec_from_config(config)
    assert spec.planning_horizon == config.planning_horizon
    assert spec.policy_len == config.policy_len


@pytest.mark.render_slow
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_si_tmaze_model_matrices_figure_is_registered_and_nonblank(project_root: Path) -> None:
    from simulation.si_runner import pymdp_available, run_and_persist

    if not pymdp_available():
        pytest.skip("pymdp not installed")
    run_and_persist(project_root)
    registry = load_figure_registry(project_root)
    assert "si_tmaze_model_matrices" in registry
    path = run_figure("si_tmaze_model_matrices", project_root)
    assert path.name == "si_tmaze_model_matrices.png"
    _assert_png(path, min_width=800, min_height=450)
    _assert_nonblank_png(path)


def test_appendix_formalism_uses_registry_tokens(project_root: Path) -> None:
    path = (
        project_root
        / "manuscript"
        / "sections"
        / "imrad"
        / "appendix_full_sheaf"
        / "formalism.md"
    )
    text = path.read_text(encoding="utf-8")
    assert "{{appendix_sheaf_track_count}}" in text
    assert re.search(r"\|\s*\\mathcal\{T\}_\{.*full.*\}\s*\|\s*=\s*9", text) is None


def test_coverage_page_section_figures_registered(project_root: Path) -> None:
    from visualizations.figure_registry import load_section_figures

    refs = load_section_figures(project_root).get("coverage_page", ())
    assert refs and refs[0].figure_id == "sheaf_coverage_heatmap"
    assert refs[0].number is None
    # pandoc-crossref owns numbering: no hand-written caption prefix is emitted.
    assert refs[0].caption_prefix == ""


def test_figure_sheaf_coverage_heatmap_dimensions(project_root: Path) -> None:
    from manuscript.sheaf.coverage import emit_coverage_artifacts
    from visualizations.figures_sheaf import figure_sheaf_coverage_heatmap

    emit_coverage_artifacts(project_root)
    path = figure_sheaf_coverage_heatmap(project_root)
    assert path is not None
    _assert_png(path, min_width=700, min_height=400)


def test_coverage_heatmap_payload_none_without_sections(tmp_path: Path) -> None:
    assert coverage_heatmap_payload(tmp_path) is None
