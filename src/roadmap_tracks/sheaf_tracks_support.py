"""Shared private helpers for canonical sheaf-track builders.

Pure code motion out of :mod:`roadmap_tracks.sheaf_tracks`. These loaders,
hashing, config-digest, and artifact-row helpers are consumed by both builder
batches (:mod:`roadmap_tracks.sheaf_tracks_builders` and
:mod:`roadmap_tracks.sheaf_tracks_reports`) and re-exported by the
``sheaf_tracks`` facade so ``roadmap_tracks.sheaf_tracks.<helper>`` keeps
resolving.
"""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .sheaf_track_contracts import CANONICAL_ARTIFACTS, LEGACY_ARTIFACTS


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return data


@lru_cache(maxsize=256)
def _parse_yaml_cached(path_str: str, _mtime_ns: int, _size: int) -> dict[str, Any]:
    """Parse a YAML file, memoized on (path, mtime, size).

    The artifact builders read the same manifest/registry/config/ledger YAML files
    dozens of times per ``write_sheaf_track_artifacts`` call; parsing dominates
    (~579 parses / ~7.5s in a single call). The cache key includes mtime_ns AND size
    so any rewrite (e.g. negative-control tests mutating then restoring these files)
    invalidates the entry. Callers receive a deepcopy via ``_load_yaml`` so mutation
    of the returned dict can never corrupt the cached object.
    """
    data = yaml.safe_load(Path(path_str).read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    stat = path.stat()
    return copy.deepcopy(_parse_yaml_cached(str(path), stat.st_mtime_ns, stat.st_size))


def _load_structured(path: Path) -> dict[str, Any]:
    if path.suffix.lower() in {".yaml", ".yml"}:
        return _load_yaml(path)
    return _load_json(path)


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _sha256(path: Path) -> str:
    if not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _analysis_scripts(root: Path) -> list[str]:
    cfg = _load_yaml(root / "manuscript" / "config.yaml")
    return [str(script) for script in ((cfg.get("analysis") or {}).get("scripts") or [])]


def _registry_tracks(root: Path) -> dict[str, dict[str, Any]]:
    registry = _load_yaml(root / "manuscript" / "sheaf" / "tracks.yaml")
    tracks = registry.get("tracks") or {}
    return tracks if isinstance(tracks, dict) else {}


def _manifest_sections(root: Path) -> list[dict[str, Any]]:
    manifest = _load_yaml(root / "manuscript" / "sheaf" / "manifest.yaml")
    sections = manifest.get("sections") or []
    return [section for section in sections if isinstance(section, dict)]


def _bound_tracks(root: Path) -> dict[str, list[str]]:
    bound: dict[str, list[str]] = {}
    for section in _manifest_sections(root):
        section_id = str(section.get("id") or "")
        tracks = section.get("tracks") or {}
        if not isinstance(tracks, dict):
            continue
        for track_id in tracks:
            bound.setdefault(str(track_id), []).append(section_id)
    return bound


def _claim_records(root: Path) -> list[dict[str, Any]]:
    ledger = _load_yaml(root / "data" / "claim_ledger.yaml")
    claims = ledger.get("claims") or []
    return [claim for claim in claims if isinstance(claim, dict)]


def _claim_ids_by_path(root: Path) -> dict[str, list[str]]:
    by_path: dict[str, list[str]] = {}
    for claim in _claim_records(root):
        rel = claim.get("path")
        claim_id = claim.get("id")
        if rel and claim_id:
            by_path.setdefault(str(rel), []).append(str(claim_id))
    return by_path


def _claim_ids_by_track(root: Path) -> dict[str, list[str]]:
    by_track: dict[str, list[str]] = {}
    for claim in _claim_records(root):
        claim_id = str(claim.get("id") or "")
        for track in claim.get("tracks") or []:
            by_track.setdefault(str(track), []).append(claim_id)
    return by_track


def _artifact_maps() -> tuple[dict[str, str], dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]]:
    from artifact_contracts import ARTIFACT_CONSUMERS, ARTIFACT_GATES, ARTIFACT_PRODUCERS

    return ARTIFACT_PRODUCERS, ARTIFACT_CONSUMERS, ARTIFACT_GATES


