from pathlib import Path

import pytest
import yaml

from gates.validation import validate_manuscript
from manuscript.sheaf import (
    SheafManifest,
    SheafSection,
    build_coverage_matrix,
    compose_all_sections,
    load_manifest,
    load_track_registry,
    validate_coverage_strict,
    validate_manifest,
)
from gate_support import ensure_gate_artifacts


def test_manifest_loads_imrad_sections() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(root / "docs" / "manuscript" / "sheaf" / "manifest.yaml")
    assert [section.order for section in manifest.sections] == sorted(section.order for section in manifest.sections)
    assert len({section.id for section in manifest.sections}) == len(manifest.sections)
    assert manifest.sections[0].id == "intro"
    assert manifest.sections[0].kind == "group"
    appendix = next(s for s in manifest.sections if s.id == "appendix_full_sheaf")
    registry = load_track_registry(root / manifest.registry_path)
    assert set(appendix.tracks) < set(registry.tracks)
    assert all(set(section.tracks).issubset(registry.tracks) for section in manifest.sections)
    assert all(section.kind == "section" for section in manifest.sections if section.should_compose())
    groups = [section for section in manifest.sections if section.kind == "group"]
    assert {section.imrad for section in groups} == {"introduction", "methods", "results", "discussion", "appendix"}
    assert all(not section.should_compose() for section in groups)


def test_canonical_ontology_placement_preserves_strict_composition_laws() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(root / "docs" / "manuscript" / "sheaf" / "manifest.yaml", project_root=root)
    registry = load_track_registry(root / manifest.registry_path)
    assert validate_manifest(manifest, root, registry=registry, strict_coverage=True) == []


@pytest.mark.parametrize("track", ["ontology", "prose"])
def test_manifest_and_promotion_reject_duplicate_binding_keys(tmp_path: Path, track: str) -> None:
    from manuscript.sheaf.manifest import load_manifest_data
    from roadmap_tracks.sheaf_tracks_support import _bound_tracks, _manifest_sections

    path = tmp_path / "docs" / "manuscript" / "sheaf" / "manifest.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(
        "sections:\n"
        "  - id: demo\n"
        "    title: Demo\n"
        "    order: 1\n"
        "    tracks:\n"
        f"      {track}: first.yaml\n"
        f"      {track}: second.yaml\n",
        encoding="utf-8",
    )
    for reader in (
        lambda: load_manifest(path, project_root=tmp_path),
        lambda: load_manifest_data(path),
        lambda: _manifest_sections(tmp_path),
        lambda: _bound_tracks(tmp_path),
    ):
        with pytest.raises(yaml.YAMLError, match=f"duplicate key '{track}'"):
            reader()


def test_manifest_projection_cannot_mutate_cached_bindings(tmp_path: Path) -> None:
    from manuscript.sheaf.manifest import load_manifest_data

    path = tmp_path / "manifest.yaml"
    path.write_text(
        "sections:\n"
        "  - id: demo\n"
        "    title: Demo\n"
        "    order: 1\n"
        "    tracks:\n"
        "      ontology: selected.yaml\n",
        encoding="utf-8",
    )
    projected = load_manifest_data(path)
    projected["sections"][0]["tracks"]["ontology"] = "not-selected.yaml"
    assert load_manifest_data(path)["sections"][0]["tracks"]["ontology"] == "selected.yaml"
    assert load_manifest(path).sections[0].tracks["ontology"] == "selected.yaml"


def test_all_composed_sections_bind_prose() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(root / "docs" / "manuscript" / "sheaf" / "manifest.yaml")
    missing = [
        section.id
        for section in manifest.sections
        if section.should_compose() and "prose" not in section.tracks
    ]
    assert missing == []


