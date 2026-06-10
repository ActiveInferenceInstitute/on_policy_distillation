"""Contract tests for the convergent chain runner and chunked test runner.

No mocks: every check runs the real script as a subprocess (CLI policy) or
inspects its real plan output against the declared configuration.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / script), *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_run_full_chain_help_exits_zero() -> None:
    proc = _run("run_full_chain.py", "--help")
    assert proc.returncode == 0
    assert "convergent" in proc.stdout.lower() or "converge" in proc.stdout.lower()


def test_run_full_chain_dry_run_plan_matches_config() -> None:
    """The plan is read from manuscript/config.yaml, never hard-coded."""
    proc = _run("run_full_chain.py", "--dry-run")
    assert proc.returncode == 0
    plan = [line for line in proc.stdout.splitlines() if line and not line.startswith("#")]
    config = yaml.safe_load((PROJECT_ROOT / "manuscript" / "config.yaml").read_text(encoding="utf-8"))
    declared = list(config["analysis"]["scripts"])
    assert plan[: len(declared)] == declared
    assert plan[len(declared)] == "validate_outputs.py"


def test_run_full_chain_tail_only_plan() -> None:
    proc = _run("run_full_chain.py", "--tail-only", "--dry-run")
    assert proc.returncode == 0
    plan = [line for line in proc.stdout.splitlines() if line and not line.startswith("#")]
    assert plan[0] == "generate_validation_spine.py"
    assert plan[-1] == "validate_outputs.py"
    assert "generate_sheaf_tracks.py" in plan
    # Sheaf tracks must precede variable hydration (attestation fixed point).
    assert plan.index("generate_sheaf_tracks.py") < plan.index("z_generate_manuscript_variables.py")


def test_run_tests_chunked_help_and_chunking() -> None:
    proc = _run("run_tests_chunked.py", "--help")
    assert proc.returncode == 0
    assert "chunk" in proc.stdout.lower()

    # Real chunk collection over the real tests directory: every test file is
    # covered exactly once and ordering is deterministic.
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    try:
        from run_tests_chunked import collect_chunks  # noqa: PLC0415

        chunks = collect_chunks(PROJECT_ROOT, 6)
    finally:
        sys.path.pop(0)
    flat = [f for chunk in chunks for f in chunk]
    expected = sorted(
        str(p.relative_to(PROJECT_ROOT)) for p in (PROJECT_ROOT / "tests").glob("test_*.py")
    )
    assert [f for f in flat if f != "tests/gates"] == expected
    assert all(len(chunk) <= 6 for chunk in chunks)


import json

import pytest


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
@pytest.mark.timeout(1800)
def test_run_full_chain_convergence_loop_actually_executes() -> None:
    """Pin 4 (advisor): the convergence loop body must be exercised, not dead code.

    Stale the attestation's pinned report hash (a real mid-convergence state),
    then require the runner to (a) report at least one convergence pass and
    (b) finish green. Restores nothing by hand — the tail rebuild IS the
    restoration.
    """
    attestation_path = PROJECT_ROOT / "output" / "reports" / "release_attestation.json"
    report_path = PROJECT_ROOT / "output" / "reports" / "validation_report.json"
    if not (attestation_path.is_file() and report_path.is_file()):
        pytest.skip("chain artifacts not present; run the chain first")
    # Perturbation that the pre-validate tail CANNOT self-heal: a saved report
    # claiming a non-fixed-point failure. The tail's attestation must reject it
    # (carve-out does not admit it), the first validate goes red, and only the
    # convergence pass — attesting the freshly written honest report — heals it.
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["failed_checks"] = sorted(set(report.get("failed_checks") or []) | {"a_genuinely_red_science_check"})
    report["all_passed"] = False
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "run_full_chain.py"), "--tail-only", "--max-passes", "3"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=1700,
    )
    assert proc.returncode == 0, proc.stdout[-2000:]
    assert "convergence pass 1" in proc.stdout, proc.stdout[-1500:]  # the loop body ran
    # Final state must be green and hash-current again.
    final = json.loads(attestation_path.read_text(encoding="utf-8"))
    assert final["all_attested"] is True
