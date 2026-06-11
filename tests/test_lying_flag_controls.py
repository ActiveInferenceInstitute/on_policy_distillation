"""Negative controls for the 9 remediated class-(c) lying-flag gaps.

A "lying flag" is a stored ``all_*`` aggregate boolean set ``True`` while a
nested row that the aggregate summarizes is corrupted. Before this remediation,
the validators only re-read the top-level flag, so a flipped aggregate survived
end-to-end. Each test here keeps the stored flag ``True``, corrupts exactly one
nested row, and asserts the now-row-re-deriving validator (or its helper)
FAILS. Every test also asserts the UNCORRUPTED real artifact passes first, so a
vacuous always-fail re-derivation would be caught.

No mocks, real data: artifacts are loaded from the live ``project_root`` tree,
corrupted in memory or in an isolated ``tmp_path`` copy, and fed to the real
validators. Source of the 9 gaps: Forge cross-vendor audit
``MEMORY/WORK/20260610-aiopd-xvendor-flags``.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from gates.output_checks import (
    _si_efe_rows_explained,
    _si_invariants_all_pass_ok,
    validate_outputs,
)
from roadmap_tracks.sheaf_track_validation import (
    load_sheaf_track_payloads,
    validate_sheaf_track_payloads,
)
from roadmap_tracks.toy_sweep import validate_toy_sweep_artifacts


def _sheaf_issues(project_root: Path, mutate) -> list[str]:
    """Load live sheaf-track payloads, apply ``mutate``, return validator issues.

    Certificate validation is disabled so the test exercises the row-level
    re-derivation rather than a saved-certificate short circuit; this mirrors
    ``validate_sheaf_track_payloads``'s documented negative-control use.
    """
    payloads = load_sheaf_track_payloads(project_root.resolve())
    mutate(payloads)
    return validate_sheaf_track_payloads(
        project_root.resolve(), payloads, validate_saved_certificate=False
    )


# --- Flag 1: si_invariants.json :: all_pass --------------------------------


def test_flag1_si_invariants_all_pass_honest_passes(project_root: Path) -> None:
    payload = json.loads(
        (project_root / "output" / "reports" / "si_invariants.json").read_text(encoding="utf-8")
    )
    assert _si_invariants_all_pass_ok(payload) is True


def test_flag1_si_invariants_all_pass_lying_flag_dies(project_root: Path, tmp_path: Path) -> None:
    # Helper-level: a false invariant value cannot be hidden behind all_pass=True.
    liar = {"invariants": {"goal_reached": False, "belief_entropy_finite": True}, "all_pass": True}
    assert _si_invariants_all_pass_ok(liar) is False

    # Validator-level: validate_outputs's si_invariants_all_pass check must fail.
    proj = tmp_path / "proj"
    shutil.copytree(project_root / "output", proj / "output")
    si_path = proj / "output" / "reports" / "si_invariants.json"
    payload = json.loads(si_path.read_text(encoding="utf-8"))
    payload["invariants"]["goal_reached"] = False
    payload["all_pass"] = True  # the lie
    si_path.write_text(json.dumps(payload), encoding="utf-8")
    checks = validate_outputs(proj, only={"si_invariants_all_pass"})
    assert checks.get("si_invariants_all_pass") is False


# --- Flag 2: si_policy_comparison.json :: summary.all_efe_rows_explained ----


def test_flag2_efe_rows_explained_honest_passes(project_root: Path) -> None:
    comparison = json.loads(
        (project_root / "output" / "data" / "si_policy_comparison.json").read_text(encoding="utf-8")
    )
    assert _si_efe_rows_explained(comparison) is True
    # And the stored summary flag agrees with the honest re-derivation.
    assert (comparison.get("summary") or {}).get("all_efe_rows_explained") is True


def test_flag2_efe_rows_explained_lying_flag_dies(project_root: Path) -> None:
    comparison = json.loads(
        (project_root / "output" / "data" / "si_policy_comparison.json").read_text(encoding="utf-8")
    )
    # Corrupt one posterior step: unavailable AND no fallback reason.
    step = comparison["runs"][0]["policy_posterior_steps"][0]
    step["posterior_available"] = False
    step["fallback_reason"] = ""
    comparison["summary"]["all_efe_rows_explained"] = True  # the lie
    # The consumer re-derivation (output_checks.py:435) uses this helper; it must
    # now disagree with the lying summary flag.
    assert _si_efe_rows_explained(comparison) is False


# --- Flag 3: toy_benchmark_matrix.json :: all_models_complete --------------


def test_flag3_models_complete_honest_passes(project_root: Path) -> None:
    assert validate_toy_sweep_artifacts(project_root.resolve()) == []


def test_flag3_models_complete_lying_flag_dies(project_root: Path, tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    shutil.copytree(project_root / "output", proj / "output")
    path = proj / "output" / "data" / "toy_benchmark_matrix.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["rows"][0]["gate_passed"] = False  # a model row is not actually complete
    payload["all_models_complete"] = True  # the lie
    path.write_text(json.dumps(payload), encoding="utf-8")
    issues = validate_toy_sweep_artifacts(proj)
    assert any("toy_benchmark_matrix.json has incomplete model rows" in i for i in issues)


# --- Flag 4: sheaf_section_status_matrix.json :: all_bound_fragments_present -


def test_flag4_bound_fragments_honest_passes(project_root: Path) -> None:
    assert _sheaf_issues(project_root, lambda _p: None) == []


def test_flag4_bound_fragments_lying_flag_dies(project_root: Path) -> None:
    def mutate(p: dict) -> None:
        cells = p["section_status"]["cells"]
        # Pick a required (non-optional) bound cell that is currently NOT missing
        # so flipping it to "missing" actually raises missing_required_count.
        idx = next(
            i
            for i, c in enumerate(cells)
            if c.get("bound") and c.get("coverage_status") != "missing" and not c.get("optional")
        )
        cells[idx]["coverage_status"] = "missing"
        p["section_status"]["all_bound_fragments_present"] = True  # the lie

    issues = _sheaf_issues(project_root, mutate)
    assert any("sheaf_section_status_matrix.json has missing bound fragments" in i for i in issues)


# --- Flag 5: sheaf_section_status_matrix.json :: all_sections_have_status ----


def test_flag5_sections_have_status_lying_flag_dies(project_root: Path) -> None:
    def mutate(p: dict) -> None:
        p["section_status"]["sections"][0]["status"] = ""
        p["section_status"]["all_sections_have_status"] = True  # the lie

    issues = _sheaf_issues(project_root, mutate)
    assert any("sheaf_section_status_matrix.json has incomplete status rows" in i for i in issues)


# --- Flag 6: sheaf_section_status_matrix.json :: all_tracks_have_status ------


def test_flag6_tracks_have_status_lying_flag_dies(project_root: Path) -> None:
    def mutate(p: dict) -> None:
        p["section_status"]["tracks"][0]["status"] = ""
        p["section_status"]["all_tracks_have_status"] = True  # the lie

    issues = _sheaf_issues(project_root, mutate)
    assert any("sheaf_section_status_matrix.json has incomplete status rows" in i for i in issues)


# --- Flag 7: sheaf_render_log.json :: all_events_ok -------------------------


def test_flag7_events_ok_honest_passes(project_root: Path) -> None:
    # render_log lives in the same payload set; the no-op mutation re-confirms green.
    assert _sheaf_issues(project_root, lambda _p: None) == []


def test_flag7_events_ok_lying_flag_dies(project_root: Path) -> None:
    def mutate(p: dict) -> None:
        p["render_log"]["events"][0]["status"] = "failed"
        p["render_log"]["all_events_ok"] = True  # the lie

    issues = _sheaf_issues(project_root, mutate)
    assert any("sheaf_render_log.json has failed render events" in i for i in issues)


# --- Flag 8: replay_matrix.json :: all_configured_producers_represented -----


def test_flag8_producers_represented_lying_flag_dies(project_root: Path) -> None:
    def mutate(p: dict) -> None:
        rows = p["replay_matrix"]["rows"]
        # Duplicate row[1]'s producer onto row[0]: the producer set no longer
        # equals configured_scripts, so coverage is genuinely incomplete.
        rows[0]["producer_script"] = rows[1]["producer_script"]
        p["replay_matrix"]["all_configured_producers_represented"] = True  # the lie

    issues = _sheaf_issues(project_root, mutate)
    assert any(
        "replay_matrix.json does not represent every configured producer" in i for i in issues
    )


# --- Flag 9: track_improvement_scope.json :: all_live_tracks_valid ----------


def test_flag9_live_tracks_valid_lying_flag_dies(project_root: Path) -> None:
    def mutate(p: dict) -> None:
        p["track_improvement_scope"]["promotion_matrix"][0]["promotion_complete"] = False
        p["track_improvement_scope"]["all_live_tracks_valid"] = True  # the lie

    issues = _sheaf_issues(project_root, mutate)
    assert any(
        "track_improvement_scope.json has incomplete live-track promotion rows" in i for i in issues
    )
