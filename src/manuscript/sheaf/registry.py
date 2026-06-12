"""Track registry loading and section ordering."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from manuscript.sheaf.models import SheafSection, TrackRegistry, TrackSpec


def load_track_registry(registry_path: Path) -> TrackRegistry:
    registry_path = registry_path.resolve()
    stat = registry_path.stat()
    raw = _load_registry_yaml_cached(str(registry_path), stat.st_mtime_ns, stat.st_size)
    tracks_raw = raw.get("tracks") or {}
    specs: dict[str, TrackSpec] = {}
    for track_id, meta in tracks_raw.items():
        entry = meta or {}
        renderer = str(entry.get("renderer", "markdown"))
        specs[str(track_id)] = TrackSpec(
            id=str(track_id),
            order=int(entry.get("order", 999)),
            renderer=renderer,
            label=str(entry.get("label", track_id)),
            optional=bool(entry.get("optional", False)),
        )
    renderers_raw = raw.get("renderers") or {}
    suffixes: dict[str, tuple[str, ...]] = {}
    for name, meta in renderers_raw.items():
        entry = meta or {}
        suffixes[str(name)] = tuple(str(s) for s in entry.get("suffixes") or ())
    return TrackRegistry(tracks=specs, renderer_suffixes=suffixes)


@lru_cache(maxsize=16)
def _load_registry_yaml_cached(path: str, mtime_ns: int, size: int) -> dict:
    del mtime_ns, size
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def track_order_for_section(
    section: SheafSection,
    registry: TrackRegistry | dict[str, TrackSpec],
) -> list[str]:
    specs = registry.tracks if isinstance(registry, TrackRegistry) else registry
    if section.track_order:
        return list(section.track_order)
    bound = set(section.tracks)
    if section.include_tracks:
        bound &= set(section.include_tracks)
    if section.exclude_tracks:
        bound -= set(section.exclude_tracks)
    return sorted(
        bound,
        key=lambda tid: specs.get(tid, TrackSpec(tid, 999, "markdown", tid)).order,
    )


def list_registered_tracks(project_root: Path) -> list[TrackSpec]:
    from manuscript.sheaf.models import DEFAULT_REGISTRY_REL

    registry_path = project_root / DEFAULT_REGISTRY_REL
    return sorted(load_track_registry(registry_path).tracks.values(), key=lambda t: t.order)