def test_validate_manifest_reports_missing_file(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    broken = tmp_path / "docs" / "manuscript" / "sheaf" / "manifest.yaml"
    broken.parent.mkdir(parents=True)
    broken.write_text(
        """
defaults:
  missing_track: error
sections:
  - id: broken
    order: 1
    title: Broken
    tracks:
      prose: docs/manuscript/sections/does_not_exist.md
""",
        encoding="utf-8",
    )
    broken_manifest = load_manifest(broken, project_root=root)
    issues = validate_manifest(broken_manifest, root)
    assert any(i.code == "missing_track_file" for i in issues)


def test_validate_manifest_duplicate_and_unknown_tracks(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        """
sections:
  - id: dup
    order: 1
    title: One
    tracks:
      prose: docs/manuscript/sections/preliminaries/prose.md
  - id: dup
    order: 2
    title: Two
    tracks:
      not_registered: docs/manuscript/sections/preliminaries/prose.md
      prose: docs/manuscript/sections/preliminaries/prose.md
    track_order: [prose, ghost]
""",
        encoding="utf-8",
    )
    manifest = load_manifest(manifest_path, project_root=root)
    issues = validate_manifest(manifest, root)
    assert any(i.code == "duplicate_section_id" for i in issues)
    assert any(i.code == "unknown_track" for i in issues)
    assert any(i.code == "track_order_unbound" for i in issues)


def test_validate_manifest_requires_prose_for_composed_sections(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        """
sections:
  - id: no_prose
    order: 1
    title: No prose
    tracks:
      formalism: docs/manuscript/sections/imrad/methods_analytical/formalism.md
""",
        encoding="utf-8",
    )
    manifest = load_manifest(manifest_path, project_root=root)
    registry = load_track_registry(root / "docs" / "manuscript" / "sheaf" / "tracks.yaml")

    issues = validate_manifest(manifest, root, registry=registry)

    assert any(i.code == "missing_prose_track" for i in issues)


def test_validate_manifest_unknown_renderer(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    registry_path = tmp_path / "tracks.yaml"
    registry_path.write_text(
        """
tracks:
  prose:
    order: 1
    renderer: not_implemented
renderers:
  not_implemented:
    suffixes: [".md"]
""",
        encoding="utf-8",
    )
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        """
sections:
  - id: s
    order: 1
    title: S
    tracks:
      prose: docs/manuscript/sections/preliminaries/prose.md
""",
        encoding="utf-8",
    )
    manifest = load_manifest(manifest_path, project_root=root)
    manifest = SheafManifest(
        defaults=manifest.defaults,
        sections=manifest.sections,
        registry_path=Path("tracks.yaml"),
    )
    issues = validate_manifest(
        manifest,
        root,
        registry=load_track_registry(registry_path),
    )
    assert any(i.code == "unknown_renderer" for i in issues)


def test_strict_validate_fails_on_gray(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(root / "docs" / "manuscript" / "sheaf" / "manifest.yaml")
    registry = load_track_registry(root / "docs" / "manuscript" / "sheaf" / "tracks.yaml")
    broken_section = SheafSection(
        id="broken_gray",
        title="Broken",
        short="b",
        order=99,
        tracks={"prose": "docs/manuscript/sections/does_not_exist.md"},
        output_name="99_broken.md",
    )
    broken_manifest = SheafManifest(
        defaults=manifest.defaults,
        sections=manifest.sections + (broken_section,),
        registry_path=manifest.registry_path,
    )
    matrix = build_coverage_matrix(registry, broken_manifest, root)
    issues = validate_coverage_strict(matrix)
    assert any(i.code == "coverage_missing" for i in issues)
    validation = validate_manifest(broken_manifest, root, registry=registry, strict_coverage=True)
    assert any(i.code == "coverage_missing" for i in validation)


@pytest.mark.render_slow
def test_group_rows_skip_compose(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    result = compose_all_sections(root, manuscript_dir=tmp_path / "docs" / "manuscript")
    names = {p.name for p in result.paths}
    assert "_group_intro.md" not in names
    assert "02_intro_motivation.md" in names


@pytest.mark.artifact_slow
def test_validate_manuscript_strict_coverage() -> None:
    from gate_support import _gate_artifacts_ready

    root = Path(__file__).resolve().parents[1]
    ensure_gate_artifacts(root, verify=True)
    checks = validate_manuscript(root)
    assert checks["sheaf_valid"]
    assert checks["coverage_matrix_valid"]
    assert checks["full_sheaf_appendix_tracks"]
    assert checks["imrad_groups_present"]
    # Structural readiness neither invents observations nor requires authentic
    # existing observations to remain absent. Cold-root tests cover rejection.
    assert _gate_artifacts_ready(root, include_manuscript=True)
    assert checks["methods_sheaf_layers"]
    assert checks["manuscript_tokens_registered"]
    assert checks["resolved_manuscript_hydrated"]
