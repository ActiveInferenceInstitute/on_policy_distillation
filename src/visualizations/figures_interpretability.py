"""Interpretability figures: the correspondence dictionary, the measured policy
posterior grid, and the OPD literature landscape (Run-4 additions).

Every value rendered here is read from a generated artifact; counts shown in
panel titles are derived from the loaded rows ("shown N of M" discipline)."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .figure_helpers import save_styled_figure
from .figure_io import save_figure_png
from .figure_registry import figure_output_path
from .figure_style import apply_style, load_figure_style


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def figure_correspondence_map(project_root: Path) -> Path:
    """Render the audited OPD <-> active inference dictionary as the paper's visual spine."""
    import textwrap

    root = project_root.resolve()
    style = load_figure_style(root)
    data = _load_json(root / "output" / "data" / "firstprinciples" / "correspondence_map.json")
    rows = list(data.get("rows") or [])
    if not rows:
        raise RuntimeError("correspondence_map.json has no rows to render")
    n = len(rows)
    out = figure_output_path(root, "correspondence_map")

    def _wrap(text: str, width: int) -> str:
        return "\n".join(textwrap.wrap(str(text), width=width)) or str(text)

    cells = [
        (
            _wrap(row.get("ai_component", ""), 30),
            _wrap(row.get("shared_object", ""), 34),
            _wrap(row.get("opd_counterpart", ""), 30),
        )
        for row in rows
    ]
    # variable row pitch: one unit per wrapped line, so long rows never collide
    line_counts = [max(cell.count("\n") + 1 for cell in triple) for triple in cells]
    pitches = [count + 0.55 for count in line_counts]
    total_units = sum(pitches)
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(11.8, 1.6 + 0.215 * total_units))
        ax.set_axis_off()
        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(0.0, total_units + 2.4)
        header_size = style.font_size("subtitle")
        cell_size = max(style.font_size("dense"), 9.5)
        header_y = total_units + 1.4
        ax.text(0.155, header_y, "Active inference", ha="center", va="center", fontsize=header_size,
                color=style.color("accent"), fontweight="bold")
        ax.text(0.50, header_y, "shared formal object", ha="center", va="center", fontsize=header_size,
                color=style.color("muted"), fontweight="bold")
        ax.text(0.845, header_y, "On-policy distillation", ha="center", va="center", fontsize=header_size,
                color=style.color("secondary"), fontweight="bold")
        cursor = total_units
        for index, (ai_text, shared_text, opd_text) in enumerate(cells):
            pitch = pitches[index]
            y = cursor - pitch / 2.0
            cursor -= pitch
            if index % 2 == 0:
                ax.axhspan(y - pitch / 2.0, y + pitch / 2.0, xmin=0.005, xmax=0.995,
                           color=style.color("muted"), alpha=0.07, lw=0)
            ax.text(0.155, y, ai_text, ha="center", va="center",
                    fontsize=cell_size, color=style.color("accent"), linespacing=1.15)
            ax.text(0.50, y, shared_text, ha="center", va="center",
                    fontsize=cell_size, color=style.color("primary"), style="italic", linespacing=1.15)
            ax.text(0.845, y, opd_text, ha="center", va="center",
                    fontsize=cell_size, color=style.color("secondary"), linespacing=1.15)
            for x_left, x_right in ((0.318, 0.352), (0.648, 0.682)):
                ax.annotate("", xy=(x_right, y), xytext=(x_left, y),
                            arrowprops={"arrowstyle": "<->", "color": style.color("muted"), "linewidth": 0.9})
        ax.set_title(
            f"The audited correspondence dictionary (all {n} rows, machine-validated)",
            fontsize=style.font_size("title"),
            color=style.color("primary"),
            pad=16,
        )
        save_styled_figure(fig, out, style)
    return out


