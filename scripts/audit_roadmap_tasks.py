#!/usr/bin/env python3
"""Audit roadmap prose against the taskboard metadata.

The project keeps future-work prose in ``TODO.md`` and taskboard metadata in
``tasks.yaml``. This script catches the small set of status drifts that matter
for the current verifier-first roadmap: open isolation-soak work, canonical
artifact deepening, and the explicit validator/audit tasks created for this
tranche.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ACTIVE_TASK_STATUSES = {"todo", "in_progress", "blocked"}
VALID_TASK_STATUSES = ACTIVE_TASK_STATUSES | {"done"}


def _read_tasks(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _task_by_id(taskboard: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = taskboard.get("tasks") or []
    return {str(row.get("id")): row for row in rows if isinstance(row, dict) and row.get("id")}


def audit_roadmap_tasks(*, tasks_path: Path, todo_path: Path) -> list[str]:
    """Return task/TODO consistency issues."""
    taskboard = _read_tasks(tasks_path)
    tasks = _task_by_id(taskboard)
    todo_text = todo_path.read_text(encoding="utf-8")
    issues: list[str] = []

    for task_id, task in tasks.items():
        status = task.get("status")
        progress = task.get("progress")
        if status not in VALID_TASK_STATUSES:
            issues.append(f"{task_id} has unknown status {status!r}")
        if not isinstance(progress, int) or not 0 <= progress <= 100:
            issues.append(f"{task_id} progress must be an integer in [0, 100]")
            continue
        if status == "done" and progress != 100:
            issues.append(f"{task_id} is done but progress is not 100")
        if status != "done" and progress == 100:
            issues.append(f"{task_id} is active but progress is 100")

    required_rows = {
        "opsd-8": "isolation",
        "opsd-9": "soak report validator",
        "opsd-10": "roadmap/task",
    }
    for task_id, title_fragment in required_rows.items():
        task = tasks.get(task_id)
        if not task:
            issues.append(f"{task_id} task row is missing")
            continue
        if title_fragment.lower() not in str(task.get("title", "")).lower():
            issues.append(f"{task_id} title does not describe {title_fragment}")

    opsd8 = tasks.get("opsd-8") or {}
    if "AI-TEST-ISOLATION-1" in todo_text:
        if opsd8.get("status") != "in_progress":
            issues.append("AI-TEST-ISOLATION-1 is active in TODO.md but opsd-8 is not in_progress")
        if int(opsd8.get("progress", 0) or 0) >= 100:
            issues.append("AI-TEST-ISOLATION-1 is active in TODO.md but opsd-8 is complete")
        opsd8_notes = str(opsd8.get("notes", ""))
        if "complete_soak: true" not in opsd8_notes:
            issues.append("opsd-8 notes must name the complete_soak: true closure condition")
        if "61300" not in opsd8_notes:
            issues.append("opsd-8 notes must preserve the latest reported shuffle-seed evidence")

    if "Live canonical supplemental artifacts" in todo_text:
        opsd5 = tasks.get("opsd-5") or {}
        if opsd5.get("status") not in ACTIVE_TASK_STATUSES:
            issues.append("canonical supplemental artifacts are open in TODO.md but opsd-5 is not active")
        opsd5_notes = str(opsd5.get("notes", ""))
        for artifact_id in (
            "proof_dependency_graph",
            "state_transition_table",
            "ablation_sensitivity_report",
            "release_attestation",
        ):
            if artifact_id not in opsd5_notes:
                issues.append(f"opsd-5 notes omit canonical artifact {artifact_id}")

    if "`_vN`" in todo_text:
        opsd5_notes = str((tasks.get("opsd-5") or {}).get("notes", ""))
        if "_vN" not in opsd5_notes and "stable" not in opsd5_notes.lower():
            issues.append("opsd-5 notes must preserve the stable-id/no-_vN constraint")

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, default=PROJECT_ROOT / "tasks.yaml")
    parser.add_argument("--todo", type=Path, default=PROJECT_ROOT / "TODO.md")
    parser.add_argument("--json", action="store_true", help="emit machine-readable audit results")
    args = parser.parse_args(argv)

    tasks_path = args.tasks if args.tasks.is_absolute() else PROJECT_ROOT / args.tasks
    todo_path = args.todo if args.todo.is_absolute() else PROJECT_ROOT / args.todo
    issues = audit_roadmap_tasks(tasks_path=tasks_path, todo_path=todo_path)
    if args.json:
        print(json.dumps({"ok": not issues, "issues": issues}, indent=2, sort_keys=True))
    elif issues:
        for issue in issues:
            print(f"FAIL: {issue}", file=sys.stderr)
    else:
        print("PASS: TODO.md and tasks.yaml are consistent")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
