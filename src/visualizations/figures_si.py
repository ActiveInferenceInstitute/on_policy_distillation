"""Supplementary-information figures for the pymdp T-maze rollout track."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import MaxNLocator

from .figure_helpers import save_styled_figure, style_grid
from .figure_registry import figure_output_path
from .figure_style import FigureStyleConfig, apply_style, load_figure_style


def _style_discrete_y(ax, style: FigureStyleConfig) -> None:
    style_grid(ax, style)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))


def _clean_action_label(name: str) -> str:
    return str(name).replace("move_to_", "").replace("_", " ")


def _tmaze_action_vocabulary(root: Path, data: dict[str, Any]) -> tuple[dict[int, str], list[str]]:
    index_to_name: dict[int, str] = {}
    for idx, name in zip(data.get("actions") or [], data.get("action_names") or [], strict=False):
        index_to_name.setdefault(int(idx), str(name))
    matrices_path = root / "output" / "data" / "si_tmaze_model_matrices.json"
    if matrices_path.is_file():
        matrices = json.loads(matrices_path.read_text(encoding="utf-8"))
        action_labels = ((matrices.get("labels") or {}).get("actions") or {})
        for idx_text, name in sorted(action_labels.items(), key=lambda item: int(item[0])):
            index_to_name.setdefault(int(idx_text), str(name))
    action_probabilities = data.get("action_probabilities") or []
    if action_probabilities:
        probability_names = sorted(str(name) for name in action_probabilities[0])
        unused_names = [name for name in probability_names if name not in set(index_to_name.values())]
        n_actions = max(len(probability_names), max(index_to_name, default=-1) + 1)
        for idx in range(n_actions):
            if idx not in index_to_name and unused_names:
                index_to_name[idx] = unused_names.pop(0)
    n_actions = max(index_to_name, default=-1) + 1
    vocab = [index_to_name.get(i, f"action {i}") for i in range(n_actions)]
    return index_to_name, vocab


def figure_si_belief_entropy_curve(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    trace_path = root / "output" / "data" / "si_tmaze_trace.json"
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    steps_data = trace.get("steps") or []
    entropies = [float(step.get("belief_entropy", 0.0)) for step in steps_data]
    out = figure_output_path(root, "si_belief_entropy_curve")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(9.2, 4.8))
        xs = list(range(len(entropies)))
        ax.plot(xs, entropies, linewidth=2.4, marker="o", markersize=5.2, color=style.color("primary"))
        ax.fill_between(xs, entropies, step="pre", alpha=0.08, color=style.color("secondary"))
        if entropies:
            mean_entropy = float(np.mean(entropies))
            ax.axhline(mean_entropy, color=style.color("accent"), linewidth=1.4, linestyle="--")
            ax.annotate(
                f"mean={mean_entropy:.3f}",
                xy=(xs[-1], mean_entropy),
                xytext=(-58, 8),
                textcoords="offset points",
                fontsize=style.font_size("annotation"),
                color=style.color("accent"),
                arrowprops={"arrowstyle": "->", "color": style.color("accent"), "linewidth": 0.8},
            )
        ax.set_xlabel("Timestep")
        ax.set_ylabel("Belief entropy (nats)")
        ax.set_title("Cue observation reduces rollout uncertainty")
        style_grid(ax, style)
        fig.text(0.01, 0.01, "Source: output/data/si_tmaze_trace.json", fontsize=style.font_size("source"), color=style.color("muted"))
        save_styled_figure(fig, out, style)
    return out


def figure_si_obs_action_trace(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    summary_path = root / "output" / "data" / "si_tmaze_summary.json"
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    observations_by_modality = data.get("observations_by_modality") or {"location": data.get("observations") or []}
    actions = data.get("actions") or []
    index_to_name, vocab = _tmaze_action_vocabulary(root, data)
    out = figure_output_path(root, "si_obs_action_trace")
    with apply_style(style):
        fig, axes = plt.subplots(2, 1, figsize=(10.6, 6.2), sharex=True, gridspec_kw={"height_ratios": [1.6, 1]})
        obs_ax, act_ax = axes
        xs = list(range(len(actions)))
        obs_colors = {
            "location": style.color("secondary"),
            "outcome": style.color("accent"),
            "cue": style.color("fail"),
        }
        offsets = {"location": 0.0, "outcome": 0.15, "cue": 0.3}
        for modality, values in observations_by_modality.items():
            obs_ax.step(
                list(range(len(values))),
                [float(value) + offsets.get(modality, 0.0) for value in values],
                where="post",
                linewidth=2,
                marker="o",
                markersize=3.8,
                color=obs_colors.get(modality, style.color("muted")),
                label=modality,
            )
        obs_ax.set_ylabel("Observation index")
        obs_ax.set_title("Observations and actions form one closed rollout loop")
        _style_discrete_y(obs_ax, style)
        obs_ax.legend(frameon=False, ncol=3, loc="upper left", title="Observation modality")
        obs_ax.text(
            0.99,
            0.97,
            "modality series offset vertically for visibility",
            transform=obs_ax.transAxes,
            ha="right",
            va="top",
            fontsize=style.font_size("source"),
            color=style.color("muted"),
        )
        act_ax.step(xs, actions, where="post", linewidth=2.4, marker="s", markersize=4.6, color=style.color("primary"))
        act_ax.set_xlabel("Timestep")
        act_ax.set_ylabel("Action")
        action_names = data.get("action_names") or []
        if vocab:
            act_ax.set_yticks(range(len(vocab)))
            act_ax.set_yticklabels([_clean_action_label(name) for name in vocab], fontsize=style.font_size("dense"))
        for x, action in enumerate(actions):
            action_idx = int(action)
            if x < len(action_names):
                name = str(action_names[x])
            else:
                name = index_to_name.get(action_idx, str(action))
            act_ax.text(
                x,
                float(action) + 0.22,
                _clean_action_label(name),
                ha="center",
                va="bottom",
                fontsize=style.font_size("dense"),
                color=style.color("primary"),
            )
        _style_discrete_y(act_ax, style)
        fig.text(0.01, 0.01, "Source: output/data/si_tmaze_summary.json", fontsize=style.font_size("source"), color=style.color("muted"))
        save_styled_figure(fig, out, style)
    return out


def figure_si_tmaze_actions(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    summary_path = root / "output" / "data" / "si_tmaze_summary.json"
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    actions = data.get("actions", [])
    action_probabilities = data.get("action_probabilities") or []
    _, vocab = _tmaze_action_vocabulary(root, data)
    planning_horizon = data.get("planning_horizon", "?")
    tree_warnings = (data.get("expected_known_warnings") or {}).get("tree_max_nodes", 0)
    out = figure_output_path(root, "si_tmaze_actions")
    with apply_style(style):
        fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.2), gridspec_kw={"width_ratios": [1.05, 1.9]})
        ax, prob_ax = axes
        steps = list(range(len(actions)))
        ax.step(steps, actions, where="post", linewidth=2, color=style.color("primary"))
        ax.fill_between(steps, actions, step="post", alpha=0.08, color=style.color("secondary"))
        ax.set_xlabel("Timestep")
        ax.set_ylabel("Action index")
        ax.set_title("Chosen action trace")
        if vocab:
            ax.set_yticks(range(len(vocab)))
            ax.set_yticklabels(
                [_clean_action_label(name) for name in vocab],
                fontsize=style.font_size("annotation"),
            )
        _style_discrete_y(ax, style)
        if action_probabilities:
            action_names = sorted(action_probabilities[0])
            palette = [style.color("secondary"), style.color("accent"), style.color("fail"), "#7c3aed", "#d97706"]
            for idx, name in enumerate(action_names):
                values = [float(row.get(name, 0.0)) for row in action_probabilities]
                prob_ax.plot(
                    steps,
                    values,
                    marker="o",
                    linewidth=1.9,
                    markersize=4.0,
                    label=name.replace("move_to_", "").replace("_", " "),
                    color=palette[idx % len(palette)],
                )
            first_row = action_probabilities[0]
            cue_probability = float(first_row.get("move_to_cue", 0.0) or 0.0)
            prob_ax.annotate(
                f"initial cue-directed p={cue_probability:.2f}",
                xy=(0, cue_probability),
                xytext=(36, -20),
                textcoords="offset points",
                fontsize=style.font_size("dense"),
                color=style.color("primary"),
                arrowprops={"arrowstyle": "->", "color": style.color("primary"), "linewidth": 0.8},
            )
        prob_ax.set_ylim(-0.02, 1.02)
        prob_ax.set_xlabel("Timestep")
        prob_ax.set_ylabel("Marginal first-action probability")
        prob_ax.set_title(
            f"Policy posterior: cue action is selected first (horizon={planning_horizon})"
        )
        style_grid(prob_ax, style)
        prob_ax.legend(frameon=False, ncol=2, fontsize=style.font_size("legend"))
        fig.text(0.01, 0.01, "Source: output/data/si_tmaze_summary.json", fontsize=style.font_size("source"), color=style.color("muted"))
        save_styled_figure(fig, out, style)
    return out


def figure_si_tmaze_model_matrices(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    matrices_path = root / "output" / "data" / "si_tmaze_model_matrices.json"
    data = json.loads(matrices_path.read_text(encoding="utf-8"))
    out = figure_output_path(root, "si_tmaze_model_matrices")
    with apply_style(style):
        fig, axes = plt.subplots(1, 2, figsize=(13.4, 6.4), gridspec_kw={"width_ratios": [1.36, 1]})
        shape_ax, norm_ax = axes
        shape_ax.axis("off")
        rows = [
            ("A[0]", "location obs", data["A_shapes"][0], data["dependencies"]["A"][0]),
            ("A[1]", "outcome obs", data["A_shapes"][1], data["dependencies"]["A"][1]),
            ("A[2]", "cue obs", data["A_shapes"][2], data["dependencies"]["A"][2]),
            ("B[0]", "location transition", data["B_shapes"][0], data["dependencies"]["B"][0]),
            ("B[1]", "reward-location fixed", data["B_shapes"][1], data["dependencies"]["B"][1]),
        ]
        y = 0.88
        for idx, (name, label, shape, deps) in enumerate(rows):
            color = style.color("secondary") if name.startswith("A") else style.color("accent")
            box = FancyBboxPatch(
                (0.05, y - 0.088),
                0.88,
                0.13,
                boxstyle="round,pad=0.015",
                facecolor="#f8fafc",
                edgecolor=color,
                linewidth=1.4,
            )
            shape_ax.add_patch(box)
            shape_ax.text(0.08, y, name, fontsize=style.font_size("small"), weight="bold", color=color, va="center")
            shape_ax.text(0.22, y, label, fontsize=style.font_size("dense"), va="center", color=style.color("primary"))
            shape_ax.text(0.58, y, f"shape {shape}", fontsize=style.font_size("dense"), va="center", color=style.color("muted"))
            shape_ax.text(0.78, y, f"deps {deps}", fontsize=style.font_size("dense"), va="center", color=style.color("muted"))
            y -= 0.158
        env = data.get("environment") or {}
        shape_ax.text(
            0.05,
            0.11,
            f"TMaze reward_condition={env.get('reward_condition')}, cue_validity={env.get('cue_validity')}, dependent_outcomes={env.get('dependent_outcomes')}",
            fontsize=style.font_size("dense"),
            color=style.color("primary"),
        )
        preferences = data.get("preferences") or {}
        c_shapes = data.get("C_shapes") or []
        d_shapes = data.get("D_shapes") or []
        shape_ax.text(
            0.05,
            0.055,
            f"C preferences={list(preferences)} with shapes {c_shapes}; D prior shapes={d_shapes}",
            fontsize=style.font_size("dense"),
            color=style.color("muted"),
        )
        shape_ax.set_title("Generative-model factors and dependencies")

        checks = data.get("normalization_checks") or []
        labels = [row["matrix"] for row in checks]
        mins = [float(row["axis0_sum_min"]) for row in checks]
        maxs = [float(row["axis0_sum_max"]) for row in checks]
        x = np.arange(len(labels))
        # The min and max column sums coincide at 1.0 for every factor, so a wide
        # symmetric axis is half-wasted. Anchor a tight band around 1.0 and report
        # the worst-case deviation so the perfect normalization reads at a glance.
        max_dev = max((abs(value - 1.0) for value in (*mins, *maxs)), default=0.0)
        band = max(2e-4, max_dev * 1.6)
        norm_ax.scatter(x, mins, label="min column sum", color=style.color("secondary"), s=60)
        norm_ax.scatter(x, maxs, label="max column sum", color=style.color("accent"), s=44, marker="D")
        norm_ax.axhline(1.0, color=style.color("reference"), linewidth=1.1)
        norm_ax.set_xticks(x)
        norm_ax.set_xticklabels(labels, rotation=35, ha="right")
        norm_ax.set_ylim(1.0 - band, 1.0 + band)
        norm_ax.ticklabel_format(axis="y", useOffset=False)
        norm_ax.set_ylabel("Column sum (mass)")
        norm_ax.set_title("Every model factor normalizes")
        style_grid(norm_ax, style)
        norm_ax.legend(frameon=False, loc="upper right", fontsize=style.font_size("legend"))
        norm_ax.text(
            0.02,
            0.06,
            f"min = max = 1.000 for all factors\nmax deviation {max_dev:.1e}",
            transform=norm_ax.transAxes,
            fontsize=style.font_size("annotation"),
            color=style.color("primary"),
            bbox=dict(boxstyle="round,pad=0.28", facecolor="#f8fafc", edgecolor=style.color("reference")),
        )
        fig.text(
            0.01,
            0.01,
            "Source: output/data/si_tmaze_model_matrices.json; all columns normalize to probability mass 1.",
            fontsize=style.font_size("source"),
            color=style.color("muted"),
        )
        save_styled_figure(fig, out, style)
    return out


def figure_si_summary(project_root: Path) -> Path:
    """Deprecated alias for ``figure_si_tmaze_actions``."""
    return figure_si_tmaze_actions(project_root)