def _source_commit(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def _deterministic_seed(root: Path) -> int:
    payload = _load_yaml(root / "pymdp.yaml")
    return int(payload.get("random_seed", payload.get("seed", 0)) or 0)


def _config_digest(root: Path) -> str:
    inputs = (
        "manuscript/config.yaml",
        "manuscript/sheaf/manifest.yaml",
        "manuscript/sheaf/tracks.yaml",
        "manuscript/sheaf/coverage.yaml",
        "tracks.yaml",
        "figures.yaml",
        "pymdp.yaml",
        "data/claim_ledger.yaml",
    )
    digest = hashlib.sha256()
    for rel in inputs:
        path = root / rel
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        if path.is_file():
            digest.update(_sha256(path).encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _entropy(values: list[float]) -> float:
    import math

    return float(-sum(value * math.log(value) for value in values if value > 0.0))


def _root_output_dir(project_root: Path) -> Path:
    root = project_root.resolve()
    for parent in root.parents:
        if (parent / "run.sh").is_file() and (parent / "projects").is_dir():
            return parent / "output" / "templates" / root.name
    return root.parents[2] / "output" / "templates" / root.name


def _copied_parity(project_root: Path, rel_paths: list[str]) -> dict[str, Any]:
    root = project_root.resolve()
    copied_root = _root_output_dir(root)
    rows: list[dict[str, Any]] = []
    for rel in rel_paths:
        source = root / rel
        copied = copied_root / rel.removeprefix("output/")
        source_hash = _sha256(source)
        copied_hash = _sha256(copied)
        source_exists = source.is_file()
        copied_exists = copied.is_file()
        hash_matches = bool(source_hash) and source_hash == copied_hash
        render_deferred = rel.startswith("output/pdf/") or rel.startswith("output/web/")
        deferred = (source_exists and not hash_matches) or (not source_exists and render_deferred)
        rows.append(
            {
                "artifact": rel,
                "source_exists": source_exists,
                "copied_path": copied.relative_to(copied_root).as_posix(),
                "copied_exists": copied_exists,
                "source_sha256": source_hash,
                "copied_sha256": copied_hash,
                "hash_matches": hash_matches,
                "comparison_deferred_until_copy": deferred,
                "matches_when_copied": hash_matches or deferred,
            }
        )
    return {
        "copied_root": copied_root.as_posix(),
        "copied_root_exists": copied_root.is_dir(),
        "rows": rows,
        "row_count": len(rows),
        "all_required_sources_present": all(row["source_exists"] for row in rows),
        "all_copied_outputs_match": all(row["hash_matches"] for row in rows if row["copied_exists"]),
        "all_copied_outputs_match_or_deferred": all(row["matches_when_copied"] for row in rows),
        "pre_copy_stage": any(row["comparison_deferred_until_copy"] for row in rows),
    }


def _remove_legacy_artifacts(root: Path) -> None:
    for rel in LEGACY_ARTIFACTS:
        path = root / rel
        if path.is_file():
            path.unlink()


def _refresh_hydrated_manuscript(root: Path) -> None:
    """Refresh hydrated manuscript copies so semantic staleness gates converge."""
    from manuscript.hydrate import write_resolved_manuscript
    from manuscript.sheaf import compose_all_sections
    from manuscript.variables import generate_variables
    from roadmap_tracks.integration_audit import write_manuscript_staleness_report

    variables_path = root / "output" / "data" / "manuscript_variables.json"
    variables_path.parent.mkdir(parents=True, exist_ok=True)
    compose_all_sections(root)
    variables = generate_variables(root, require_analysis_outputs=False)
    variables_path.write_text(json.dumps(variables, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_resolved_manuscript(root, variables)
    write_manuscript_staleness_report(root)


def _canonical_artifact_rows(root: Path) -> list[dict[str, Any]]:
    producers, consumers, gates = _artifact_maps()
    configured = set(_analysis_scripts(root))
    claims = _claim_ids_by_path(root)
    digest = _config_digest(root)
    seed = _deterministic_seed(root)
    commit = _source_commit(root)
    rows: list[dict[str, Any]] = []
    for rel, producer in sorted(producers.items()):
        path = root / rel
        cycle_excluded = rel in {
            CANONICAL_ARTIFACTS["provenance"],
            CANONICAL_ARTIFACTS["semantic"],
            CANONICAL_ARTIFACTS["dependency"],
            CANONICAL_ARTIFACTS["track_improvement_scope"],
            CANONICAL_ARTIFACTS["replay_matrix"],
            CANONICAL_ARTIFACTS["artifact_diffoscope"],
            "output/reports/manuscript_hardcoded_variable_audit.json",
        }
        rows.append(
            {
                "artifact": rel,
                "path": rel,
                "producer": producer,
                "exists": path.is_file(),
                "size_bytes": path.stat().st_size if path.is_file() else 0,
                "sha256": _sha256(path),
                "deterministic_seed": seed,
                "config_digest": digest,
                "source_commit": commit,
                "producer_configured": producer in configured,
                "consumers": list(consumers.get(rel, ())),
                "validation_gates": list(gates.get(rel, ())),
                "claim_ids": sorted(claims.get(rel, [])),
                "hash_checked": not cycle_excluded,
                "cycle_excluded": cycle_excluded,
                "complete": path.is_file()
                and producer in configured
                and bool(consumers.get(rel))
                and bool(gates.get(rel)),
            }
        )
    return rows

