"""Shared matplotlib helpers for figure generators."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from typing import TYPE_CHECKING

from pathlib import Path

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

from .figure_io import save_figure_png
from .figure_registry import figure_output_path
from .figure_style import FigureStyleConfig, apply_style, load_figure_style


def save_styled_figure(fig: "Figure", path: Path, style: FigureStyleConfig) -> Path:
    engine = getattr(fig, "get_layout_engine", lambda: None)()
    if engine is None:
        fig.tight_layout(rect=(0.0, 0.085, 1.0, 0.965))
    else:
        # constrained_layout figures manage their own spacing; reserve the source-footer margin.
        with contextlib.suppress(Exception):
            fig.get_layout_engine().set(rect=(0.0, 0.045, 1.0, 0.96))
    return save_figure_png(
        fig,
        path,
        dpi=style.dpi,
        facecolor="white",
        transparent=style.transparent,
    )


def style_grid(ax: "Axes", style: FigureStyleConfig) -> None:
    if style.grid:
        ax.grid(True, alpha=0.35, color=style.color("grid"))


@contextlib.contextmanager
def styled_figure(project_root: Path, figure_id: str) -> Iterator[tuple[FigureStyleConfig, Path]]:
    """Load style, resolve output path, and apply matplotlib rc context."""
    root = project_root.resolve()
    style = load_figure_style(root)
    out = figure_output_path(root, figure_id)
    with apply_style(style):
        yield style, out

def subset_note(fig, shown: int, total: int, what: str, *, color: str = "#64748b", fontsize: float = 9.0) -> None:
    """Stamp a 'showing N of M' annotation on any figure rendering a filtered view.

    Caption tokens are computed from full data ledgers; when a figure filters or
    aggregates rows, the pixels must say so themselves or the figure silently
    over-claims its coverage. No-op when nothing was dropped.
    """
    if shown >= total:
        return
    fig.text(
        0.99,
        0.005,
        f"showing {shown} of {total} {what}",
        ha="right",
        va="bottom",
        fontsize=fontsize,
        color=color,
    )
