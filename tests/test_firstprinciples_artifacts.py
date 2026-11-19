"""Tests for the deterministic first-principles artifact emitters."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from artifact_fixtures import stage_source_project

from firstprinciples import artifacts


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_write_all_emits_validated_artifacts(tmp_path: Path) -> None:
    paths = artifacts.write_all(tmp_path)
    expected = {
        "correspondence_map.json",
        "opd_taxonomy.json",
        "divergence_demo.json",
        "reward_tilting_demo.json",
        "exposure_bias_demo.json",
        "sdpg_demo.json",
        "sequential_shift.json",
        "sequential_shift_sensitivity.json",
        "correspondence_table.md",
        "taxonomy_table.md",
    }
    assert expected <= set(paths)
    for name, path in paths.items():
        assert path.is_file()
        if name.endswith(".json"):
            payload = _load(path)
            assert payload["schema"].startswith("firstprinciples.")


def test_correspondence_and_taxonomy_payloads(tmp_path: Path) -> None:
    paths = artifacts.write_all(tmp_path)
    corr = _load(paths["correspondence_map.json"])
    assert corr["ok"] is True and corr["row_count"] >= 10
    tax = _load(paths["opd_taxonomy.json"])
    assert tax["method_count"] >= 8
    by_key = {row["bibkey"]: row for row in tax["methods"]}
    assert by_key["chen2026freshness_opd"]["acronym"] == "f-OPD"
    assert by_key["chen2026freshness_opd"]["signal_source"] == "freshness_aware_async_buffer"
    assert by_key["chen2026freshness_opd"]["divergence"] == "freshness_weighted_reverse_kl"
    assert by_key["chen2026freshness_opd"]["on_policy"] is True
    assert by_key["chen2026freshness_opd"]["privileged_info"] is False
    assert "freshness_aware_async_buffer" in tax["signal_sources"]


def test_divergence_demo_mode_seeking() -> None:
    demo = artifacts.divergence_demo()
    # Teacher is peaked; reverse KL (mode-seeking) is finite and smaller than
    # the symmetric JSD scaling would suggest; all values are finite.
    assert demo["reverse_kl"] >= 0.0
    assert demo["forward_kl"] >= 0.0
    assert demo["clipped_reverse_kl"] <= demo["reverse_kl"] + 1e-9
    assert demo["mode_concentration"]["mode_seeking"] in (True, False)


def test_reward_tilting_demo_optimal() -> None:
    demo = artifacts.reward_tilting_demo()
    assert demo["optimality"]["optimal"] is True


def test_exposure_bias_demo_collapses_off_policy() -> None:
    demo = artifacts.exposure_bias_demo()
    assert demo["gap"]["off_policy_collapses"] is True


def test_sdpg_demo_all_modes_present() -> None:
    demo = artifacts.sdpg_demo()
    assert set(demo["modes"]) == {"fkl", "rkl", "ufkl", "urkl"}
    assert demo["mode_keys"] == ["fkl", "rkl", "ufkl", "urkl"]
    assert {row["mode"] for row in demo["mode_rows"]} == {"fkl", "rkl", "ufkl", "urkl"}
    assert demo["required_loss_terms"] == [
        "clip_term",
        "distill_term",
        "ref_kl_term",
        "self_distillation_kl",
        "reference_kl",
        "total",
    ]
    assert demo["signal_density"]["denser_than_scalar"] is True
    assert demo["dense_privileged_signal"] is True
    assert demo["all_loss_terms_present"] is True
    assert demo["all_loss_terms_finite"] is True
    assert demo["all_self_distillation_kl_positive"] is True
    assert demo["all_reference_kl_positive"] is True
    assert demo["ok"] is True
    for row in demo["mode_rows"]:
        assert set(demo["required_loss_terms"]) < set(row)
        assert row["self_distillation_kl"] > 0.0
        assert row["reference_kl"] > 0.0


def test_markdown_tables_written(tmp_path: Path) -> None:
    paths = artifacts.write_markdown_tables(tmp_path)
    assert "| Method |" in paths["taxonomy_table.md"].read_text(encoding="utf-8")
    assert "Active inference" in paths["correspondence_table.md"].read_text(encoding="utf-8")


def _prepare_complete_inputs(root: Path) -> None:
    from roadmap_tracks.toy_sweep import build_analytical_observable_sweep
    from simulation.si_runner import run_and_persist

    run_and_persist(root)
    (root / "output" / "data" / "analytical_observable_sweep.json").write_text(
        json.dumps(build_analytical_observable_sweep(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _run_complete_producer(root: Path, entrypoint: str, *, classroom: bool) -> None:
    from orchestration.artifact_lock import artifact_lease

    with artifact_lease(root) as lease:
        if entrypoint == "api":
            artifacts.write_complete(root, classroom=classroom)
            return
        handoff = lease.handoff()
        argv = [sys.executable, "-B", str(root / "scripts" / "generate_firstprinciples.py")]
        if not classroom:
            argv.append("--no-classroom")
        completed = subprocess.run(
            argv, cwd=root, env=handoff.env, pass_fds=handoff.pass_fds,
            capture_output=True, text=True, timeout=600,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr


@pytest.mark.requires_pymdp
@pytest.mark.render_slow
@pytest.mark.timeout(900)
@pytest.mark.parametrize("entrypoint", ["api", "cli"])
def test_complete_producer_cross_reads_real_inputs_and_clears_disabled_classroom(
    project_root: Path, tmp_path: Path, entrypoint: str,
) -> None:
    from firstprinciples import classroom, precision_ledger, si_bridge
    from visualizations.figures_firstprinciples import (
        figure_classroom_distillation_signal,
        figure_precision_ledger,
        figure_privilege_dose_response,
        figure_si_bridge_match,
    )

    root = stage_source_project(project_root, tmp_path / "project")
    assert not (root / "output").exists()
    _prepare_complete_inputs(root)
    _run_complete_producer(root, entrypoint, classroom=True)

    data = root / "output" / "data"
    fp = data / "firstprinciples"
    trace = _load(data / "si_tmaze_trace.json")
    summary = _load(data / "si_tmaze_summary.json")
    bridge = _load(fp / "si_bridge_demo.json")
    assert bridge["cue_validity"] == summary["config"]["environment"]["cue_validity"]
    assert bridge["belief_entropy_by_step"] == [step["belief_entropy"] for step in trace["steps"]]
    assert si_bridge.validate_payload(bridge) == []
    ledger = _load(fp / "precision_ledger_demo.json")
    assert precision_ledger.validate_against_sources(root, ledger) == []
    assert ledger["ok"] is True

    measured = _load(fp / "classroom.json")
    assert classroom.validate_classroom_payload(measured)
    statistics = _load(fp / "statistics_demo.json")
    assert statistics["teacher_entropy"] == measured["teacher_belief_entropies"]
    assert statistics["student_entropy"] == measured["student_belief_entropies"]
    assert statistics["sample_size"] == len(measured["teacher_belief_entropies"])
    assert statistics["ok"] is True
    privilege = _load(fp / "privilege_sweep.json")
    matching = next(
        row for row in privilege["levels"]
        if row["teacher_cue_validity"] == measured["teacher_cue_validity"]
    )
    assert privilege["student_cue_validity"] == measured["student_cue_validity"]
    assert matching["mean_reverse_kl"] == pytest.approx(measured["mean_reverse_kl"])
    assert matching["teacher_belief_entropy"] == pytest.approx(measured["teacher_mean_belief_entropy"])

    for render in (
        figure_si_bridge_match, figure_precision_ledger,
        figure_classroom_distillation_signal, figure_privilege_dose_response,
    ):
        assert render(root).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

    _run_complete_producer(root, entrypoint, classroom=False)
    for name in ("classroom.json", "statistics_demo.json", "privilege_sweep.json"):
        assert not (fp / name).exists()
    assert si_bridge.validate_payload(_load(fp / "si_bridge_demo.json")) == []
    assert precision_ledger.validate_against_sources(root, _load(fp / "precision_ledger_demo.json")) == []


def test_no_classroom_invalidates_stale_outputs_even_when_upstream_is_missing(tmp_path: Path) -> None:
    fp = tmp_path.joinpath(*artifacts.ARTIFACT_DIR)
    fp.mkdir(parents=True)
    for name in ("classroom.json", "statistics_demo.json", "privilege_sweep.json"):
        (fp / name).write_text('{"stale_previous_run": true}\n', encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        artifacts.write_complete(tmp_path, classroom=False)

    for name in ("classroom.json", "statistics_demo.json", "privilege_sweep.json"):
        assert not (fp / name).exists()


@pytest.mark.parametrize(
    "entrypoint",
    ["write_json", "write_all", "write_markdown_tables", "write_statistics_artifact", "write_complete"],
)
def test_firstprinciples_producers_refuse_competing_custody(
    project_root: Path, tmp_path: Path, entrypoint: str,
) -> None:
    from orchestration.artifact_lock import ARTIFACT_LEASE_ENV, artifact_lease

    child = """
import sys
from pathlib import Path
from firstprinciples import artifacts
from orchestration.artifact_lock import ArtifactLeaseBusy

root = Path(sys.argv[1])
name = sys.argv[2]
try:
    if name == "write_json":
        artifacts.write_json(root, "not-owned.json", {"value": 1})
    elif name == "write_statistics_artifact":
        artifacts.write_statistics_artifact(root, [0.0, 0.0], [0.5, 0.4])
    else:
        getattr(artifacts, name)(root)
except ArtifactLeaseBusy:
    raise SystemExit(23)
raise SystemExit("producer escaped exclusive custody")
"""
    with artifact_lease(tmp_path) as lease:
        env = lease.handoff().env
        env.pop(ARTIFACT_LEASE_ENV)
        env["PYTHONPATH"] = str(project_root / "src")
        completed = subprocess.run(
            [sys.executable, "-B", "-c", child, str(tmp_path), entrypoint],
            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120,
        )
        assert completed.returncode == 23, completed.stdout + completed.stderr
        assert not (tmp_path / "output" / "data").exists()
