"""Marker contracts for fast and artifact-heavy test lanes."""

from __future__ import annotations

import ast
from pathlib import Path


def _decorator_name(node: ast.AST) -> str:
    if isinstance(node, ast.Call):
        return _decorator_name(node.func)
    if isinstance(node, ast.Attribute):
        parent = _decorator_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _module_marks_artifact_slow(tree: ast.Module) -> bool:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "pytestmark" for target in node.targets):
            value = node.value
            if _decorator_name(value).endswith("pytest.mark.artifact_slow"):
                return True
            if isinstance(value, (ast.List, ast.Tuple)):
                return any(_decorator_name(item).endswith("pytest.mark.artifact_slow") for item in value.elts)
    return False


def test_mutating_artifact_tests_are_not_in_fast_lane() -> None:
    root = Path(__file__).resolve().parent
    offenders: list[str] = []
    for path in sorted(root.glob("**/test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        module_artifact_slow = _module_marks_artifact_slow(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            decorators = {_decorator_name(decorator) for decorator in node.decorator_list}
            mutates = any(name.endswith("pytest.mark.mutates_artifacts") for name in decorators)
            artifact_slow = module_artifact_slow or any(
                name.endswith("pytest.mark.artifact_slow") for name in decorators
            )
            if mutates and not artifact_slow:
                offenders.append(f"{path.relative_to(root)}::{node.name}")

    assert offenders == []
