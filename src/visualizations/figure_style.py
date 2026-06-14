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
    "analytical": "#2563eb",
    "student": "#0f766e",
    "teacher": "#b45309",
    "energy": "#6d28d9",
    "validation": "#166534",
    "warning": "#b45309",
    "grid": "#d4d4d8",
    "muted": "#64748b",
    "reference": "#52525b",
    "pass": "#0f766e",
    "fail": "#b91c1c",
    "paper": "#ffffff",
    "cover_bg": "#eef6ff",
    "cover_panel": "#ffffff",
    "panel_edge": "#cbd5e1",
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
    "annotation": 11.5,
    "small": 10.5,
    "source": 10.5,
    "dense": 10.5,
    "table": 11.0,
}

_ACCESSIBLE_TEXT_PAIRS: dict[str, tuple[str, str, float]] = {
    "primary_on_paper": ("primary", "paper", 7.0),
    "muted_on_paper": ("muted", "paper", 4.5),
    "reference_on_paper": ("reference", "paper", 4.5),
    "secondary_on_paper": ("secondary", "paper", 4.5),
    "accent_on_paper": ("accent", "paper", 4.5),
    "teacher_on_paper": ("teacher", "paper", 4.5),
    "energy_on_paper": ("energy", "paper", 4.5),
    "validation_on_paper": ("validation", "paper", 4.5),
    "fail_on_paper": ("fail", "paper", 4.5),
    "primary_on_panel_bg": ("primary", "panel_bg", 7.0),
}


def _hex_rgb(color: str) -> tuple[float, float, float]:
    raw = color.strip().lstrip("#")
    if len(raw) != 6:
        raise ValueError(f"expected #RRGGBB color, got {color!r}")
    return tuple(int(raw[i : i + 2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore[return-value]


def _linear_channel(channel: float) -> float:
    return channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4


def relative_luminance(color: str) -> float:
    """Return WCAG relative luminance for a hex color."""
    red, green, blue = (_linear_channel(channel) for channel in _hex_rgb(color))
    return (0.2126 * red) + (0.7152 * green) + (0.0722 * blue)


def contrast_ratio(foreground: str, background: str) -> float:
    """Return WCAG contrast ratio for two hex colors."""
    lum_fg = relative_luminance(foreground)
    lum_bg = relative_luminance(background)
    lighter = max(lum_fg, lum_bg)
    darker = min(lum_fg, lum_bg)
    return (lighter + 0.05) / (darker + 0.05)


@dataclass(frozen=True)
class FigureStyleConfig:
    dpi: int = 160
    transparent: bool = False
    font_scale: float = 1.0
    grid: bool = True
    palette: Mapping[str, str] = field(default_factory=lambda: dict(_DEFAULT_PALETTE))

    def color(self, role: str, fallback: str = "#111827") -> str:
        return str(self.palette.get(role, fallback))

    def contrast_ratio(self, foreground_role: str, background_role: str = "paper") -> float:
        return contrast_ratio(self.color(foreground_role), self.color(background_role, "#ffffff"))

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

    def font_role_report(self) -> dict[str, dict[str, float | bool]]:
        """Return font role sizes and minimum checks for generated visualization audits."""
        roles = sorted(set(_FONT_ROLE_MULTIPLIERS) | set(_FONT_ROLE_MINIMUMS))
        return {
            role: {
                "size_pt": self.font_size(role),
                "minimum_pt": _FONT_ROLE_MINIMUMS.get(role, 0.0),
                "meets_minimum": self.font_size(role) >= _FONT_ROLE_MINIMUMS.get(role, 0.0),
            }
            for role in roles
        }

    def palette_contrast_report(self) -> dict[str, dict[str, float | str | bool]]:
        """Return WCAG contrast checks for the palette pairs used as text roles."""
        report: dict[str, dict[str, float | str | bool]] = {}
        for pair_id, (foreground_role, background_role, minimum_ratio) in _ACCESSIBLE_TEXT_PAIRS.items():
            ratio = self.contrast_ratio(foreground_role, background_role)
            report[pair_id] = {
                "foreground_role": foreground_role,
                "background_role": background_role,
                "ratio": ratio,
                "minimum_ratio": minimum_ratio,
                "passes_aa": ratio >= minimum_ratio,
            }
        return report

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
