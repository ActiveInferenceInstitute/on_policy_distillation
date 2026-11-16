"""Roadmap/taskboard drift controls."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
import yaml


def _load_audit_module(project_root: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "audit_roadmap_tasks",
        project_root / "scripts" / "audit_roadmap_tasks.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_inputs(project_root: Path, tmp_path: Path) -> tuple[Path, Path, dict]:
    tasks = yaml.safe_load((project_root / "tasks.yaml").read_text(encoding="utf-8"))
    todo = (project_root / "TODO.md").read_text(encoding="utf-8")
    tasks_path = tmp_path / "tasks.yaml"
    todo_path = tmp_path / "TODO.md"
    tasks_path.write_text(yaml.safe_dump(tasks, sort_keys=False), encoding="utf-8")
    todo_path.write_text(todo, encoding="utf-8")
    return tasks_path, todo_path, tasks


def _save_tasks(path: Path, tasks: dict) -> None:
    path.write_text(yaml.safe_dump(tasks, sort_keys=False), encoding="utf-8")


def test_roadmap_task_audit_accepts_current_files(project_root: Path) -> None:
    audit = _load_audit_module(project_root)

    assert audit.audit_roadmap_tasks(tasks_path=project_root / "tasks.yaml", todo_path=project_root / "TODO.md") == []


def test_roadmap_task_audit_rejects_closed_open_soak(project_root: Path, tmp_path: Path) -> None:
    audit = _load_audit_module(project_root)
    tasks_path, todo_path, tasks = _write_inputs(project_root, tmp_path)
    opsd8 = next(row for row in tasks["tasks"] if row["id"] == "opsd-8")
    opsd8["status"] = "done"
    opsd8["progress"] = 100
    _save_tasks(tasks_path, tasks)

    issues = audit.audit_roadmap_tasks(tasks_path=tasks_path, todo_path=todo_path)

    assert any("AI-TEST-ISOLATION-1" in issue for issue in issues)


def test_roadmap_task_audit_rejects_missing_validator_task(project_root: Path, tmp_path: Path) -> None:
    audit = _load_audit_module(project_root)
    tasks_path, todo_path, tasks = _write_inputs(project_root, tmp_path)
    tasks["tasks"] = [row for row in tasks["tasks"] if row["id"] != "opsd-9"]
    _save_tasks(tasks_path, tasks)

    issues = audit.audit_roadmap_tasks(tasks_path=tasks_path, todo_path=todo_path)

    assert any("opsd-9 task row is missing" in issue for issue in issues)


def test_roadmap_task_audit_rejects_progress_status_drift(project_root: Path, tmp_path: Path) -> None:
    audit = _load_audit_module(project_root)
    tasks_path, todo_path, tasks = _write_inputs(project_root, tmp_path)
    opsd5 = next(row for row in tasks["tasks"] if row["id"] == "opsd-5")
    opsd5["status"] = "in_progress"
    opsd5["progress"] = 100
    _save_tasks(tasks_path, tasks)

    issues = audit.audit_roadmap_tasks(tasks_path=tasks_path, todo_path=todo_path)

    assert any("active but progress is 100" in issue for issue in issues)


@pytest.mark.parametrize(
    "todo",
    [
        "## Completed / Closed (historical)\n- [x] `AI-TEST-ISOLATION-1` completed.\n",
        "## History\n### Active roadmap\n| ID | Work |\n| --- | --- |\n"
        "| `AI-TEST-ISOLATION-1` | Old in-progress record |\n",
        "## Active roadmap\n| ID | Status |\n| --- | --- |\n"
        "| `AI-TEST-ISOLATION-1` | done |\n",
        "## Notes\nAI-TEST-ISOLATION-1 was completed; the old Live canonical supplemental artifacts "
        "heading and `_vN` discussion are historical.\n",
        "> ## Active roadmap\n> - [ ] `AI-TEST-ISOLATION-1`\n",
        "```markdown\n## Active roadmap\n- [ ] `AI-TEST-ISOLATION-1`\n```\n",
        "<!--\n## Active roadmap\n- [ ] `AI-TEST-ISOLATION-1`\n-->\n",
        "## Live canonical supplemental artifacts\n| Canonical id | Purpose |\n| --- | --- |\n"
        "| `proof_dependency_graph` | Implemented source surface, not an open status |\n",
    ],
)
def test_historical_closed_and_inventory_mentions_do_not_reopen_tasks(
    project_root: Path, tmp_path: Path, todo: str,
) -> None:
    audit = _load_audit_module(project_root)
    tasks_path, todo_path, tasks = _write_inputs(project_root, tmp_path)
    for task in tasks["tasks"]:
        if task["id"] in {"opsd-5", "opsd-8"}:
            task.update(status="done", progress=100, notes="")
    _save_tasks(tasks_path, tasks)
    todo_path.write_text(todo, encoding="utf-8")

    assert audit.audit_roadmap_tasks(tasks_path=tasks_path, todo_path=todo_path) == []


@pytest.mark.parametrize(
    "todo",
    [
        "## Active roadmap\n| ID | Work |\n| --- | --- |\n"
        "| `AI-TEST-ISOLATION-1` | Complete the idle-host soak |\n",
        "## Remaining work\n- [ ] **AI-TEST-ISOLATION-1**: complete the soak.\n",
        "## Current records\n| ID | Status |\n| --- | --- |\n"
        "| `AI-TEST-ISOLATION-1` | in_progress |\n",
    ],
)
def test_explicit_open_soak_cannot_be_marked_complete(
    project_root: Path, tmp_path: Path, todo: str,
) -> None:
    audit = _load_audit_module(project_root)
    tasks_path, todo_path, tasks = _write_inputs(project_root, tmp_path)
    next(task for task in tasks["tasks"] if task["id"] == "opsd-8").update(status="done", progress=100)
    _save_tasks(tasks_path, tasks)
    todo_path.write_text(todo, encoding="utf-8")

    issues = audit.audit_roadmap_tasks(tasks_path=tasks_path, todo_path=todo_path)

    assert any("AI-TEST-ISOLATION-1" in issue for issue in issues)


@pytest.mark.parametrize("notes", ["complete_soak: true", "Preserve seed 61300 failures."])
def test_open_soak_retains_closure_and_seed_evidence(
    project_root: Path, tmp_path: Path, notes: str,
) -> None:
    audit = _load_audit_module(project_root)
    tasks_path, todo_path, tasks = _write_inputs(project_root, tmp_path)
    opsd8 = next(task for task in tasks["tasks"] if task["id"] == "opsd-8")
    opsd8["notes"] = notes
    _save_tasks(tasks_path, tasks)

    issues = audit.audit_roadmap_tasks(tasks_path=tasks_path, todo_path=todo_path)

    assert issues
    opsd8["notes"] = "Require complete_soak: true; preserve seed 61300 failures."
    _save_tasks(tasks_path, tasks)
    assert audit.audit_roadmap_tasks(tasks_path=tasks_path, todo_path=todo_path) == []


def test_active_soak_malformed_progress_is_a_diagnostic(project_root: Path, tmp_path: Path) -> None:
    audit = _load_audit_module(project_root)
    tasks_path, todo_path, tasks = _write_inputs(project_root, tmp_path)
    next(task for task in tasks["tasks"] if task["id"] == "opsd-8")["progress"] = "unknown"
    _save_tasks(tasks_path, tasks)

    issues = audit.audit_roadmap_tasks(tasks_path=tasks_path, todo_path=todo_path)

    assert any("opsd-8" in issue for issue in issues)


def test_only_explicit_open_supplemental_rows_require_task_bindings(
    project_root: Path, tmp_path: Path,
) -> None:
    audit = _load_audit_module(project_root)
    tasks_path, todo_path, tasks = _write_inputs(project_root, tmp_path)
    opsd5 = next(task for task in tasks["tasks"] if task["id"] == "opsd-5")
    opsd5["notes"] = "Deepen stable proof_dependency_graph source binding."
    _save_tasks(tasks_path, tasks)
    todo_path.write_text(
        "## Live canonical supplemental artifacts\n"
        "| Canonical id | Status |\n| --- | --- |\n"
        "| `proof_dependency_graph` | in_progress |\n"
        "| `release_attestation` | done |\n",
        encoding="utf-8",
    )
    assert audit.audit_roadmap_tasks(tasks_path=tasks_path, todo_path=todo_path) == []

    opsd5.update(status="done", progress=100)
    _save_tasks(tasks_path, tasks)
    issues = audit.audit_roadmap_tasks(tasks_path=tasks_path, todo_path=todo_path)
    assert any("opsd-5" in issue for issue in issues)


@pytest.mark.parametrize("notes", ["stable canonical IDs", "ablation_sensitivity_report"])
def test_open_supplemental_checkbox_requires_its_source_id_and_stability(
    project_root: Path, tmp_path: Path, notes: str,
) -> None:
    audit = _load_audit_module(project_root)
    tasks_path, todo_path, tasks = _write_inputs(project_root, tmp_path)
    opsd5 = next(task for task in tasks["tasks"] if task["id"] == "opsd-5")
    opsd5["notes"] = notes
    _save_tasks(tasks_path, tasks)
    todo_path.write_text("- [ ] `ablation_sensitivity_report`: authenticate joins.\n", encoding="utf-8")

    issues = audit.audit_roadmap_tasks(tasks_path=tasks_path, todo_path=todo_path)

    assert issues
    opsd5["notes"] = "Deepen stable ablation_sensitivity_report source binding."
    _save_tasks(tasks_path, tasks)
    assert audit.audit_roadmap_tasks(tasks_path=tasks_path, todo_path=todo_path) == []
