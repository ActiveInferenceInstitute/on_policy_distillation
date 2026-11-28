"""Sheaf manifest loading."""

from __future__ import annotations

import copy
from functools import lru_cache
from pathlib import Path
from typing import cast

import yaml

from .models import (
    DEFAULT_MANIFEST_REL,
    DEFAULT_REGISTRY_REL,
    ImradBlock,
    MissingTrackPolicy,
    SectionKind,
    SheafDefaults,
    SheafManifest,
    SheafSection,
)


class _UniqueKeyLoader(yaml.SafeLoader):
    """Reject ambiguous bindings instead of silently retaining the last value."""

    def construct_mapping(self, node: yaml.nodes.MappingNode, deep: bool = False) -> dict:
        self.flatten_mapping(node)
        mapping: dict = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in mapping:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"duplicate key {key!r}",
                    key_node.start_mark,
                )
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def parse_missing(value: str | None, fallback: MissingTrackPolicy) -> MissingTrackPolicy:
    if value is None:
        return fallback
    try:
        return MissingTrackPolicy(str(value).strip().lower())
    except ValueError:
        return fallback


def load_manifest(
    manifest_path: Path,
    *,
    registry_path: Path | None = None,
    project_root: Path | None = None,
) -> SheafManifest:
    manifest_path = manifest_path.resolve()
    if project_root is not None:
        root = project_root.resolve()
    elif manifest_path.parent.name == "sheaf" and manifest_path.parent.parent.name == "manuscript":
        container = manifest_path.parent.parent.parent
        root = container.parent if container.name == "docs" else container
    else:
        root = manifest_path.parent
    registry = registry_path or (root / DEFAULT_REGISTRY_REL)
    stat = manifest_path.stat()
    raw = _load_manifest_yaml_cached(str(manifest_path), stat.st_mtime_ns, stat.st_size)
    defaults_raw = raw.get("defaults") or {}
    manifest_defaults = SheafDefaults(
        missing_track=parse_missing(defaults_raw.get("missing_track"), MissingTrackPolicy.SKIP),
    )
    sections: list[SheafSection] = []
    for entry in raw.get("sections") or []:
        tracks = {str(k): str(v) for k, v in dict(entry.get("tracks") or {}).items()}
        include = entry.get("include_tracks")
        exclude = entry.get("exclude_tracks")
        order_override = entry.get("track_order")
        kind_raw = str(entry.get("kind", "section")).strip().lower()
        kind: SectionKind = "group" if kind_raw == "group" else "section"
        imrad_raw = str(entry.get("imrad", "methods")).strip().lower()
        imrad: ImradBlock = (
            cast(ImradBlock, imrad_raw)
            if imrad_raw
            in {
                "introduction",
                "methods",
                "results",
                "discussion",
                "appendix",
            }
            else "methods"
        )
        depth = int(entry.get("depth", 0 if kind == "group" else 1))
        compose_raw = entry.get("compose")
        if compose_raw is None:
            compose = kind == "section"
        else:
            compose = bool(compose_raw)
        sections.append(
            SheafSection(
                id=str(entry["id"]),
                title=str(entry["title"]),
                short=str(entry.get("short", entry["id"])),
                order=int(entry["order"]),
                tracks=tracks,
                output_name=str(entry.get("output_name", f"{entry['order']:02d}_{entry['id']}.md")),
                kind=kind,
                imrad=imrad,
                depth=depth,
                compose=compose,
                track_order=tuple(str(t) for t in order_override) if order_override else None,
                include_tracks=tuple(str(t) for t in include) if include else None,
                exclude_tracks=tuple(str(t) for t in exclude) if exclude else None,
            )
        )
    return SheafManifest(
        defaults=manifest_defaults,
        sections=tuple(sorted(sections, key=lambda s: s.order)),
        registry_path=registry,
    )


@lru_cache(maxsize=16)
def _load_manifest_yaml_cached(path: str, mtime_ns: int, size: int) -> dict:
    del mtime_ns, size
    data = yaml.load(Path(path).read_text(encoding="utf-8"), Loader=_UniqueKeyLoader) or {}
    if not isinstance(data, dict):
        raise ValueError(f"manifest must contain a mapping: {path}")
    return data


def load_manifest_data(manifest_path: Path) -> dict:
    """Return a defensive, duplicate-safe manifest projection for artifact builders."""
    path = manifest_path.resolve()
    stat = path.stat()
    return copy.deepcopy(_load_manifest_yaml_cached(str(path), stat.st_mtime_ns, stat.st_size))


def default_manifest_path(project_root: Path) -> Path:
    return project_root.resolve() / DEFAULT_MANIFEST_REL