def figure_policy_posterior_grid(project_root: Path) -> Path:
    """Render the measured per-step policy posteriors for both planners."""
    root = project_root.resolve()
    style = load_figure_style(root)
    data = _load_json(root / "output" / "data" / "pymdp_policy_posterior_grid.json")
    rows = [row for row in data.get("rows") or [] if row.get("posterior_available")]
    if not rows:
        raise RuntimeError("pymdp_policy_posterior_grid.json has no available posterior rows")
    total = len(data.get("rows") or [])
    planners = sorted({str(row["planner"]) for row in rows})
    out = figure_output_path(root, "policy_posterior_grid")
    with apply_style(style):
        fig, axes = plt.subplots(
            1, len(planners) + 1, figsize=(13.4, 4.6), gridspec_kw={"width_ratios": [*([1.0] * len(planners)), 1.15]}
        )
        mappable = None
        for panel_index, planner in enumerate(planners):
            ax = axes[panel_index]
            planner_rows = sorted((row for row in rows if row["planner"] == planner), key=lambda row: int(row["step"]))
            steps = [int(row["step"]) for row in planner_rows]
            action_names = sorted(planner_rows[0]["action_probabilities"])
            matrix = np.array(
                [[float(row["action_probabilities"][name]) for row in planner_rows] for name in action_names]
            )
            mappable = ax.imshow(matrix, aspect="auto", cmap="Blues", vmin=0.0, vmax=1.0)
            ax.set_xticks(range(len(steps)))
            ax.set_xticklabels([str(step) for step in steps], fontsize=style.font_size("tick"))
            ax.set_yticks(range(len(action_names)))
            ax.set_yticklabels(
                [name.replace("move_to_", "") for name in action_names], fontsize=style.font_size("tick")
            )
            ax.set_xlabel("rollout step", fontsize=style.font_size("label"))
            if panel_index == 0:
                ax.set_ylabel("action (marginal posterior)", fontsize=style.font_size("label"))
            ax.set_title(
                f"{planner.replace('_', ' ')} ({len(planner_rows)} steps)",
                fontsize=style.font_size("subtitle"),
                color=style.color("primary"),
            )
            for (row_idx, col_idx), value in np.ndenumerate(matrix):
                if value >= 0.30:
                    ax.text(col_idx, row_idx, f"{value:.2f}", ha="center", va="center",
                            fontsize=style.font_size("small"), color="white")
        if mappable is not None:
            colorbar = fig.colorbar(mappable, ax=list(axes[: len(planners)]), fraction=0.030, pad=0.015)
            colorbar.ax.tick_params(labelsize=style.font_size("tick"))
        ax_entropy = axes[-1]
        ax_entropy.yaxis.set_label_position("right")
        ax_entropy.yaxis.tick_right()
        for planner, color_role, marker in zip(planners, ("secondary", "accent"), ("o", "s")):
            planner_rows = sorted((row for row in rows if row["planner"] == planner), key=lambda row: int(row["step"]))
            ax_entropy.plot(
                [int(row["step"]) for row in planner_rows],
                [float(row["q_pi_entropy"]) for row in planner_rows],
                marker=marker,
                linewidth=2.0,
                color=style.color(color_role),
                label=planner.replace("_", " "),
            )
        ax_entropy.set_xlabel("rollout step", fontsize=style.font_size("label"))
        ax_entropy.set_ylabel("policy posterior entropy (nats)", fontsize=style.font_size("label"))
        ax_entropy.set_title(
            f"posterior sharpness ({len(rows)} of {total} grid rows measured)",
            fontsize=style.font_size("subtitle"),
            color=style.color("primary"),
        )
        ax_entropy.legend(fontsize=style.font_size("legend"))
        ax_entropy.grid(True, alpha=0.3)
        fig.suptitle(
            "Measured policy posteriors: the student's q over policies, step by step",
            fontsize=style.font_size("title"),
            color=style.color("primary"),
        )
        # colorbar layout conflicts with tight_layout; save via the shared PNG path
        save_figure_png(fig, out, dpi=style.dpi, facecolor="white", transparent=style.transparent)
    return out


_QUADRANTS: tuple[tuple[bool, bool, str], ...] = (
    (False, False, "off-policy, no privilege"),
    (False, True, "off-policy + privileged signal"),
    (True, False, "on-policy, no privilege"),
    (True, True, "on-policy + privileged signal"),
)


def figure_opd_taxonomy_landscape(project_root: Path) -> Path:
    """Render the audited method taxonomy as a year-by-design-quadrant landscape."""
    root = project_root.resolve()
    style = load_figure_style(root)
    data = _load_json(root / "output" / "data" / "firstprinciples" / "opd_taxonomy.json")
    methods = list(data.get("methods") or [])
    if not methods:
        raise RuntimeError("opd_taxonomy.json has no method rows")
    out = figure_output_path(root, "opd_taxonomy_landscape")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(12.6, 6.4))
        lane_color = {0: "muted", 1: "fail", 2: "secondary", 3: "accent"}
        years = [int(row["year"]) for row in methods]
        for lane, (on_policy, privileged, label) in enumerate(_QUADRANTS):
            lane_rows = [
                row
                for row in methods
                if bool(row["on_policy"]) == on_policy and bool(row["privileged_info"]) == privileged
            ]
            color = style.color(lane_color[lane])
            ax.axhspan(lane - 0.42, lane + 0.42, color=color, alpha=0.06, lw=0)
            ax.text(
                min(years) - 0.6,
                lane + 0.30,
                f"{label} ({len(lane_rows)})",
                fontsize=style.font_size("annotation"),
                color=color,
                fontweight="bold",
                ha="left",
            )
            occupancy: dict[int, int] = {}
            for row in sorted(lane_rows, key=lambda item: (int(item["year"]), str(item["acronym"]))):
                year = int(row["year"])
                slot = occupancy.get(year, 0)
                occupancy[year] = slot + 1
                # stack within a year (4 vertical slots), then shift a full label
                # column right; labels alternate sides so dense modern clusters
                # stay legible at print scale
                y = lane - 0.27 + (slot % 4) * 0.17
                x = year + 1.05 * (slot // 4)
                ax.scatter([x], [y], s=26, color=color, zorder=3)
                left_side = slot % 2 == 1
                ax.annotate(
                    str(row["acronym"]),
                    xy=(x, y),
                    xytext=(-5 if left_side else 5, 0),
                    textcoords="offset points",
                    fontsize=style.font_size("small"),
                    color=style.color("primary"),
                    va="center",
                    ha="right" if left_side else "left",
                )
        from matplotlib.ticker import MaxNLocator

        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_yticks(range(len(_QUADRANTS)))
        ax.set_yticklabels(["" for _ in _QUADRANTS])
        ax.set_xlabel("publication year", fontsize=style.font_size("label"))
        ax.set_xlim(min(years) - 0.8, max(years) + 2.6)
        ax.set_ylim(-0.6, len(_QUADRANTS) - 0.3)
        ax.grid(True, axis="x", alpha=0.25)
        ax.set_title(
            f"The distillation literature as a design landscape (all {len(methods)} audited methods)",
            fontsize=style.font_size("title"),
            color=style.color("primary"),
            pad=12,
        )
        save_styled_figure(fig, out, style)
    return out
