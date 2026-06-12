"""Configurable matplotlib style for publication figures."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_PALETTE: dict[str, str] = {
    "primary": "#111827",
    "secondary": "#2563eb",
    "accent": "#0f766e",
    "grid": "#d4d4d8",
    "muted": "#64748b",
    "reference": "#52525b",
    "pass": "#0f766e",
    "fail": "#b91c1c",
    "proved": "#dcfce7",
    "sorry": "#fee2e2",
    "panel_bg": "#f8fafc",
    "header_bg": "#e2e8f0",
}

_FONT_ROLE_MULTIPLIERS: dict[str, float] = {
    "title": 1.12,
    "subtitle": 1.0,
    "label": 1.0,
    "tick": 0.9,
    "legend": 0.82,
    "annotation": 0.78,
    "small": 0.74,
    "source": 0.7,
    "dense": 0.64,
    "table": 0.7,
    "hero": 2.05,
}

_FONT_ROLE_MINIMUMS: dict[str, float] = {
    "annotation": 11.0,
    "small": 10.5,
    "source": 10.0,
    "dense": 9.5,
    "table": 10.0,
}


@dataclass(frozen=True)
class FigureStyleConfig:
    dpi: int = 160
    transparent: bool = False
    font_scale: float = 1.0
    grid: bool = True
    palette: Mapping[str, str] = field(default_factory=lambda: dict(_DEFAULT_PALETTE))

    def color(self, role: str, fallback: str = "#111827") -> str:
        return str(self.palette.get(role, fallback))

    @property
    def base_font_size(self) -> float:
        return 10.0 * float(self.font_scale)

    def font_size(self, role: str = "label") -> float:
        """Return a named figure font size in points.

        Figure generators use this instead of one-off small literals so dense
        diagrams remain readable after the global PDF typography changes.
        """
        base = self.base_font_size
        multiplier = _FONT_ROLE_MULTIPLIERS.get(role, 1.0)
        minimum = _FONT_ROLE_MINIMUMS.get(role, 0.0)
        return max(minimum, base * multiplier)

    def rc_params(self) -> dict[str, Any]:
        base = self.base_font_size
        return {
            "font.size": base,
            "axes.titlesize": self.font_size("title"),
            "axes.labelsize": self.font_size("label"),
            "xtick.labelsize": self.font_size("tick"),
            "ytick.labelsize": self.font_size("tick"),
            "legend.fontsize": self.font_size("legend"),
            "figure.titlesize": base * 1.18,
        }


DEFAULT_FIGURE_STYLE = FigureStyleConfig()

_active_style: FigureStyleConfig = DEFAULT_FIGURE_STYLE


def active_style() -> FigureStyleConfig:
    return _active_style


def load_figure_style(project_root: Path) -> FigureStyleConfig:
    path = project_root.resolve() / "figures.yaml"
    if not path.is_file():
        return DEFAULT_FIGURE_STYLE
    stat = path.stat()
    return _load_figure_style_cached(str(path), stat.st_mtime_ns, stat.st_size)


@lru_cache(maxsize=16)
def _load_figure_style_cached(path: str, mtime_ns: int, size: int) -> FigureStyleConfig:
    del mtime_ns, size
    raw: dict[str, Any] = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    palette = dict(_DEFAULT_PALETTE)
    palette.update(dict(raw.get("palette") or {}))
    return FigureStyleConfig(
        dpi=int(raw.get("dpi", 160)),
        transparent=bool(raw.get("transparent", False)),
        font_scale=float(raw.get("font_scale", 1.0)),
        grid=bool(raw.get("grid", True)),
        palette=palette,
    )


@contextlib.contextmanager
def apply_style(config: FigureStyleConfig) -> Iterator[FigureStyleConfig]:
    global _active_style
    previous = _active_style
    _active_style = config
    import matplotlib.pyplot as plt

    with plt.rc_context(config.rc_params()):
        try:
            yield config
        finally:
            _active_style = previous
