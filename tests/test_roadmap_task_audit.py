"""Roadmap/taskboard drift controls."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

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
