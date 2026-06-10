"""Import-boundary tests for source package orchestration."""

from __future__ import annotations

import ast
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
BOUNDARY_ROOTS = ("gates", "manuscript", "orchestration", "roadmap_tracks")


def _module_name(path: Path) -> str:
    rel = path.relative_to(SRC_ROOT).with_suffix("")
    parts = rel.parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _resolve_from_import(current: str, node: ast.ImportFrom, *, is_package: bool) -> str | None:
    if node.level:
        parts = current.split(".")
        if not is_package:
            parts = parts[:-1]
        base = parts[: max(len(parts) - node.level + 1, 0)]
        if node.module:
            base.extend(node.module.split("."))
        return ".".join(part for part in base if part)
    return node.module


def _local_target(candidate: str | None, modules: set[str]) -> str | None:
    if not candidate:
        return None
    parts = candidate.split(".")
    for index in range(len(parts), 0, -1):
        prefix = ".".join(parts[:index])
        if prefix in modules:
            return prefix
    return None


def _top_level_import_graph() -> dict[str, set[str]]:
    modules = {_module_name(path) for path in SRC_ROOT.rglob("*.py")}
    graph: dict[str, set[str]] = {module: set() for module in modules}
    for path in SRC_ROOT.rglob("*.py"):
        module = _module_name(path)
        is_package = path.name == "__init__.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = _local_target(alias.name, modules)
                    if target and target != module:
                        graph[module].add(target)
            elif isinstance(node, ast.ImportFrom):
                target = _local_target(_resolve_from_import(module, node, is_package=is_package), modules)
                if target and target != module:
                    graph[module].add(target)
    return graph


def _strong_components(graph: dict[str, set[str]]) -> list[set[str]]:
    index = 0
    stack: list[str] = []
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    on_stack: set[str] = set()
    components: list[set[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for target in graph[node]:
            if target not in indices:
                visit(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[target])
        if lowlinks[node] == indices[node]:
            component: set[str] = set()
            while True:
                item = stack.pop()
                on_stack.remove(item)
                component.add(item)
                if item == node:
                    break
            components.append(component)

    for node in graph:
        if node not in indices:
            visit(node)
    return components


def test_no_top_level_source_import_cycles() -> None:
    graph = _top_level_import_graph()
    cycles = [sorted(component) for component in _strong_components(graph) if len(component) > 1]
    assert cycles == []


def test_boundary_packages_do_not_import_contracts_through_each_other() -> None:
    graph = _top_level_import_graph()
    boundary_edges = {
        source: sorted(
            target
            for target in targets
            if source.startswith(BOUNDARY_ROOTS) and target.startswith(BOUNDARY_ROOTS)
        )
        for source, targets in graph.items()
    }
    assert "artifact_contracts" not in BOUNDARY_ROOTS
    assert "manuscript.sheaf.semantic" not in boundary_edges.get("roadmap_tracks.sheaf_tracks", [])
    assert "manuscript.sheaf.semantic" not in boundary_edges.get("roadmap_tracks.integration_audit_builders", [])
