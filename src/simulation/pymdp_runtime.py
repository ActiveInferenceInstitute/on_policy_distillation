"""Scoped pymdp/JAX runtime diagnostics for agent construction."""

from __future__ import annotations

import importlib.metadata
import json
import warnings
from pathlib import Path
from typing import Any, Callable

from simulation.pymdp_config import PymdpConfig, config_hash

KNOWN_JAX_STATIC_WARNING = "A JAX array is being set as static"
KNOWN_TREE_MAX_NODES_WARNING = "Used up all"
RUNTIME_DIAGNOSTICS_SCHEMA = "template_active_inference.pymdp_runtime_diagnostics.v1"

# Every categorized diagnostic row must carry one of these category labels; the
# read-time gate fails closed on any unknown category.
RUNTIME_ROW_CATEGORIES = frozenset({"construction", "inference", "backend", "warning", "fallback"})
# Categories whose rows must additionally carry a non-empty ``reason`` field.
RUNTIME_REASONED_CATEGORIES = frozenset({"inference", "fallback"})


def _categorized_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Derive explicit per-construction categorized diagnostic rows.

    Each agent-construction record fans out into category-labelled rows spanning
    ``construction``, ``inference``, ``backend``, optional ``warning`` rows, and a
    ``fallback`` row whenever the JAX backend reported an error (a genuine runtime
    fallback). ``inference`` and ``fallback`` rows always carry a non-empty
    ``reason``; the gate re-derives that every row has a known category and that
    every reasoned-category row is explained — an empty/blank reason fails closed.
    """
    rows: list[dict[str, Any]] = []
    for record in records:
        context = str(record.get("context", ""))
        backend_flags = record.get("backend_flags") or {}
        tree_count = int(record.get("known_tree_warning_count", 0) or 0)
        rows.append(
            {
                "category": "construction",
                "context": context,
                "reason": "",
                "explained": True,
            }
        )
        rows.append(
            {
                "category": "inference",
                "context": context,
                "reason": (
                    f"sophisticated-inference tree expanded with {tree_count} max-node warning(s)"
                    if tree_count
                    else "policy posterior computed via finite tree enumeration"
                ),
                "explained": True,
            }
        )
        rows.append(
            {
                "category": "backend",
                "context": context,
                "reason": "",
                "explained": True,
            }
        )
        for warning in (record.get("unexpected_warnings") or []) + (record.get("known_warnings") or []):
            rows.append(
                {
                    "category": "warning",
                    "context": context,
                    "reason": str(warning.get("message", "")),
                    "explained": True,
                }
            )
        backend_error = backend_flags.get("jax_backend_error")
        if backend_error:
            rows.append(
                {
                    "category": "fallback",
                    "context": context,
                    "reason": f"jax backend unavailable ({backend_error}); diagnostics recorded on fallback path",
                    "explained": True,
                }
            )
    return rows


def _runtime_rows_explained(rows: list[dict[str, Any]]) -> bool:
    """True iff every row has a known category and every reasoned-category row has a reason."""
    if not rows:
        return False
    for row in rows:
        category = row.get("category")
        if category not in RUNTIME_ROW_CATEGORIES:
            return False
        if category in RUNTIME_REASONED_CATEGORIES and not str(row.get("reason") or "").strip():
            return False
    return True


def _package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def _backend_flags() -> dict[str, Any]:
    try:
        import jax

        return {
            "jax_default_backend": jax.default_backend(),
            "jax_enable_x64": bool(jax.config.jax_enable_x64),
            "jax_platforms": ",".join(str(device.platform) for device in jax.devices()),
        }
    except (AttributeError, ImportError, RuntimeError, ValueError) as exc:
        return {"jax_backend_error": type(exc).__name__}


def _warning_record(warning: warnings.WarningMessage) -> dict[str, str | bool]:
    message = str(warning.message)
    return {
        "category": warning.category.__name__,
        "message": message,
        "known": warning.category is UserWarning and KNOWN_JAX_STATIC_WARNING in message,
    }


def construct_agent_with_diagnostics(
    project_root: Path,
    *,
    config: PymdpConfig,
    model: dict[str, list[Any]],
    policy_len: int,
    context: str,
    agent_factory: Callable[..., Any] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Construct ``pymdp.Agent`` while capturing the one audited JAX warning."""
    del project_root
    if agent_factory is None:
        from pymdp.agent import Agent

        agent_factory = Agent

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        agent = agent_factory(
            A=model["A"],
            B=model["B"],
            C=model["C"],
            D=model["D"],
            A_dependencies=model["A_dependencies"],
            B_dependencies=model["B_dependencies"],
            policy_len=policy_len,
            inference_algo=config.agent.inference_algo,
            action_selection=config.agent.action_selection,
            sampling_mode=config.agent.sampling_mode,
            gamma=config.agent.gamma,
            learn_A=config.agent.learn_A,
            learn_B=config.agent.learn_B,
        )

    records = [_warning_record(warning) for warning in captured]
    known = [record for record in records if record["known"]]
    unexpected = [record for record in records if not record["known"]]
    diagnostic = {
        "context": context,
        "config_hash": config_hash(config),
        "versions": {
            "inferactively_pymdp": _package_version("inferactively-pymdp"),
            "jax": _package_version("jax"),
            "jaxlib": _package_version("jaxlib"),
        },
        "backend_flags": _backend_flags(),
        "known_warning_count": len(known),
        "unexpected_warning_count": len(unexpected),
        "known_warnings": known,
        "unexpected_warnings": unexpected,
    }
    return agent, diagnostic


