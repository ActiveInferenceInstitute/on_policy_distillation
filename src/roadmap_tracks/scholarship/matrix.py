"""Builders, writers, and validators for the scholarship source matrix."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

import yaml

from .schema import EXPECTED_SCHOLARSHIP_KEYS, SCHOLARSHIP_SCHEMA
from .sources_base import _BASE_SCHOLARSHIP_SOURCES
from .sources_review import _REDTEAM_REVIEW_SOURCES, _RUN5_REVIEW_SOURCES

SCHOLARSHIP_SOURCES: tuple[dict[str, Any], ...] = (
    _BASE_SCHOLARSHIP_SOURCES + _REDTEAM_REVIEW_SOURCES + _RUN5_REVIEW_SOURCES
)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _bib_entries(root: Path) -> dict[str, str]:
    path = root / "manuscript" / "references.bib"
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,(.*?)(?=\n@\w+\s*\{|\Z)", re.S)
    return {match.group(1).strip(): match.group(2) for match in pattern.finditer(text)}


def _bib_field(entry: str, field: str) -> str:
    match = re.search(rf"\b{re.escape(field)}\s*=\s*\{{([^}}]+)\}}", entry, re.I | re.S)
    if not match:
        return ""
    return " ".join(match.group(1).split())


def _arxiv_id(entry: str) -> str:
    text = " ".join(entry.split())
    match = re.search(r"arXiv[:. ]+(\d{4}\.\d{4,5})(?:v\d+)?", text, re.I)
    if match:
        return match.group(1)
    doi = _bib_field(entry, "doi")
    match = re.search(r"arXiv\.(\d{4}\.\d{4,5})", doi, re.I)
    return match.group(1) if match else ""


def _manuscript_citation_text(root: Path) -> str:
    paths = sorted((root / "manuscript" / "sections").glob("**/*.md")) + sorted(
        path
        for path in (root / "manuscript").glob("*.md")
        if path.name not in {"99_references.md", "SYNTAX.md", "README.md", "AGENTS.md"}
    )
    return "\n".join(path.read_text(encoding="utf-8") for path in paths if path.is_file())


def _citation_present(text: str, key: str) -> bool:
    needle = f"@{key}"
    return needle in text


def _registry_tracks(root: Path) -> set[str]:
    tracks = (_load_yaml(root / "manuscript" / "sheaf" / "tracks.yaml").get("tracks") or {}).keys()
    return {str(track) for track in tracks}


def _manifest_sections(root: Path) -> set[str]:
    sections = _load_yaml(root / "manuscript" / "sheaf" / "manifest.yaml").get("sections") or []
    return {str(section.get("id")) for section in sections if isinstance(section, dict) and section.get("id")}


def _has_locator(entry: str) -> bool:
    lower = entry.lower()
    return "doi" in lower or "url" in lower or "https://" in lower or "http://" in lower


def build_scholarship_source_matrix(project_root: Path) -> dict[str, Any]:
    """Build the literature-to-method traceability matrix."""
    root = project_root.resolve()
    bib_entries = _bib_entries(root)
    registry = _registry_tracks(root)
    sections = _manifest_sections(root)
    citation_text = _manuscript_citation_text(root)
    rows: list[dict[str, Any]] = []
    for source in SCHOLARSHIP_SOURCES:
        key = str(source["citation_key"])
        entry = bib_entries.get(key, "")
        artifact = str(source["artifact"])
        track_ids = [str(track) for track in source["tracks"]]
        section_ids = [str(section) for section in source["manuscript_sections"]]
        row = {
            **source,
            "doi": _bib_field(entry, "doi"),
            "url": _bib_field(entry, "url"),
            "arxiv_id": _arxiv_id(entry),
            "bib_has_entry": bool(entry),
            "bib_has_locator": bool(entry and _has_locator(entry)),
            "cited_in_manuscript": _citation_present(citation_text, key),
            "artifact_exists": artifact == "output/data/scholarship_source_matrix.json" or (root / artifact).is_file(),
            "tracks_registered": set(track_ids).issubset(registry),
            "sections_bound": set(section_ids).issubset(sections),
        }
        row["connected"] = all(
            bool(row[field])
            for field in (
                "bib_has_entry",
                "bib_has_locator",
                "cited_in_manuscript",
                "artifact_exists",
                "tracks_registered",
                "sections_bound",
            )
        ) and bool(row["claim_boundary"])
        rows.append(row)
    expected = set(EXPECTED_SCHOLARSHIP_KEYS)
    observed = {str(row["citation_key"]) for row in rows}
    return {
        "schema": SCHOLARSHIP_SCHEMA,
        "rows": rows,
        "source_count": len(rows),
        "expected_sources": sorted(expected),
        "observed_sources": sorted(observed),
        "method_role_count": len({str(row["method_role"]) for row in rows}),
        "source_family_count": len({str(row["source_family"]) for row in rows}),
        "primary_source_count": sum(
            1
            for row in rows
            if row["source_kind"] in {"primary_article", "primary_repository", "primary_preprint", "primary_conference"}
        ),
        "all_expected_sources_present": observed == expected,
        "all_sources_connected": bool(rows) and all(row["connected"] for row in rows),
    }


def write_scholarship_source_matrix(project_root: Path) -> Path:
    """Write the source-backed scholarship matrix."""
    root = project_root.resolve()
    return _write_json(
        root / "output" / "data" / "scholarship_source_matrix.json", build_scholarship_source_matrix(root)
    )


def validate_scholarship_source_matrix_payload(payload: Mapping[str, Any]) -> list[str]:
    """Validate an already-loaded scholarship-source matrix payload."""
    issues: list[str] = []
    rows = payload.get("rows") or []
    observed = {str(row.get("citation_key")) for row in rows}
    expected = set(EXPECTED_SCHOLARSHIP_KEYS)
    if payload.get("schema") != SCHOLARSHIP_SCHEMA:
        issues.append("scholarship_source_matrix.json schema mismatch")
    if observed != expected or payload.get("all_expected_sources_present") is not True:
        issues.append("scholarship_source_matrix.json source set is incomplete")
    connected = bool(rows) and all(
        row.get("bib_has_entry")
        and row.get("bib_has_locator")
        and row.get("cited_in_manuscript")
        and row.get("artifact_exists")
        and row.get("tracks_registered")
        and row.get("sections_bound")
        and row.get("claim_boundary")
        and row.get("connected")
        for row in rows
    )
    if payload.get("all_sources_connected") is not True or payload.get("all_sources_connected") != connected:
        issues.append("scholarship_source_matrix.json has disconnected source rows")
    if int(payload.get("method_role_count", 0) or 0) < 6:
        issues.append("scholarship_source_matrix.json has too few method roles")
    return issues


def validate_scholarship_source_matrix(project_root: Path) -> list[str]:
    """Validate the saved scholarship-source matrix against its row evidence."""
    root = project_root.resolve()
    payload_path = root / "output" / "data" / "scholarship_source_matrix.json"
    if not payload_path.is_file():
        return ["scholarship_source_matrix.json missing"]
    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return ["scholarship_source_matrix.json is not valid JSON"]
    return validate_scholarship_source_matrix_payload(payload)
