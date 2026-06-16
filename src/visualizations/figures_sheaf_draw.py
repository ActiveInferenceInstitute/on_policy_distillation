"""Matplotlib drawing helpers for sheaf coverage figures."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pathlib import Path

if TYPE_CHECKING:
    from matplotlib.axes import Axes
import textwrap

import matplotlib.pyplot as plt
import numpy as np

from visualizations.figure_style import load_figure_style
from visualizations.figures_sheaf_payload import HeatmapPayload


def _imrad_group_label(imrad: str) -> str:
    return imrad.replace("_", " ").strip().title()


def _draw_imrad_group_labels(
    ax,
    payload: HeatmapPayload,
    *,
    style,
    label_fontsize: int,
) -> None:
    """Annotate IMRAD block names on the left margin of the heatmap."""
    if not payload.sections or not payload.cfg.heatmap.group_separator:
        return
    groups: list[tuple[str, int, int]] = []
    current_imrad: str | None = None
    start_idx = 0
    for row_idx, section in enumerate(payload.sections):
        imrad = str(section.get("imrad") or "")
        if current_imrad is not None and imrad != current_imrad:
            groups.append((current_imrad, start_idx, row_idx - 1))
            start_idx = row_idx
        current_imrad = imrad
    if current_imrad is not None:
        groups.append((current_imrad, start_idx, len(payload.sections) - 1))
    for imrad, start_row, end_row in groups:
        mid_y = (start_row + end_row) / 2.0 + 0.5
        ax.text(
            -1.15,
            mid_y,
            _imrad_group_label(imrad),
            transform=ax.transData,
            rotation=90,
            va="center",
            ha="center",
            fontsize=label_fontsize + 1,
            fontweight="bold",
            color=style.color("muted"),
        )


def draw_coverage_heatmap(
    ax: "Axes",
    payload: HeatmapPayload,
    project_root: Path,
    *,
    title: str | None = None,
    show_legend: bool = False,
    show_row_pct: bool = False,
    boundary_width: float = 1.0,
    label_fontsize: int = 8,
    show_group_labels: bool = True,
) -> None:
    from matplotlib.colors import ListedColormap

    style = load_figure_style(project_root)
    cfg = payload.cfg
    data = np.asarray(payload.grid, dtype=float)
    n_rows, n_cols = data.shape
    cmap = ListedColormap([cfg.colors.present, cfg.colors.absent, cfg.colors.missing])
    x_edges = np.arange(n_cols + 1)
    y_edges = np.arange(n_rows + 1)
    ax.pcolormesh(
        x_edges,
        y_edges,
        data,
        cmap=cmap,
        vmin=0,
        vmax=2,
        edgecolors=style.color("grid"),
        linewidth=0.35,
        shading="flat",
    )
    ax.set_xlim(0, n_cols)
    ax.set_ylim(n_rows, 0)
    for boundary in payload.group_boundaries:
        ax.axhline(boundary + 0.5, color=style.color("muted"), linewidth=boundary_width, zorder=3)
    ax.set_xticks(np.arange(len(payload.track_ids)) + 0.5)
    ax.set_xticklabels(payload.track_ids, rotation=45, ha="right", fontsize=label_fontsize)
    ax.set_yticks(np.arange(len(payload.y_labels)) + 0.5)
    wrapped_y_labels = [
        "\n".join(textwrap.wrap(label, width=28, break_long_words=False)) for label in payload.y_labels
    ]
    ax.set_yticklabels(wrapped_y_labels, fontsize=label_fontsize)
    ax.set_xlabel("Fragment tracks", fontsize=label_fontsize)
    if show_group_labels:
        _draw_imrad_group_labels(ax, payload, style=style, label_fontsize=label_fontsize)
    ax.set_title(title or cfg.report.title, fontsize=label_fontsize + 1, pad=8)
    if show_row_pct and cfg.heatmap.show_row_coverage_pct:
        n_cols = len(payload.track_ids)
        for row_idx, section in enumerate(payload.sections):
            cells = section.get("cells") or []
            bound = sum(1 for cell in cells if cell.get("bound"))
            present = sum(1 for cell in cells if cell.get("color") == "black")
            if bound:
                pct = 100.0 * present / bound
                ax.text(
                    n_cols - 0.08,
                    row_idx + 0.5,
                    f"{pct:.0f}%",
                    va="center",
                    ha="right",
                    fontsize=style.font_size("dense"),
                    color=style.color("muted"),
                )
    if show_legend:
        legend_handles = [
            plt.Rectangle((0, 0), 1, 1, fc=cfg.colors.present),
            plt.Rectangle((0, 0), 1, 1, fc=cfg.colors.absent, ec=style.color("grid")),
            plt.Rectangle((0, 0), 1, 1, fc=cfg.colors.missing),
        ]
        ax.legend(
            legend_handles,
            ["P — present (bound + file exists)", "— absent (not bound)", "M — missing (bound, absent)"],
            loc="upper left",
            bbox_to_anchor=(1.02, 1.0),
            ncol=1,
            fontsize=style.font_size("annotation"),
            frameon=True,
        )


def draw_track_layers_panel(ax, project_root: Path) -> bool:
    from manuscript.sheaf.manifest import load_manifest
    from manuscript.sheaf.registry import load_track_registry

    root = project_root.resolve()
    manifest = load_manifest(root / "manuscript" / "sheaf" / "manifest.yaml", project_root=root)
    registry = load_track_registry(root / manifest.registry_path)
    if not registry.tracks:
        return False
    style = load_figure_style(root)
    specs = sorted(registry.tracks.values(), key=lambda spec: spec.order)
    y_pos = np.arange(len(specs))
    bar_colors = [style.color("muted") if spec.optional else style.color("secondary") for spec in specs]
    ax.barh(
        y_pos,
        [1.0] * len(specs),
        color=bar_colors,
        edgecolor=style.color("primary"),
        linewidth=0.6,
        height=0.68,
        alpha=0.85,
    )
    for idx, spec in enumerate(specs):
        optional = " optional" if spec.optional else ""
        ax.text(
            0.02,
            idx,
            f"{spec.order:02d}  {spec.id}{optional}",
            va="center",
            ha="left",
            fontsize=style.font_size("small"),
            color=style.color("primary"),
            fontweight="bold",
        )
        ax.text(
            0.98,
            idx,
            spec.renderer,
            va="center",
            ha="right",
            fontsize=style.font_size("dense"),
            # Muted gray on the secondary-blue required bars was illegible;
            # white reads on blue, primary reads on the lighter optional fill.
            color="#ffffff" if not spec.optional else style.color("primary"),
            family="monospace",
        )
    ax.set_yticks([])
    ax.set_xlim(0.0, 1.0)
    ax.set_xticks([])
    ax.invert_yaxis()
    ax.set_title("Fragment track registry (compose order)", fontsize=style.font_size("small"), pad=8)
    ax.text(
        0.02,
        0.985,
        "Blue = required track · Gray = optional",
        transform=ax.transAxes,
        fontsize=style.font_size("source"),
        color=style.color("muted"),
        va="top",
    )
    return True


def layers_overview_figure_height(n_rows: int, row_height: float) -> float:
    """Figure height (inches) for the two-panel sheaf layers overview."""
    return max(6.5, n_rows * row_height + 2.0)
