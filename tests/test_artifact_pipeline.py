"""Real cold-root and fixed-point artifact producer regressions."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from PIL import Image

from artifact_fixtures import stage_source_project
from firstprinciples import precision_ledger, si_bridge
from manuscript.sheaf.semantic import validate_semantic_gluing
from ontology.bindings import GRAPH_WORLD_EXPECTED_TERMS, resolve_model_ontology_path
from orchestration.artifact_pipeline import hydrate_manuscript_fixed_point, refresh_gate_artifacts
from orchestration.artifact_lock import artifact_lease
from roadmap_tracks import validate_integration_audit_artifacts, validate_sheaf_track_artifacts
from roadmap_tracks.integration_audit import validate_manuscript_staleness_report

pytestmark = [pytest.mark.requires_pymdp, pytest.mark.render_slow, pytest.mark.timeout(1800)]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def cold_production(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Path]]:
    root = stage_source_project(
        Path(__file__).resolve().parents[1],
        tmp_path_factory.mktemp("cold-artifact-pipeline") / "project",
    )
    assert not (root / "output").exists()
    return root, refresh_gate_artifacts(root)


def test_full_pipeline_produces_current_cold_inputs_and_real_figures_without_receipts(
    cold_production: tuple[Path, dict[str, Path]],
) -> None:
    root, paths = cold_production
    fp = root / "output" / "data" / "firstprinciples"
    assert si_bridge.validate_payload(_load(fp / "si_bridge_demo.json")) == []
    assert precision_ledger.validate_against_sources(root, _load(fp / "precision_ledger_demo.json")) == []
    measured = _load(fp / "classroom.json")
    statistics = _load(fp / "statistics_demo.json")
    assert statistics["teacher_entropy"] == measured["teacher_belief_entropies"]
    assert statistics["student_entropy"] == measured["student_belief_entropies"]
    assert _load(fp / "privilege_sweep.json")["levels"]
    figures = [
        path for key, path in paths.items()
        if key.startswith("figure:") and path.suffix == ".png"
    ]
    assert figures
    assert all(path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for path in figures)

    assert validate_integration_audit_artifacts(root, require_release_evidence=False) == []
    assert validate_integration_audit_artifacts(root)
    assert validate_manuscript_staleness_report(root) == []
    assert validate_sheaf_track_artifacts(root, require_observations=False) == []
    assert validate_semantic_gluing(root, require_observations=False) == []
    # A structurally complete cold surface cannot invent execution receipts.
    assert validate_sheaf_track_artifacts(root)
    assert validate_semantic_gluing(root)


def test_fixed_point_refreshes_real_figure_source_currency(
    cold_production: tuple[Path, dict[str, Path]], tmp_path: Path,
) -> None:
    produced_root, paths = cold_production
    root = tmp_path / "project"
    shutil.copytree(produced_root, root)
    relative_figure = next(
        path.relative_to(produced_root) for key, path in paths.items()
        if key.startswith("figure:") and path.suffix == ".png"
    )
    figure = root / relative_figure
    source_map = root / "output" / "data" / "figure_source_map.json"
    old_row = next(
        row for row in _load(source_map)["rows"] if row["output"] == relative_figure.as_posix()
    )
    with Image.open(figure) as image:
        new_width = image.width + 1
        with image.resize((new_width, image.height)) as resized:
            resized.save(figure)
    assert old_row["image_width_px"] != new_width
    assert validate_integration_audit_artifacts(root, require_release_evidence=False)

    with artifact_lease(root) as lease:
        handoff = lease.handoff()
        completed = subprocess.run(
            [sys.executable, str(root / "scripts" / "z_generate_manuscript_variables.py")],
            cwd=root,
            env=handoff.env,
            pass_fds=handoff.pass_fds,
            capture_output=True,
            text=True,
            timeout=180,
        )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    current_row = next(
        row for row in _load(source_map)["rows"] if row["output"] == relative_figure.as_posix()
    )
    assert current_row["image_width_px"] == new_width

    assert validate_integration_audit_artifacts(root, require_release_evidence=False) == []
    assert validate_integration_audit_artifacts(root)
    assert validate_manuscript_staleness_report(root) == []
    assert validate_semantic_gluing(root, require_observations=False) == []
    assert validate_semantic_gluing(root)


def test_structural_fixed_point_does_not_exempt_non_observation_failures(
    cold_production: tuple[Path, dict[str, Path]], tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    shutil.copytree(cold_production[0], root)
    ontology_path = resolve_model_ontology_path(root, "graph_world")
    ontology = yaml.safe_load(ontology_path.read_text(encoding="utf-8"))
    terms = ontology.get("terms", ontology)
    terms[next(iter(GRAPH_WORLD_EXPECTED_TERMS))] = "not-the-declared-model-term"
    ontology_path.write_text(yaml.safe_dump(ontology, sort_keys=False), encoding="utf-8")

    with pytest.raises(RuntimeError):
        hydrate_manuscript_fixed_point(root, max_passes=2)

    assert validate_semantic_gluing(root, require_observations=False)
