"""Manuscript gate validation tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from gates.manuscript_checks import validate_manuscript_selected_strict
from gates.validation import validate_manuscript

from gate_support import ensure_gate_artifacts

# This module mutates tracked manuscript sources (with restoration) and runs
# fixed-point artifact refreshes — it belongs in the slow mutating lane, not
# the daily fast lane.
pytestmark = [pytest.mark.timeout(300), pytest.mark.artifact_slow, pytest.mark.mutates_artifacts]


@pytest.mark.timeout(300)
@pytest.mark.artifact_slow
def test_validate_manuscript_contract(project_root: Path) -> None:
    from manuscript.hydrate import write_resolved_manuscript
    from manuscript.variables import generate_variables

    ensure_gate_artifacts(project_root)
    write_resolved_manuscript(project_root, generate_variables(project_root, require_analysis_outputs=False))
    checks = validate_manuscript(project_root)
    selected_keys = {
        "claim_ledger_valid",
        "methods_sheaf_layers",
        "citation_keys_resolved",
        "resolved_manuscript_hydrated",
    }
    selected = validate_manuscript_selected_strict(project_root, selected_keys)
    assert selected == {key: checks[key] for key in selected_keys}
    assert checks["sheaf_manifest"]
    assert checks["sheaf_registry"]
    assert checks["sheaf_valid"]
    assert checks["coverage_matrix_valid"]
    assert checks["full_sheaf_appendix_tracks"]
    assert checks["imrad_groups_present"]
    assert checks["claim_ledger_valid"]
    assert checks["gnn_concordance"]
    assert checks["sheaf_coverage_page"]
    assert checks["sheaf_coverage_json"]
    assert checks["sheaf_coverage_heatmap"]
    assert checks["methods_sheaf_layers"]
    assert checks["manuscript_tokens_registered"]
    assert checks["citation_keys_resolved"]
    assert checks["resolved_manuscript_hydrated"]


def test_validate_manuscript_selected_strict_rejects_unknown_key(project_root: Path) -> None:
    with pytest.raises(KeyError, match="unsupported lazy manuscript check keys"):
        validate_manuscript_selected_strict(project_root, {"not_a_real_manuscript_check"})


def test_validate_manuscript_methods_sheaf_layers_negative(project_root: Path) -> None:
    from manuscript.sheaf import compose_all_sections

    path = project_root / "manuscript" / "19_supplement_reproducibility.md"
    if not path.is_file():
        compose_all_sections(project_root)
    original = path.read_text(encoding="utf-8")
    stat = path.stat()
    try:
        path.write_text(original.replace("<!-- sheaf-layers:registry -->", ""), encoding="utf-8")
        checks = validate_manuscript(project_root, only={"methods_sheaf_layers"})
        assert checks["methods_sheaf_layers"] is False
    finally:
        # Restore bytes AND mtime: a newer-looking composed file makes saved
        # staleness reports look stale and poisons later tests (same class as
        # the test_semantic_sheaf isolation defect).
        path.write_text(original, encoding="utf-8")
        os.utime(path, (stat.st_atime, stat.st_mtime))


@pytest.mark.parametrize(
    ("needle", "replacement"),
    [
        ("<!-- sheaf-layers:binding-matrix -->", ""),
        ("<!-- sheaf-layers:legend -->", ""),
        ("<!-- sheaf-layers:render-log -->", ""),
        ("sheaf_layers_overview.png", "broken_layers_overview.png"),
    ],
)
def test_validate_manuscript_methods_sheaf_layers_negative_markers(
    project_root: Path,
    needle: str,
    replacement: str,
) -> None:
    from manuscript.sheaf import compose_all_sections

    path = project_root / "manuscript" / "19_supplement_reproducibility.md"
    if not path.is_file():
        compose_all_sections(project_root)
    original = path.read_text(encoding="utf-8")
    stat = path.stat()
    try:
        path.write_text(original.replace(needle, replacement), encoding="utf-8")
        checks = validate_manuscript(project_root, only={"methods_sheaf_layers"})
        assert checks["methods_sheaf_layers"] is False
    finally:
        # Restore bytes AND mtime: a newer-looking composed file makes saved
        # staleness reports look stale and poisons later tests (same class as
        # the test_semantic_sheaf isolation defect).
        path.write_text(original, encoding="utf-8")
        os.utime(path, (stat.st_atime, stat.st_mtime))


def test_validate_manuscript_full_sheaf_appendix_tracks_negative(project_root: Path) -> None:
    path = project_root / "manuscript" / "18_supplement_full_coverage.md"
    original = path.read_text(encoding="utf-8")
    stat = path.stat()
    try:
        path.write_text(original.replace("sheaf-track:prose", "sheaf-track:broken"), encoding="utf-8")
        checks = validate_manuscript(project_root, only={"full_sheaf_appendix_tracks"})
        assert checks["full_sheaf_appendix_tracks"] is False
    finally:
        # Restore bytes AND mtime: a newer-looking composed file makes saved
        # staleness reports look stale and poisons later tests (same class as
        # the test_semantic_sheaf isolation defect).
        path.write_text(original, encoding="utf-8")
        os.utime(path, (stat.st_atime, stat.st_mtime))


def test_validate_manuscript_resolved_hydrated_negative(project_root: Path) -> None:
    from manuscript.hydrate import write_resolved_manuscript
    from manuscript.variables import generate_variables

    resolved = project_root / "output" / "manuscript" / "00_abstract.md"
    if not resolved.is_file():
        write_resolved_manuscript(project_root, generate_variables(project_root, require_analysis_outputs=False))
    original = resolved.read_text(encoding="utf-8")
    try:
        resolved.write_text(original + "\n{{unresolved_test_token}}\n", encoding="utf-8")
        checks = validate_manuscript(project_root, only={"resolved_manuscript_hydrated"})
        assert checks["resolved_manuscript_hydrated"] is False
    finally:
        resolved.write_text(original, encoding="utf-8")


def test_validate_manuscript_resolved_hydrated_allows_generated_latex_bookends(project_root: Path) -> None:
    from manuscript.hydrate import write_resolved_manuscript
    from manuscript.variables import generate_variables

    output_dir = write_resolved_manuscript(
        project_root,
        generate_variables(project_root, require_analysis_outputs=False),
    )
    begin = output_dir / "00_00_transmission_begin.md"
    original = begin.read_text(encoding="utf-8") if begin.is_file() else None
    try:
        begin.write_text("\\thispagestyle{empty}\n\\begin{samepage}\n", encoding="utf-8")

        checks = validate_manuscript(project_root, only={"resolved_manuscript_hydrated"})

        assert checks["resolved_manuscript_hydrated"] is True
    finally:
        if original is None:
            begin.unlink(missing_ok=True)
        else:
            begin.write_text(original, encoding="utf-8")


def test_validate_manuscript_gnn_concordance_negative(project_root: Path) -> None:
    gnn = project_root / "gnn" / "bernoulli_toy.gnn.md"
    original = gnn.read_text(encoding="utf-8")
    try:
        gnn.write_text(original.replace("pi1=Stream1PolicyVector\n", ""), encoding="utf-8")
        checks = validate_manuscript(project_root, only={"gnn_concordance"})
        assert checks["gnn_concordance"] is False
    finally:
        gnn.write_text(original, encoding="utf-8")


def test_validate_manuscript_tokens_registered_negative(project_root: Path) -> None:
    path = project_root / "manuscript" / "00_abstract.md"
    original = path.read_text(encoding="utf-8")
    stat = path.stat()
    try:
        path.write_text(original + "\n{{not_a_registered_token}}\n", encoding="utf-8")
        checks = validate_manuscript(project_root, only={"manuscript_tokens_registered"})
        assert checks["manuscript_tokens_registered"] is False
    finally:
        # Restore bytes AND mtime: a newer-looking composed file makes saved
        # staleness reports look stale and poisons later tests (same class as
        # the test_semantic_sheaf isolation defect).
        path.write_text(original, encoding="utf-8")
        os.utime(path, (stat.st_atime, stat.st_mtime))


def test_validate_manuscript_citation_keys_resolved_negative(project_root: Path) -> None:
    from manuscript.sheaf.cli import run_compose_cli

    path = project_root / "manuscript" / "sections" / "imrad" / "methods_sheaf" / "prose.md"
    original = path.read_text(encoding="utf-8")
    stat = path.stat()
    try:
        path.write_text(original + "\n\nBroken citation negative control [@not_a_real_bibkey].\n", encoding="utf-8")
        checks = validate_manuscript(project_root, only={"citation_keys_resolved"})
        assert checks["citation_keys_resolved"] is False
        assert run_compose_cli(["--validate-only", "--strict"], project_root=project_root) == 1
    finally:
        # Restore bytes AND mtime: a newer-looking composed file makes saved
        # staleness reports look stale and poisons later tests (same class as
        # the test_semantic_sheaf isolation defect).
        path.write_text(original, encoding="utf-8")
        os.utime(path, (stat.st_atime, stat.st_mtime))


def test_validate_manuscript_duplicate_track_marker_negative(project_root: Path) -> None:
    """A composed section with a doubled sheaf-track marker must fail the gate."""
    from manuscript.sheaf import compose_all_sections

    path = project_root / "manuscript" / "07_methods_lean.md"
    if not path.is_file():
        compose_all_sections(project_root)
    original = path.read_text(encoding="utf-8")
    stat = path.stat()
    marker = "<!-- sheaf-track:lean -->"
    assert marker in original
    try:
        # Plant a second standalone copy of an already-present marker (the stutter bug).
        path.write_text(original.replace(marker, marker + "\n\n" + marker, 1), encoding="utf-8")
        checks = validate_manuscript(project_root, only={"no_duplicate_sheaf_track_markers"})
        assert checks["no_duplicate_sheaf_track_markers"] is False
    finally:
        # Restore bytes AND mtime: a newer-looking composed file makes saved
        # staleness reports look stale and poisons later tests (same class as
        # the test_semantic_sheaf isolation defect).
        path.write_text(original, encoding="utf-8")
        os.utime(path, (stat.st_atime, stat.st_mtime))


def test_manuscript_review_citation_keys_and_overclaim_guards(project_root: Path) -> None:
    """Review-added sources must be cited, and stale overclaims must stay out."""
    source_paths = [
        project_root / "manuscript" / "00_abstract.md",
        project_root / "manuscript" / "17_conclusion.md",
        *sorted((project_root / "manuscript" / "sections" / "imrad").glob("*/prose.md")),
    ]
    rendered_paths = sorted((project_root / "output" / "manuscript").glob("*.md"))
    text = "\n".join(path.read_text(encoding="utf-8") for path in [*source_paths, *rendered_paths] if path.is_file())

    for key in (
        "snell2022context_distillation",
        "ye2026context_distillation",
        "lazaridis2026edge_opd",
        "ke2019f_divergence_imitation",
        "hernandezlobato2016blackbox_alpha",
        "shrivastava2021mi_kd",
        "li2026rethinking_opd",
        "luo2026demystifying_opd",
        "han2026adaptive_teacher_exposure",
        "chen2026freshness_opd",
        "zhong2026sod",
        "zhang2026opsdl",
        "fellows2018virel",
        "vanoostrum2024discrete_active_inference",
        "tian2026vicur",
        "liu2026visual_advantage_opd",
    ):
        assert f"@{key}" in text

    for forbidden in (
        "reverse KL is mode-seeking",
        "the privileged advantage predicted by the Markov-blanket asymmetry",
        "Monotone descent is the falsifiable signature here",
        "Markov-blanket asymmetry in this toy system",
        "solid and dashed",
        "Reproduced from [@fig:ising_mi_curve]",
    ):
        assert forbidden not in text