def build_runtime_diagnostics(records: list[dict[str, Any]]) -> dict[str, Any]:
    known_count = sum(int(record.get("known_warning_count", 0) or 0) for record in records)
    unexpected_count = sum(int(record.get("unexpected_warning_count", 0) or 0) for record in records)
    tree_count = sum(int(record.get("known_tree_warning_count", 0) or 0) for record in records)
    versions = records[-1].get("versions", {}) if records else {}
    backend_flags = records[-1].get("backend_flags", {}) if records else {}
    rows = _categorized_rows(records)
    return {
        "schema": RUNTIME_DIAGNOSTICS_SCHEMA,
        "records": records,
        "rows": rows,
        "row_count": len(rows),
        "construction_count": len(records),
        "config_hashes": sorted({str(record.get("config_hash")) for record in records if record.get("config_hash")}),
        "versions": versions,
        "backend_flags": backend_flags,
        "known_warning_count": known_count,
        "known_tree_warning_count": tree_count,
        "unexpected_warning_count": unexpected_count,
        "all_rows_explained": _runtime_rows_explained(rows),
        "ok": bool(records) and unexpected_count == 0,
    }


def write_runtime_diagnostics(project_root: Path, records: list[dict[str, Any]]) -> Path:
    root = project_root.resolve()
    path = root / "output" / "reports" / "pymdp_runtime_diagnostics.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(build_runtime_diagnostics(records), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def validate_runtime_diagnostics(project_root: Path) -> list[str]:
    root = project_root.resolve()
    path = root / "output" / "reports" / "pymdp_runtime_diagnostics.json"
    if not path.is_file():
        return ["missing output/reports/pymdp_runtime_diagnostics.json"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    issues: list[str] = []
    if payload.get("schema") != RUNTIME_DIAGNOSTICS_SCHEMA:
        issues.append("pymdp_runtime_diagnostics.json schema mismatch")
    if int(payload.get("construction_count", 0) or 0) < 1:
        issues.append("pymdp_runtime_diagnostics.json records no agent constructions")
    if int(payload.get("unexpected_warning_count", 0) or 0) != 0:
        issues.append("pymdp_runtime_diagnostics.json captured unexpected warning")
    # Re-derive the categorized-row contract from the stored rows (never trust the
    # stored boolean): every row must have a known category and every
    # inference/fallback row must carry a reason. Empty rows fail closed.
    rows = payload.get("rows") or []
    if not _runtime_rows_explained(rows):
        issues.append("pymdp_runtime_diagnostics.json has uncategorized or unexplained inference/fallback rows")
    if payload.get("all_rows_explained") is not _runtime_rows_explained(rows):
        issues.append("pymdp_runtime_diagnostics.json all_rows_explained disagrees with row re-derivation")
    if not {str(row.get("category")) for row in rows} >= {"construction", "inference", "backend"}:
        issues.append("pymdp_runtime_diagnostics.json missing required diagnostic categories")
    if not payload.get("config_hashes"):
        issues.append("pymdp_runtime_diagnostics.json lacks config hashes")
    if not payload.get("versions"):
        issues.append("pymdp_runtime_diagnostics.json lacks package versions")
    if not payload.get("backend_flags"):
        issues.append("pymdp_runtime_diagnostics.json lacks backend flags")
    if payload.get("ok") is not True:
        issues.append("pymdp_runtime_diagnostics.json does not record ok=true")
    return issues
