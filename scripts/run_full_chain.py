#!/usr/bin/env python3
"""One-command convergent pipeline runner (thin orchestrator).

Runs the canonical analysis chain in the order declared by
``manuscript/config.yaml`` ``analysis.scripts`` (the single source of truth —
nothing is hard-coded here), then validates, then — because
``release_attestation.json`` attests the *previous* ``validation_report.json``
(see ``src/roadmap_tracks/supplemental.py``) — re-runs the attestation tail and
re-validates until the report is green and stable, bounded by ``--max-passes``.

This replaces the manual "re-run the tail, validate again" dance that the
attestation circularity otherwise requires after any red validate.

Exit code is honest: 0 only when the final ``validate_outputs`` pass exits 0.

Usage:
    .venv/bin/python scripts/run_full_chain.py             # full chain + converge
    .venv/bin/python scripts/run_full_chain.py --tail-only # convergence tail only
    .venv/bin/python scripts/run_full_chain.py --render    # + render the PDF
    .venv/bin/python scripts/run_full_chain.py --dry-run   # print the plan
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from contextlib import contextmanager
from collections.abc import Iterator

import fcntl

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent

#: Scripts whose outputs feed the attestation/certificate fixed point. Order
#: matters: spine before audits, sheaf tracks before variable hydration.
CONVERGENCE_TAIL = [
    "generate_validation_spine.py",
    "generate_toy_sweep_tracks.py",
    "generate_formal_interop_tracks.py",
    "generate_integration_audit.py",
    "generate_sheaf_tracks.py",
    # Figure-producing tests may refresh PNG bytes without refreshing the
    # integration audit hash manifest. Regenerate figures before the final
    # audit/variable pass so tail-only repairs that legitimate mid-test state.
    "generate_figures.py",
    "z_generate_manuscript_variables.py",
]

VALIDATE = "validate_outputs.py"
RENDER = "render_pdf.py"
LOCK_PATH = PROJECT_ROOT / "output" / ".run_full_chain.lock"


def canonical_scripts(project_root: Path) -> list[str]:
    """The declared analysis order from manuscript/config.yaml (source of truth)."""
    config = yaml.safe_load((project_root / "manuscript" / "config.yaml").read_text(encoding="utf-8"))
    scripts = list(((config.get("analysis") or {}).get("scripts")) or [])
    if not scripts:
        raise SystemExit("manuscript/config.yaml declares no analysis.scripts — nothing to run")
    return scripts


def _run(project_root: Path, script: str) -> int:
    proc = subprocess.run(
        [sys.executable, str(project_root / "scripts" / script)],
        cwd=project_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    return proc.returncode


def _project_pytest_running(project_root: Path) -> bool:
    """Detect another same-repo pytest run before mutating generated artifacts."""

    try:
        proc = subprocess.run(
            ["ps", "-axo", "pid,command"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return False
    root = str(project_root)
    this_pid = os.getpid()
    for line in proc.stdout.splitlines():
        try:
            pid_text, command = line.strip().split(maxsplit=1)
            pid = int(pid_text)
        except ValueError:
            continue
        if pid == this_pid:
            continue
        if root in command and "pytest" in command and "rg " not in command:
            return True
    return False


@contextmanager
def _pipeline_lock(project_root: Path) -> Iterator[None]:
    """Serialize full-chain writers so artifact fixed points are not interleaved."""

    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("w", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise SystemExit("another run_full_chain.py process is already mutating artifacts") from exc
        lock.write(f"pid={os.getpid()}\n")
        lock.flush()
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def _release_attestation_current(project_root: Path) -> bool:
    """Return true only when the attestation pins the current validation report."""
    report_path = project_root / "output" / "reports" / "validation_report.json"
    attestation_path = project_root / "output" / "reports" / "release_attestation.json"
    if not (report_path.is_file() and attestation_path.is_file()):
        return False
    try:
        attestation = json.loads(attestation_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    rows = attestation.get("rows") or []
    validation_row = next((row for row in rows if row.get("id") == "validation_report"), {})
    return (
        attestation.get("schema") == "template_active_inference.release_attestation.v1"
        and attestation.get("all_attested") is True
        and validation_row.get("report_sha256") == hashlib.sha256(report_path.read_bytes()).hexdigest()
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tail-only", action="store_true", help="skip analysis; run only the convergence tail")
    parser.add_argument("--render", action="store_true", help="render the PDF after a green validate")
    parser.add_argument("--max-passes", type=int, default=3, help="bound on validate->tail convergence passes")
    parser.add_argument("--dry-run", action="store_true", help="print the execution plan and exit")
    args = parser.parse_args(argv)

    full = canonical_scripts(PROJECT_ROOT)
    plan = (CONVERGENCE_TAIL if args.tail_only else full) + [VALIDATE]
    if args.dry_run:
        for step in plan:
            print(step)
        print(f"# then converge (tail + {VALIDATE}) up to {args.max_passes} passes" + (" + render" if args.render else ""))
        return 0

    if "PYTEST_CURRENT_TEST" not in os.environ and _project_pytest_running(PROJECT_ROOT):
        print("FAIL: refusing to mutate artifacts while a same-repo pytest process is running")
        return 2

    with _pipeline_lock(PROJECT_ROOT):
        for script in CONVERGENCE_TAIL if args.tail_only else full:
            code = _run(PROJECT_ROOT, script)
            print(f"{script}: exit {code}")
            if code != 0 and script not in CONVERGENCE_TAIL:
                # Analysis-stage failures are real failures; the convergence loop
                # below only repairs attestation/staleness circularity, not science.
                print(f"FAIL: {script} exited {code} — aborting before validation")
                return code

        code = _run(PROJECT_ROOT, VALIDATE)
        print(f"{VALIDATE}: exit {code}")
        passes = 0
        while (code != 0 or not _release_attestation_current(PROJECT_ROOT)) and passes < args.max_passes:
            passes += 1
            print(f"convergence pass {passes}/{args.max_passes}: re-running attestation tail")
            for script in CONVERGENCE_TAIL:
                tail_code = _run(PROJECT_ROOT, script)
                if tail_code != 0:
                    print(f"FAIL: {script} exited {tail_code} during convergence")
                    return tail_code
            code = _run(PROJECT_ROOT, VALIDATE)
            print(f"{VALIDATE}: exit {code}")

        if code != 0:
            print(f"FAIL: validation still red after {passes} convergence pass(es)")
            return code
        if not _release_attestation_current(PROJECT_ROOT):
            print(f"FAIL: release attestation still stale after {passes} convergence pass(es)")
            return 1

        if args.render:
            render_code = _run(PROJECT_ROOT, RENDER)
            print(f"{RENDER}: exit {render_code}")
            if render_code != 0:
                return render_code

    print(f"OK: chain green (convergence passes used: {passes})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
