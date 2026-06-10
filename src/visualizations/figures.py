"""Publication figures for analytical and pymdp tracks."""

from __future__ import annotations

import json
import textwrap
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
from matplotlib.ticker import FixedFormatter, FixedLocator, MaxNLocator

from analytical.hyperparameters import lambda_grid, load_hyperparameters
from analytical.sweep_io import read_parameter_sweep
from .figure_io import save_figure_png
from .figure_helpers import save_styled_figure, style_grid
from .figure_registry import figure_output_path, load_figure_registry
from .figure_style import FigureStyleConfig, apply_style, load_figure_style
from .figures_diagrams import (
    figure_gnn_ontology_concordance,
    figure_invariant_dashboard,
    figure_lean_boundary_status,
    figure_multi_track_architecture,
    figure_tmaze_schematic,
)
from .figures_sheaf import figure_sheaf_coverage_heatmap, figure_sheaf_layers_overview


def _read_sweep(path: Path) -> tuple[list[float], list[float], list[float]]:
    rows = read_parameter_sweep(path)
    lambdas = [row["lambda"] for row in rows]
    closed = [row["closed_form_mi"] for row in rows]
    empirical = [row["empirical_mi"] for row in rows]
    return lambdas, closed, empirical


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


def figure_ising_mi_curve(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    sweep = root / "output" / "data" / "parameter_sweep.csv"
    lambdas, closed, empirical = _read_sweep(sweep)
    out = figure_output_path(root, "ising_mi_curve")
    with apply_style(style):
        fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.5), gridspec_kw={"width_ratios": [2.2, 1]})
        ax_main, ax_resid = axes
        ax_main.plot(lambdas, closed, label="closed-form MI", color=style.color("primary"), linewidth=2)
        ax_main.set_xlabel(r"Coupling strength $\lambda$")
        ax_main.set_ylabel("Teacher-student MI (nats)")
        ax_main.set_title("Coupling increases transferable information")
        if lambdas and closed:
            ax_main.annotate(
                "stronger coupling\nmeans more teacher\ninformation to distill",
                xy=(lambdas[-1], closed[-1]),
                xytext=(-140, -48),
                textcoords="offset points",
                fontsize=style.font_size("annotation"),
                color=style.color("primary"),
                arrowprops={"arrowstyle": "->", "color": style.color("muted"), "linewidth": 0.9},
            )
        style_grid(ax_main, style)
        ax_main.legend(frameon=False, fontsize=style.font_size("legend"))
        residuals = [e - c for e, c in zip(empirical, closed, strict=True)]
        ax_resid.axhline(0.0, color=style.color("reference"), linewidth=1)
        markerline, stemlines, baseline = ax_resid.stem(lambdas, residuals)
        plt.setp(markerline, color=style.color("accent"), markersize=4)
        plt.setp(stemlines, color=style.color("accent"), linewidth=1.0)
        plt.setp(baseline, visible=False)
        ax_resid.set_xlabel(r"$\lambda$")
        ax_resid.set_ylabel("recompute - closed (nats)")
        ax_resid.set_title("Exact recompute check", fontsize=style.font_size("small"))
        style_grid(ax_resid, style)
        save_styled_figure(fig, out, style)
    return out


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
        norm_ax.scatter(x, mins, label="min column sum", color=style.color("secondary"), s=44)
        norm_ax.scatter(x, maxs, label="max column sum", color=style.color("accent"), s=44, marker="D")
        norm_ax.axhline(1.0, color=style.color("reference"), linewidth=1.1)
        norm_ax.set_xticks(x)
        norm_ax.set_xticklabels(labels, rotation=35, ha="right")
        norm_ax.set_ylim(0.94, 1.06)
        norm_ax.set_ylabel("Probability mass")
        norm_ax.set_title("Every model factor normalizes")
        style_grid(norm_ax, style)
        norm_ax.legend(frameon=False, loc="upper right")
        fig.text(
            0.01,
            0.01,
            "Source: output/data/si_tmaze_model_matrices.json; all columns normalize to probability mass 1.",
            fontsize=style.font_size("source"),
            color=style.color("muted"),
        )
        save_styled_figure(fig, out, style)
    return out


def figure_distillation_divergence_geometry(project_root: Path) -> Path:
    """Render first-principles divergence geometry for teacher/student policies."""
    root = project_root.resolve()
    style = load_figure_style(root)
    data_path = root / "output" / "data" / "firstprinciples" / "divergence_demo.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    teacher = [float(value) for value in data.get("teacher") or []]
    student = [float(value) for value in data.get("student") or []]
    measures = [
        ("reverse KL", float(data.get("reverse_kl", 0.0))),
        ("forward KL", float(data.get("forward_kl", 0.0))),
        ("Jensen-Shannon", float(data.get("jensen_shannon", 0.0))),
        ("alpha 0.5", float(data.get("alpha_divergence_0_5", 0.0))),
        ("clipped RKL", float(data.get("clipped_reverse_kl", 0.0))),
    ]
    concentration = data.get("mode_concentration") or {}
    entropy_rows = [
        ("teacher H", float(concentration.get("teacher_entropy", 0.0))),
        ("student H", float(concentration.get("student_entropy", 0.0))),
    ]
    entropy_gap = float(concentration.get("entropy_gap", 0.0))
    mode_seeking = bool(concentration.get("mode_seeking", False))
    out = figure_output_path(root, "distillation_divergence_geometry")
    with apply_style(style):
        fig, axes = plt.subplots(1, 3, figsize=(14.0, 5.3), gridspec_kw={"width_ratios": [1.0, 1.28, 0.9]})
        mass_ax, div_ax, entropy_ax = axes
        x = np.arange(len(teacher))
        width = 0.36
        mass_ax.bar(x - width / 2, teacher, width, label="teacher p", color=style.color("secondary"))
        mass_ax.bar(x + width / 2, student, width, label="student q", color=style.color("accent"))
        mass_ax.set_xticks(x, [f"mode {idx + 1}" for idx in x])
        mass_ax.set_ylim(0.0, 1.0)
        mass_ax.set_ylabel("Probability mass")
        mass_ax.set_title("Teacher/student mass on finite support")
        style_grid(mass_ax, style)
        mass_ax.legend(frameon=False, fontsize=style.font_size("legend"))

        names = [name for name, _value in measures]
        values = [value for _name, value in measures]
        colors = [style.color("accent"), style.color("secondary"), "#7c3aed", "#b45309", style.color("fail")]
        bars = div_ax.bar(np.arange(len(values)), values, color=colors, alpha=0.88)
        div_ax.set_xticks(np.arange(len(values)), [name.replace(" ", "\n") for name in names], fontsize=style.font_size("dense"))
        div_ax.set_ylabel("Divergence (nats)")
        div_ax.set_title("Objective choice changes the penalty")
        style_grid(div_ax, style)
        for bar, value in zip(bars, values, strict=True):
            div_ax.text(bar.get_x() + bar.get_width() / 2, value + 0.006, f"{value:.3f}", ha="center", fontsize=style.font_size("annotation"))
        entropy_names = [name for name, _value in entropy_rows]
        entropy_values = [value for _name, value in entropy_rows]
        entropy_colors = [style.color("secondary"), style.color("accent")]
        entropy_ax.barh(np.arange(len(entropy_values)), entropy_values, color=entropy_colors, alpha=0.88)
        entropy_ax.set_yticks(np.arange(len(entropy_values)), entropy_names, fontsize=style.font_size("dense"))
        entropy_ax.set_xlabel("Entropy (nats)")
        entropy_ax.set_title("Entropy check is example-specific")
        entropy_ax.set_xlim(0, max(1.0, max(entropy_values, default=0.0) * 1.28))
        style_grid(entropy_ax, style)
        for y, value in enumerate(entropy_values):
            entropy_ax.text(value + 0.025, y, f"{value:.3f}", va="center", fontsize=style.font_size("dense"))
        entropy_ax.text(
            0.02,
            0.05,
            f"H gap={entropy_gap:+.3f}\nmode-seeking={mode_seeking}\nnot a universal KL law",
            transform=entropy_ax.transAxes,
            fontsize=style.font_size("annotation"),
            color=style.color("primary"),
            bbox=dict(boxstyle="round,pad=0.28", facecolor="#f8fafc", edgecolor=style.color("reference")),
        )
        fig.text(
            0.01,
            0.01,
            "Source: output/data/firstprinciples/divergence_demo.json; realized behavior depends on support and optimization.",
            fontsize=style.font_size("source"),
            color=style.color("muted"),
        )
        save_styled_figure(fig, out, style)
    return out


def figure_exposure_bias_recovery(project_root: Path) -> Path:
    """Render off-policy compounding versus on-policy correction curves."""
    root = project_root.resolve()
    style = load_figure_style(root)
    data_path = root / "output" / "data" / "firstprinciples" / "exposure_bias_demo.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    curves = data.get("curves") or {}
    off_policy = [float(value) for value in curves.get("off_policy") or []]
    on_policy = [float(value) for value in curves.get("on_policy") or []]
    gap = data.get("gap") or {}
    fixed_point = data.get("on_policy_fixed_point") or gap.get("on_policy_fixed_point")
    xs = np.arange(max(len(off_policy), len(on_policy)))
    out = figure_output_path(root, "exposure_bias_recovery")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(9.8, 5.2))
        ax.plot(
            xs[: len(off_policy)], off_policy, marker="o", linewidth=2.2, color=style.color("fail"), label="off-policy"
        )
        ax.plot(
            xs[: len(on_policy)], on_policy, marker="s", linewidth=2.2, color=style.color("pass"), label="on-policy"
        )
        if off_policy and on_policy:
            ax.fill_between(
                xs[: min(len(off_policy), len(on_policy))],
                off_policy[: min(len(off_policy), len(on_policy))],
                on_policy[: min(len(off_policy), len(on_policy))],
                color=style.color("secondary"),
                alpha=0.10,
                label="terminal recovery gap",
            )
            terminal_x = min(len(off_policy), len(on_policy)) - 1
            ax.annotate(
                f"gap={float(gap.get('terminal_gap', 0.0)):.3f}",
                xy=(terminal_x, on_policy[terminal_x]),
                xytext=(-76, -34),
                textcoords="offset points",
                fontsize=style.font_size("annotation"),
                color=style.color("primary"),
                arrowprops={"arrowstyle": "->", "color": style.color("primary"), "linewidth": 0.8},
            )
            ax.scatter(
                [terminal_x, terminal_x],
                [off_policy[terminal_x], on_policy[terminal_x]],
                s=46,
                color=[style.color("fail"), style.color("pass")],
                zorder=4,
            )
            ax.text(
                terminal_x,
                off_policy[terminal_x] - 0.055,
                f"{off_policy[terminal_x]:.3f}",
                ha="center",
                va="top",
                fontsize=style.font_size("annotation"),
                color=style.color("fail"),
            )
            ax.text(
                terminal_x,
                on_policy[terminal_x] + 0.035,
                f"{on_policy[terminal_x]:.3f}",
                ha="center",
                va="bottom",
                fontsize=style.font_size("annotation"),
                color=style.color("pass"),
            )
        if fixed_point is not None:
            fixed_value = float(fixed_point)
            ax.axhline(
                fixed_value,
                color=style.color("reference"),
                linewidth=1.2,
                linestyle=":",
                label="on-policy fixed point",
            )
            ax.text(
                0.35,
                fixed_value + 0.035,
                f"fixed point={fixed_value:.3f}",
                transform=ax.get_yaxis_transform(),
                fontsize=style.font_size("annotation"),
                color=style.color("reference"),
            )
        ax.set_xlabel("Generated step")
        ax.set_ylabel("Expected correctness")
        ax.set_ylim(0.0, 1.02)
        ax.set_title("On-policy correction arrests compounding error")
        style_grid(ax, style)
        ax.legend(frameon=False, fontsize=style.font_size("legend"))
        fig.text(
            0.01,
            0.01,
            "Source: output/data/firstprinciples/exposure_bias_demo.json",
            fontsize=style.font_size("source"),
            color=style.color("muted"),
        )
        save_styled_figure(fig, out, style)
    return out


def figure_classroom_distillation_signal(project_root: Path) -> Path:
    """Render teacher/student policy gaps in the two-agent classroom artifact."""
    root = project_root.resolve()
    style = load_figure_style(root)
    data_path = root / "output" / "data" / "firstprinciples" / "classroom.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    rows = data.get("per_step") or []
    actions = rows[0].get("actions") if rows else []
    reverse = [float(row.get("reverse_kl", 0.0)) for row in rows]
    forward = [float(row.get("forward_kl", 0.0)) for row in rows]
    jsd = [float(row.get("jensen_shannon", 0.0)) for row in rows]
    teacher_argmaxes: list[int] = []
    student_argmaxes: list[int] = []
    for row in rows:
        teacher_policy = [float(value) for value in row.get("teacher") or []]
        student_policy = [float(value) for value in row.get("student") or []]
        teacher_argmaxes.append(int(np.argmax(teacher_policy)) if teacher_policy else -1)
        student_argmaxes.append(int(np.argmax(student_policy)) if student_policy else -1)
    agreement_count = sum(
        1
        for teacher_idx, student_idx in zip(teacher_argmaxes, student_argmaxes, strict=True)
        if teacher_idx == student_idx
    )
    deltas = np.array(
        [
            [float(t) - float(s) for t, s in zip(row.get("teacher") or [], row.get("student") or [], strict=True)]
            for row in rows
        ]
    )
    out = figure_output_path(root, "classroom_distillation_signal")
    with apply_style(style):
        fig, axes = plt.subplots(
            1,
            2,
            figsize=(12.8, 5.4),
            gridspec_kw={"width_ratios": [1.05, 1.42]},
            constrained_layout=True,
        )
        div_ax, heat_ax = axes
        xs = np.arange(len(rows))
        div_ax.plot(xs, reverse, marker="o", linewidth=2.0, color=style.color("accent"), label="reverse KL")
        div_ax.plot(xs, forward, marker="s", linewidth=2.0, color=style.color("secondary"), label="forward KL")
        div_ax.plot(xs, jsd, marker="^", linewidth=1.8, color="#7c3aed", label="Jensen-Shannon")
        div_ax.set_xlabel("Classroom step")
        div_ax.set_ylabel("Divergence (nats)")
        div_ax.set_title("Per-step divergence")
        style_grid(div_ax, style)
        div_ax.legend(frameon=False, fontsize=style.font_size("legend"))
        div_ax.text(
            0.02,
            0.95,
            f"argmax agreement {agreement_count}/{len(rows)}",
            transform=div_ax.transAxes,
            va="top",
            fontsize=style.font_size("annotation"),
            color=style.color("primary"),
            bbox=dict(boxstyle="round,pad=0.28", facecolor="#f8fafc", edgecolor=style.color("reference")),
        )

        if deltas.size:
            image = heat_ax.imshow(deltas, cmap="coolwarm", aspect="auto", vmin=-1.0, vmax=1.0)
            action_labels = [str(action).replace("move_to_", "").replace("_", " ") for action in actions]
            heat_ax.set_xticks(
                range(len(actions)),
                [str(action).replace("move_to_", "").replace("_", "\n") for action in actions],
                fontsize=style.font_size("dense"),
            )
            heat_ax.set_yticks(
                range(len(rows)),
                [
                    "\n".join(
                        [
                            f"step {row.get('step')}",
                            f"T:{action_labels[teacher_argmaxes[idx]] if 0 <= teacher_argmaxes[idx] < len(action_labels) else '?'}",
                            f"S:{action_labels[student_argmaxes[idx]] if 0 <= student_argmaxes[idx] < len(action_labels) else '?'}",
                        ]
                    )
                    for idx, row in enumerate(rows)
                ],
                fontsize=style.font_size("dense"),
            )
            heat_ax.set_xlabel("Action")
            heat_ax.set_ylabel("Classroom step")
            for i in range(deltas.shape[0]):
                for j in range(deltas.shape[1]):
                    heat_ax.text(
                        j,
                        i,
                        f"{deltas[i, j]:+.2f}",
                        ha="center",
                        va="center",
                        fontsize=style.font_size("annotation"),
                    )
            cbar = fig.colorbar(image, ax=heat_ax, shrink=0.84)
            cbar.set_label("teacher p - student q")
        heat_ax.set_title("Teacher-student mass gap")
        fig.suptitle("Two-agent classroom distillation signal", fontsize=style.font_size("title"))
        fig.text(
            0.01,
            0.01,
            "Source: output/data/firstprinciples/classroom.json",
            fontsize=style.font_size("source"),
            color=style.color("muted"),
        )
        save_figure_png(fig, out, dpi=style.dpi, facecolor="white", transparent=style.transparent)
    return out


def figure_energy_decomposition(project_root: Path) -> Path:
    """Render the VFE and EFE decompositions from the energy demo artifact."""
    root = project_root.resolve()
    style = load_figure_style(root)
    data = json.loads((root / "output" / "data" / "firstprinciples" / "energy_demo.json").read_text(encoding="utf-8"))
    vfe = data.get("vfe_at_prior") or {}
    efe = data.get("efe") or {}
    complexity = float(vfe.get("complexity", 0.0))
    accuracy = float(vfe.get("accuracy", 0.0))
    free_energy = float(vfe.get("vfe_complexity_accuracy", complexity - accuracy))
    risk = float(efe.get("risk", 0.0))
    ambiguity = float(efe.get("ambiguity", 0.0))
    epistemic = float(efe.get("epistemic_value", 0.0))
    pragmatic = float(efe.get("pragmatic_value", 0.0))
    out = figure_output_path(root, "energy_decomposition")
    with apply_style(style):
        fig, axes = plt.subplots(1, 2, figsize=(13.4, 5.3), gridspec_kw={"wspace": 0.34})
        vfe_ax, efe_ax = axes
        vfe_labels = [
            "complexity\n$D_{KL}(q\\|p(s))$",
            "accuracy term\n$E_q[\\ln p(o|s)]$",
            "VFE\n$F=C-A$",
        ]
        vfe_values = [complexity, accuracy, free_energy]
        vfe_colors = [style.color("secondary"), style.color("accent"), style.color("primary")]
        vfe_ax.bar(vfe_labels, vfe_values, color=vfe_colors)
        vfe_ax.axhline(0.0, color=style.color("reference"), linewidth=0.8)
        vfe_ax.set_ylabel("nats")
        vfe_ax.set_title("VFE at prior: complexity is zero", fontsize=style.font_size("small"))
        for i, v in enumerate(vfe_values):
            vfe_ax.text(i, v, f"{v:.3f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=style.font_size("annotation"))
        vfe_ax.annotate(
            "q = prior, so\ncomplexity = 0",
            xy=(0, complexity),
            xytext=(0.07, 0.32),
            textcoords="axes fraction",
            arrowprops={"arrowstyle": "->", "lw": 0.9, "color": style.color("muted")},
            fontsize=style.font_size("annotation"),
            color=style.color("muted"),
        )
        vfe_ax.annotate(
            "F = 0 - A\npositive surprisal",
            xy=(2, free_energy),
            xytext=(0.42, 0.77),
            textcoords="axes fraction",
            arrowprops={"arrowstyle": "->", "lw": 0.9, "color": style.color("muted")},
            fontsize=style.font_size("annotation"),
            color=style.color("primary"),
        )
        style_grid(vfe_ax, style)

        efe_labels = [
            "risk\n$D_{KL}(q(o)\\|p(o))$",
            "ambiguity\n$E[H[p(o|s)]]$",
            "epistemic\n$I(o;s)$",
            "pragmatic\n$E[\\ln p(o)]$",
        ]
        efe_values = [risk, ambiguity, epistemic, pragmatic]
        efe_colors = [style.color("fail"), style.color("muted"), style.color("accent"), style.color("secondary")]
        efe_ax.bar(efe_labels, efe_values, color=efe_colors)
        efe_ax.axhline(0.0, color=style.color("reference"), linewidth=0.8)
        efe_ax.set_ylabel("nats")
        efe_ax.set_title("EFE sign convention: G = risk + ambiguity - value", fontsize=style.font_size("small"))
        for i, v in enumerate(efe_values):
            efe_ax.text(i, v, f"{v:.3f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=style.font_size("annotation"))
        efe_ax.text(
            0.02,
            0.93,
            "risk + ambiguity\nminus epistemic/pragmatic value",
            transform=efe_ax.transAxes,
            fontsize=style.font_size("annotation"),
            color=style.color("primary"),
            bbox=dict(boxstyle="round,pad=0.28", facecolor="#f8fafc", edgecolor=style.color("reference")),
        )
        style_grid(efe_ax, style)
        fig.suptitle("Energy terms explain what the student is matching", fontsize=style.font_size("title"), y=0.98)
        fig.text(
            0.99,
            0.925,
            "Source: output/data/firstprinciples/energy_demo.json",
            fontsize=style.font_size("source"),
            color=style.color("muted"),
            ha="right",
        )
        fig.subplots_adjust(left=0.07, right=0.98, bottom=0.18, top=0.82, wspace=0.32)
        save_figure_png(fig, out, dpi=style.dpi, facecolor="white", transparent=style.transparent)
    return out


def figure_parallel_convergence(project_root: Path) -> Path:
    """Two frameworks, one answer: ML distillation converging to the AIF posterior."""
    root = project_root.resolve()
    style = load_figure_style(root)
    data = json.loads((root / "output" / "data" / "firstprinciples" / "parallel_demo.json").read_text(encoding="utf-8"))
    steps = [int(s) for s in data.get("trajectory_steps") or []]
    losses = [max(float(v), 1e-12) for v in data.get("loss_trajectory") or []]
    teacher = [float(v) for v in data.get("active_inference_teacher_posterior") or []]
    student = [float(v) for v in data.get("ml_distilled_student") or []]
    vfe = float(data.get("student_free_energy", 0.0))
    neg_log_ev = float(data.get("neg_log_evidence", 0.0))
    out = figure_output_path(root, "parallel_convergence")
    with apply_style(style):
        fig, axes = plt.subplots(
            1,
            2,
            figsize=(12.4, 5.0),
            gridspec_kw={"width_ratios": [1.28, 1.0]},
            constrained_layout=True,
        )
        loss_ax, bar_ax = axes
        loss_ax.semilogy(steps, losses, marker="o", linewidth=2.2, color=style.color("accent"))
        loss_ax.set_xlabel("Gradient step")
        loss_ax.set_ylabel(r"reverse KL $D_{KL}(\pi_S\|\pi_T)$ (nats)")
        loss_ax.set_title("Reverse-KL training")
        style_grid(loss_ax, style)

        idx = np.arange(len(teacher))
        width = 0.38
        bar_ax.bar(idx - width / 2, teacher, width, label="active inference: posterior $p(s\\mid o)$", color=style.color("secondary"))
        bar_ax.bar(idx + width / 2, student, width, label="ML: distilled student $\\pi_S$", color=style.color("accent"))
        bar_ax.set_xticks(list(idx))
        bar_ax.set_xticklabels([f"state {i}" for i in idx])
        bar_ax.set_ylabel("probability")
        bar_ax.set_title("Recovered posterior")
        bar_ax.legend(
            frameon=False,
            fontsize=style.font_size("legend"),
            loc="center right",
        )
        for i, (t, s) in enumerate(zip(teacher, student, strict=False)):
            bar_ax.text(i - width / 2, t, f"{t:.2f}", ha="center", va="bottom", fontsize=style.font_size("annotation"))
            bar_ax.text(i + width / 2, s, f"{s:.2f}", ha="center", va="bottom", fontsize=style.font_size("annotation"))
        bar_ax.set_ylim(0.0, max(max(teacher), max(student)) * 1.22)
        bar_ax.text(
            0.02,
            0.92,
            f"VFE = {vfe:.3f} nats = -ln p(o) = {neg_log_ev:.3f}",
            transform=bar_ax.transAxes,
            fontsize=style.font_size("annotation"),
            color=style.color("primary"),
            bbox=dict(boxstyle="round,pad=0.28", facecolor="#f8fafc", edgecolor=style.color("reference")),
        )
        style_grid(bar_ax, style)
        fig.suptitle(
            "Two frameworks, one posterior: ML distillation reaches the active-inference posterior",
            fontsize=style.font_size("title"),
        )
        fig.text(0.01, 0.01, "Source: output/data/firstprinciples/parallel_demo.json", fontsize=style.font_size("source"), color=style.color("muted"))
        save_styled_figure(fig, out, style)
    return out


def figure_diversity_tradeoff(project_root: Path) -> Path:
    """Pass@1 (greedy, temperature-invariant) vs Pass@k (collapses under sharpening)."""
    root = project_root.resolve()
    style = load_figure_style(root)
    data = json.loads((root / "output" / "data" / "firstprinciples" / "diversity_demo.json").read_text(encoding="utf-8"))
    temps = [float(t) for t in data.get("temperatures") or []]
    pass_k = [float(v) for v in data.get("pass_at_k") or []]
    greedy = float(data.get("greedy_pass_at_1", 0.0))
    k = int(data.get("k", 0))
    out = figure_output_path(root, "diversity_tradeoff")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(9.8, 5.0))
        ax.plot(temps, pass_k, marker="o", linewidth=2.4, color=style.color("accent"), label=f"sampling Pass@{k}")
        ax.axhline(greedy, color=style.color("secondary"), linewidth=2.0, linestyle="--", label="greedy Pass@1 (temperature-invariant)")
        ax.set_xscale("log")
        ax.xaxis.set_major_locator(FixedLocator(temps))
        ax.xaxis.set_minor_locator(FixedLocator([]))
        ax.xaxis.set_major_formatter(FixedFormatter([f"{temp:g}" for temp in temps]))
        if temps and pass_k:
            endpoints = [(temps[0], pass_k[0], (20, -14)), (temps[-1], pass_k[-1], (-52, -18))]
            for temp, pass_value, offset in endpoints:
                ax.annotate(
                    f"{pass_value:.3f}",
                    xy=(temp, pass_value),
                    xytext=offset,
                    textcoords="offset points",
                    fontsize=style.font_size("annotation"),
                    color=style.color("primary"),
                    arrowprops={"arrowstyle": "->", "color": style.color("muted"), "linewidth": 0.8},
                )
        ax.text(
            0.04,
            0.12,
            rf"Pass@k = 1 - (1 - p)^k; k={k}",
            transform=ax.transAxes,
            fontsize=style.font_size("annotation"),
            color=style.color("primary"),
            bbox=dict(boxstyle="round,pad=0.28", facecolor="#f8fafc", edgecolor=style.color("reference")),
        )
        ax.set_xlabel(r"student temperature $\tau$ (low = sharper / reverse-KL)")
        ax.set_ylabel("success probability")
        ax.set_title(f"Sharpening costs Pass@{k} coverage; greedy Pass@1 is temperature-invariant")
        ax.legend(frameon=False, fontsize=style.font_size("legend"), loc="best")
        style_grid(ax, style)
        fig.text(0.01, 0.01, "Source: output/data/firstprinciples/diversity_demo.json", fontsize=style.font_size("source"), color=style.color("muted"))
        save_styled_figure(fig, out, style)
    return out


def figure_si_summary(project_root: Path) -> Path:
    """Deprecated alias for ``figure_si_tmaze_actions``."""
    return figure_si_tmaze_actions(project_root)


def figure_free_energy_curve(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    from analytical.decomposition import free_energy_against_entangled_prior
    from analytical.bernoulli_toy import (
        ising_coupling,
        ising_joint_posterior,
        ising_mutual_information,
        symmetric_mean_field_prior,
    )
    from analytical.free_energy import kl_divergence, total_correlation
    from analytical.joint_dist import mean_field_to_joint

    hp_lambdas = lambda_grid(load_hyperparameters())
    mf = symmetric_mean_field_prior()
    mf_joint = mean_field_to_joint(mf)
    g0 = [np.zeros(2), np.zeros(2)]
    j = ising_coupling()
    kc = np.zeros((2, 2))
    exact_values = []
    mean_field_gaps = []
    mi_values = []
    for lam in hp_lambdas:
        q = ising_joint_posterior(float(lam))
        exact_values.append(free_energy_against_entangled_prior(q, mf, g0, j, kc, gamma=1.0, lam=float(lam)))
        mean_field_gaps.append(kl_divergence(q, mf_joint))
        mi_values.append(ising_mutual_information(float(lam)))
    out = figure_output_path(root, "free_energy_curve")
    with apply_style(style):
        fig, (curve_ax, decomp_ax) = plt.subplots(
            1,
            2,
            figsize=(12.6, 5.2),
            gridspec_kw={"width_ratios": [1.55, 1.0]},
        )
        curve_ax.plot(
            hp_lambdas,
            mean_field_gaps,
            linewidth=2.8,
            color=style.color("primary"),
            label=r"independent student gap $D_{KL}(q_\lambda\|q_0)$",
        )
        curve_ax.plot(
            hp_lambdas,
            mi_values,
            linewidth=1.7,
            linestyle=":",
            color=style.color("secondary"),
            label=r"mutual information $I(\lambda)$",
        )
        curve_ax.plot(
            hp_lambdas,
            exact_values,
            linewidth=2.0,
            linestyle="--",
            color=style.color("muted"),
            label=r"exact entangled target $F(q_\lambda;p_\lambda)=0$",
        )
        max_idx = int(np.argmax(mean_field_gaps))
        max_lam = float(hp_lambdas[max_idx])
        max_gap = float(mean_field_gaps[max_idx])
        exact_max = float(max(abs(value) for value in exact_values))
        curve_ax.scatter([max_lam], [max_gap], s=54, color=style.color("accent"), zorder=4)
        curve_ax.annotate(
            f"max gap {max_gap:.3f} nats\nat λ={max_lam:.1f}",
            xy=(max_lam, max_gap),
            xytext=(max_lam - 1.55, max_gap * 0.72),
            arrowprops={"arrowstyle": "->", "color": style.color("muted"), "lw": 1.0},
            fontsize=style.font_size("annotation"),
            color=style.color("primary"),
        )
        curve_ax.set_xlabel(r"Coupling strength $\lambda$")
        curve_ax.set_ylabel("nats")
        curve_ax.set_title("Mean-field students pay the missing-coupling gap")
        curve_ax.set_ylim(-0.04, max(0.08, max_gap * 1.17))
        style_grid(curve_ax, style)
        curve_ax.legend(frameon=False, fontsize=style.font_size("legend"), loc="upper left")

        q_max = ising_joint_posterior(max_lam)
        tc_max = float(total_correlation(q_max))
        decomp_labels = ["exact target\nF=0", "coupling\nprior term", "total corr.\nI(λ)", "mean-field\ngap"]
        decomp_values = [0.0, -tc_max, tc_max, max_gap]
        decomp_colors = [
            style.color("muted"),
            "#b91c1c",
            style.color("secondary"),
            style.color("accent"),
        ]
        bars = decomp_ax.bar(range(len(decomp_values)), decomp_values, color=decomp_colors)
        decomp_ax.axhline(0, color=style.color("reference"), linewidth=1.0)
        decomp_ax.set_xticks(range(len(decomp_labels)), decomp_labels, fontsize=style.font_size("dense"))
        decomp_ax.set_ylabel("nats at λmax")
        decomp_ax.set_title("Why the exact-target VFE is 0")
        decomp_ax.set_ylim(-max_gap * 1.35, max_gap * 1.35)
        for bar, value in zip(bars, decomp_values, strict=True):
            y = value + (0.03 if value >= 0 else -0.03)
            decomp_ax.text(
                bar.get_x() + bar.get_width() / 2,
                y,
                f"{value:+.3f}",
                ha="center",
                va="bottom" if value >= 0 else "top",
                fontsize=style.font_size("annotation"),
                color=style.color("primary"),
            )
        decomp_ax.text(
            0.03,
            0.94,
            f"max |exact F| = {exact_max:.1e}\nsource: analytical sweep",
            transform=decomp_ax.transAxes,
            fontsize=style.font_size("source"),
            color=style.color("muted"),
            va="top",
        )
        style_grid(decomp_ax, style)
        fig.suptitle("Privileged coupling creates the free-energy gap", fontsize=style.font_size("title"), y=0.98)
        fig.text(
            0.01,
            0.015,
            "Source: src/analytical/decomposition.py; output/data/parameter_sweep.csv",
            fontsize=style.font_size("source"),
            color=style.color("muted"),
        )
        save_styled_figure(fig, out, style)
    return out


def figure_semantic_gluing_graph(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    from manuscript.sheaf.semantic import build_validation_dependency_graph

    graph = build_validation_dependency_graph(root)
    selected = [
        "output/data/sheaf_gluing_certificate.json",
        "output/data/sheaf_evidence_crosswalk.json",
        "output/data/validation_dependency_graph.json",
        "output/data/artifact_provenance.json",
        "output/reports/replay_matrix.json",
        "output/data/sensitivity_sweep.json",
        "output/data/uncertainty_summary.json",
        "output/data/toy_benchmark_matrix.json",
        "output/data/interop_roundtrip_report.json",
        "output/reports/model_checking_witnesses.json",
        "output/reports/adversarial_audit.json",
        "output/data/evidence_field_index.json",
        "output/reports/release_bundle_manifest.json",
        "output/data/theorem_traceability_matrix.json",
    ]
    artifacts = graph.get("artifacts") or {}
    out = figure_output_path(root, "semantic_gluing_graph")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(13.2, 9.2))
        ax.axis("off")
        producer_x, artifact_x, consumer_x = 0.05, 0.42, 0.78
        y_positions = np.linspace(0.86, 0.14, len(selected))
        ax.text(producer_x, 0.96, "Producer script", weight="bold", color=style.color("primary"))
        ax.text(artifact_x, 0.96, "Evidence artifact", weight="bold", color=style.color("primary"))
        ax.text(consumer_x, 0.96, "Consumer / gate", weight="bold", color=style.color("primary"))
        for y, rel in zip(y_positions, selected, strict=True):
            record = artifacts.get(rel, {})
            producer = str(record.get("producer", "?"))
            consumers = ", ".join(record.get("consumers") or record.get("validation_gates") or ["validate_outputs"])
            ok = bool(record.get("produced_by_configured_analysis"))
            box_color = style.color("pass") if ok else style.color("fail")
            ax.text(
                producer_x,
                y,
                producer,
                fontsize=style.font_size("dense"),
                va="center",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#f8fafc", edgecolor=box_color),
            )
            ax.text(
                artifact_x,
                y,
                rel.replace("output/", ""),
                fontsize=style.font_size("dense"),
                va="center",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#ffffff", edgecolor=style.color("secondary")),
            )
            ax.text(
                consumer_x,
                y,
                consumers,
                fontsize=style.font_size("dense"),
                va="center",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#f8fafc", edgecolor=style.color("accent")),
            )
            ax.annotate("", xy=(artifact_x - 0.02, y), xytext=(producer_x + 0.24, y), arrowprops={"arrowstyle": "->"})
            ax.annotate("", xy=(consumer_x - 0.02, y), xytext=(artifact_x + 0.29, y), arrowprops={"arrowstyle": "->"})
        ax.set_title("Every generated claim flows through a producer, artifact, and gate", loc="left", pad=16)
        save_styled_figure(fig, out, style)
    return out


def figure_theorem_traceability_graph(project_root: Path) -> Path:
    """Render theorem → proof dependency → witness links from generated JSON rows."""
    root = project_root.resolve()
    style = load_figure_style(root)
    theorem_path = root / "output" / "data" / "theorem_traceability_matrix.json"
    dependency_path = root / "output" / "data" / "proof_dependency_graph.json"
    if not theorem_path.is_file() or not dependency_path.is_file():
        from roadmap_tracks import write_sheaf_track_artifacts

        write_sheaf_track_artifacts(root)
    theorem = json.loads(theorem_path.read_text(encoding="utf-8"))
    dependency = json.loads(dependency_path.read_text(encoding="utf-8"))
    all_rows = theorem.get("rows") or []
    total_rows = len(all_rows)
    max_rows = 11
    shown_rows = all_rows[:max_rows]
    edges = dependency.get("edges") or []
    edge_count_by_theorem = {
        row.get("theorem", ""): sum(1 for edge in edges if edge.get("source") == row.get("theorem")) for row in shown_rows
    }
    shown_edge_total = sum(edge_count_by_theorem.values())
    witness_counts = {len(row.get("model_witnesses") or []) for row in shown_rows}
    collapse_witnesses = len(witness_counts) == 1
    row_fontsize = style.font_size("dense") if len(shown_rows) <= 10 else style.font_size("source")
    out = figure_output_path(root, "theorem_traceability_graph")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(10.8, max(5.6, 0.55 * len(shown_rows) + 1.2)))
        ax.axis("off")
        columns = [0.05, 0.56] if collapse_witnesses else [0.05, 0.42, 0.78]
        headers = ["Lean theorem", "Proof dependency rows"]
        if not collapse_witnesses:
            headers.append("Finite witnesses")
        for x, header in zip(columns, headers, strict=True):
            ax.text(x, 0.94, header, weight="bold", color=style.color("primary"), fontsize=style.font_size("annotation"))
        y_positions = np.linspace(0.82, 0.14, max(1, len(shown_rows)))
        for y, row in zip(y_positions, shown_rows, strict=False):
            theorem_id = str(row.get("theorem", ""))
            theorem_words = theorem_id.split("_")
            theorem_label = "\n".join(
                " ".join(theorem_words[index : index + 3]) for index in range(0, len(theorem_words), 3)
            )
            witness_count = len(row.get("model_witnesses") or [])
            linked = row.get("linked") is True
            edge_color = style.color("pass") if linked else style.color("fail")
            proof_label = f"{edge_count_by_theorem.get(theorem_id, 0)} dependency edges"
            witness_label = f"{witness_count} finite witnesses"
            ax.text(
                columns[0],
                y,
                theorem_label,
                fontsize=row_fontsize,
                va="center",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#f8fafc", edgecolor=edge_color),
            )
            ax.text(
                columns[1],
                y,
                proof_label,
                fontsize=row_fontsize,
                va="center",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#ffffff", edgecolor=style.color("secondary")),
            )
            ax.annotate("", xy=(columns[1] - 0.03, y), xytext=(columns[0] + 0.24, y), arrowprops={"arrowstyle": "->"})
            if not collapse_witnesses:
                ax.text(
                    columns[2],
                    y,
                    witness_label,
                    fontsize=row_fontsize,
                    va="center",
                    bbox=dict(boxstyle="round,pad=0.25", facecolor="#f8fafc", edgecolor=style.color("accent")),
                )
                ax.annotate("", xy=(columns[2] - 0.03, y), xytext=(columns[1] + 0.24, y), arrowprops={"arrowstyle": "->"})
        if total_rows > len(shown_rows):
            subtitle = (
                f"showing {len(shown_rows)} of {total_rows} theorem rows; "
                f"{shown_edge_total} dependency edges in the shown subset"
            )
        else:
            subtitle = f"all {total_rows} theorem rows shown; {shown_edge_total} dependency edges across the shown set"
        fig.text(0.05, 0.91, subtitle, fontsize=style.font_size("annotation"), color=style.color("muted"))
        if collapse_witnesses and witness_counts:
            fig.text(
                0.05,
                0.03,
                f"each theorem carries {next(iter(witness_counts))} finite witnesses",
                fontsize=style.font_size("annotation"),
                color=style.color("accent"),
            )
        ax.set_title("Lean theorem rows connect to dependencies and finite witnesses", loc="left", pad=16)
        save_styled_figure(fig, out, style)
    return out


def figure_causal_ablation_heatmap(project_root: Path) -> Path:
    """Render source-backed causal-ablation effects as topology × perturbation heatmap."""
    root = project_root.resolve()
    style = load_figure_style(root)
    report_path = root / "output" / "reports" / "ablation_sensitivity_report.json"
    if not report_path.is_file():
        from roadmap_tracks import write_sheaf_track_artifacts

        write_sheaf_track_artifacts(root)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    rows = report.get("rows") or []
    topologies = sorted({str(row.get("topology")) for row in rows if row.get("topology")})
    perturbations = sorted({str(row.get("perturbation")) for row in rows if row.get("perturbation")})
    matrix = np.zeros((len(topologies), len(perturbations)))
    for i, topology in enumerate(topologies):
        for j, perturbation in enumerate(perturbations):
            effects = [
                abs(float(row.get("effect", 0.0) or 0.0))
                for row in rows
                if row.get("topology") == topology and row.get("perturbation") == perturbation
            ]
            matrix[i, j] = max(effects) if effects else 0.0
    out = figure_output_path(root, "causal_ablation_heatmap")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(9.4, 5.4))
        image = ax.imshow(matrix, cmap="viridis", aspect="auto")
        ax.set_xticks(range(len(perturbations)), [label.replace("_", "\n") for label in perturbations], fontsize=style.font_size("dense"))
        ax.set_yticks(range(len(topologies)), topologies, fontsize=style.font_size("dense"))
        ax.set_xlabel("Perturbation")
        ax.set_ylabel("Toy topology")
        ax.set_title("Finite topology stress tests expose sensitive assumptions")
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", color="white", fontsize=style.font_size("dense"))
        cbar = fig.colorbar(image, ax=ax, shrink=0.86)
        cbar.set_label("|effect|")
        save_styled_figure(fig, out, style)
    return out


def figure_scholarship_source_map(project_root: Path) -> Path:
    """Render bibliography-to-method-source bindings from the scholarship matrix."""
    root = project_root.resolve()
    style = load_figure_style(root)
    matrix_path = root / "output" / "data" / "scholarship_source_matrix.json"
    if not matrix_path.is_file():
        from roadmap_tracks import write_sheaf_track_artifacts

        write_sheaf_track_artifacts(root)
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    rows = matrix.get("rows") or []

    def artifact_bucket(artifact: str) -> str:
        if "firstprinciples" in artifact:
            return "first-principles"
        if "si_" in artifact or "pymdp" in artifact:
            return "pymdp/runtime"
        if "sheaf" in artifact or "validation_dependency" in artifact:
            return "sheaf/validation"
        if "interop" in artifact or "gnn" in artifact:
            return "interop/notation"
        if "reports/" in artifact:
            return "reports"
        return "other data"

    family_counts = Counter(str(row.get("source_family", "unknown")) for row in rows)
    kind_counts = Counter(str(row.get("source_kind", "unknown")) for row in rows)
    family_order = [family for family, _count in family_counts.most_common()]
    max_display_families = 12
    display_family_order = family_order[:max_display_families]
    other_family_label = "other source families"
    if len(family_order) > max_display_families:
        display_family_order.append(other_family_label)
    bucket_preference = [
        "first-principles",
        "pymdp/runtime",
        "sheaf/validation",
        "interop/notation",
        "reports",
        "other data",
    ]
    buckets = sorted(
        {artifact_bucket(str(row.get("artifact", ""))) for row in rows},
        key=lambda value: bucket_preference.index(value) if value in bucket_preference else len(bucket_preference),
    )
    display_family_counts: Counter[str] = Counter()
    for family, count in family_counts.items():
        display_family = family if family in display_family_order else other_family_label
        display_family_counts[display_family] += count
    family_bucket_counts = np.zeros((len(display_family_order), len(buckets)))
    family_indices = {family: index for index, family in enumerate(display_family_order)}
    bucket_indices = {bucket: index for index, bucket in enumerate(buckets)}
    for row in rows:
        family = str(row.get("source_family", "unknown"))
        display_family = family if family in family_indices else other_family_label
        bucket = artifact_bucket(str(row.get("artifact", "")))
        family_bucket_counts[family_indices[display_family], bucket_indices[bucket]] += 1

    out = figure_output_path(root, "scholarship_source_map")
    with apply_style(style):
        family_count = max(1, len(display_family_order))
        fig_height = max(7.2, 2.8 + 0.52 * family_count)
        fig, axes = plt.subplots(
            1,
            3,
            figsize=(14.8, fig_height),
            gridspec_kw={"width_ratios": [1.6, 1.32, 1.16], "wspace": 0.52},
        )
        family_ax, bucket_ax, kind_ax = axes

        y_positions = np.arange(family_count)
        family_values = [display_family_counts[family] for family in display_family_order]
        family_labels = [
            "\n".join(textwrap.wrap(family.replace("_", " "), width=24, break_long_words=False))
            for family in display_family_order
        ]
        family_ax.barh(y_positions, family_values, color=style.color("secondary"), alpha=0.86)
        family_ax.set_yticks(y_positions, family_labels, fontsize=style.font_size("dense"))
        family_ax.invert_yaxis()
        family_ax.set_xlabel("Source rows")
        family_ax.set_title("Literature families\nwith load-bearing rows", fontsize=style.font_size("small"))
        style_grid(family_ax, style)
        for y, value in zip(y_positions, family_values, strict=True):
            family_ax.text(value + 0.08, y, str(value), va="center", fontsize=style.font_size("dense"), color=style.color("primary"))

        bucket_ax.imshow(family_bucket_counts, cmap="YlGnBu", aspect="auto")
        bucket_ax.set_xticks(
            np.arange(len(buckets)),
            ["\n".join(textwrap.wrap(bucket, width=13, break_long_words=False)) for bucket in buckets],
            fontsize=style.font_size("dense"),
            rotation=28,
            ha="right",
        )
        bucket_ax.tick_params(axis="y", labelleft=False, left=False)
        bucket_ax.set_title("Artifact buckets\nwhere citations bind", fontsize=style.font_size("small"))
        for i in range(family_bucket_counts.shape[0]):
            for j in range(family_bucket_counts.shape[1]):
                value = int(family_bucket_counts[i, j])
                if value:
                    bucket_ax.text(j, i, str(value), ha="center", va="center", fontsize=style.font_size("dense"), color="#111827")
        kind_order = [kind for kind, _count in kind_counts.most_common()]
        kind_values = [kind_counts[kind] for kind in kind_order]
        kind_positions = np.arange(len(kind_order))
        kind_ax.barh(kind_positions, kind_values, color=style.color("accent"), alpha=0.86)
        kind_ax.set_yticks(
            kind_positions,
            ["\n".join(textwrap.wrap(kind.replace("_", " "), width=18, break_long_words=False)) for kind in kind_order],
            fontsize=style.font_size("dense"),
        )
        kind_ax.invert_yaxis()
        kind_ax.set_xlabel("Rows")
        kind_ax.set_title("Primary and contextual\nsource types", fontsize=style.font_size("small"))
        style_grid(kind_ax, style)
        for y, value in zip(kind_positions, kind_values, strict=True):
            kind_ax.text(value + 0.08, y, str(value), va="center", fontsize=style.font_size("dense"), color=style.color("primary"))

        summary = (
            f"{matrix.get('source_count', 0)} sources, "
            f"{matrix.get('source_family_count', 0)} families, "
            f"{matrix.get('method_role_count', 0)} method roles, "
            f"connected={matrix.get('all_sources_connected')}"
        )
        fig.suptitle("Scholarship source map: print summary of bound citation families", x=0.01, ha="left", fontsize=style.font_size("title"), color=style.color("primary"))
        fig.text(
            0.01,
            0.015,
            f"{summary}. Row-level bindings: output/data/scholarship_source_matrix.json",
            fontsize=style.font_size("source"),
            color=style.color("muted"),
        )
        fig.subplots_adjust(left=0.17, right=0.985, top=0.89, bottom=0.13, wspace=0.48)
        save_figure_png(
            fig,
            out,
            dpi=style.dpi,
            facecolor="white",
            transparent=style.transparent,
        )
    return out


def _json_or_empty(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def figure_graphical_abstract(project_root: Path) -> Path:
    """Render the cover-page graphical abstract from generated evidence artifacts."""
    root = project_root.resolve()
    style = load_figure_style(root)
    from manuscript.sheaf.counts import structural_counts

    counts = structural_counts(root)
    variables = _json_or_empty(root / "output" / "data" / "manuscript_variables.json")
    fp = root / "output" / "data" / "firstprinciples"
    energy_d = _json_or_empty(fp / "energy_demo.json")
    classroom_d = _json_or_empty(fp / "classroom.json")
    vfe_d = energy_d.get("vfe_at_prior") or {}
    efe_d = energy_d.get("efe") or {}

    def _f(value: object, fmt: str = ".2f") -> str:
        try:
            return format(float(value), fmt)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return "--"

    def _i(value: object) -> str:
        try:
            return str(int(value))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return "--"

    out = figure_output_path(root, "graphical_abstract")

    def _v(name: str) -> object:
        return variables.get(name, counts.get(name))

    background = "#eaf2ff"
    with apply_style(style):
        fig = plt.figure(figsize=(10.5, 10.5), facecolor=background)
        ax = fig.add_axes((0.0, 0.0, 1.0, 1.0))
        ax.set_xlim(0, 10.0)
        ax.set_ylim(0, 10.0)
        ax.axis("off")
        ax.set_facecolor(background)

        ax.add_patch(Rectangle((0, 0), 10.0, 10.0, facecolor=background, edgecolor="none"))
        ax.add_patch(Polygon([(0, 0), (10, 0), (10, 2.3), (0, 1.55)], closed=True, color="#ccfbf1", alpha=0.76))
        ax.add_patch(Polygon([(0, 8.15), (10, 8.52), (10, 10), (0, 10)], closed=True, color="#0f172a", alpha=0.985))
        ax.add_patch(Polygon([(0, 1.55), (3.35, 2.2), (4.35, 10), (0, 10)], closed=True, color="#fff7ed", alpha=0.58))
        ax.add_patch(Polygon([(6.25, 0), (10, 0), (10, 6.15), (7.8, 5.72)], closed=True, color="#eef2ff", alpha=0.80))
        ax.add_patch(Polygon([(2.8, 3.8), (10, 3.25), (10, 8.52), (4.3, 8.12)], closed=True, color="#dbeafe", alpha=0.47))

        ax.text(
            0.48,
            9.42,
            "OPD = Active Inference",
            fontsize=31,
            fontweight="bold",
            color="white",
            va="center",
        )
        ax.text(
            0.50,
            8.96,
            "student rollouts make reverse KL a free-energy objective",
            fontsize=15.5,
            color="#dbeafe",
            va="center",
        )

        def evidence_card(
            x: float,
            y: float,
            width: float,
            height: float,
            title: str,
            eyebrow: str,
            lines: list[str],
            color: str,
            metric: tuple[str, str] | None = None,
        ) -> None:
            ax.add_patch(
                FancyBboxPatch(
                    (x + 0.05, y - 0.06),
                    width,
                    height,
                    boxstyle="round,pad=0.06,rounding_size=0.10",
                    linewidth=0,
                    facecolor="#0f172a",
                    alpha=0.16,
                )
            )
            ax.add_patch(
                FancyBboxPatch(
                    (x, y),
                    width,
                    height,
                    boxstyle="round,pad=0.06,rounding_size=0.10",
                    linewidth=1.55,
                    edgecolor=color,
                    facecolor="#fffefe",
                )
            )
            ax.add_patch(Rectangle((x, y + height - 0.16), width, 0.16, facecolor=color, edgecolor="none"))
            ax.text(x + 0.20, y + height - 0.46, eyebrow.upper(), fontsize=style.font_size("dense"), color="#64748b", fontweight="bold")
            ax.text(x + 0.20, y + height - 0.82, title, fontsize=16.2, fontweight="bold", color=color)
            text_top = y + height - 1.12
            for line_idx, line in enumerate(lines):
                ax.text(
                    x + 0.20,
                    text_top - line_idx * 0.35,
                    textwrap.fill(line, width=28),
                    fontsize=10.9,
                    color=style.color("primary"),
                    va="top",
                )
            if metric is not None:
                ax.add_patch(
                    FancyBboxPatch(
                        (x + width - 1.35, y + 0.12),
                        1.13,
                        0.62,
                        boxstyle="round,pad=0.04,rounding_size=0.09",
                        linewidth=0,
                        facecolor=color,
                        alpha=0.94,
                    )
                )
                ax.text(x + width - 0.785, y + 0.52, metric[0], fontsize=14.6, fontweight="bold", color="white", ha="center")
                ax.text(x + width - 0.785, y + 0.25, metric[1], fontsize=style.font_size("dense"), color="#f8fafc", ha="center")

        evidence_card(
            0.45,
            5.85,
            3.65,
            2.25,
            "Analytical oracle",
            "closed form",
            [
                "F_target: 0 nats",
                f"I(lambda) max: {_f(_v('ising_mi_saturation'), '.3f')} nats",
                f"sweep RMSE: {_f(_v('sweep_rmse_mi'), '.1e')}",
            ],
            style.color("secondary"),
            ("0", "target F"),
        )
        evidence_card(
            0.45,
            1.05,
            3.65,
            2.35,
            "Student rollouts",
            "pymdp + classroom",
            [
                f"cue observed: step {_i(_v('si_tmaze_cue_observed_step'))}",
                f"entropy drop: {_f(_v('si_tmaze_policy_entropy_drop_after_cue'), '.3f')} nats",
                f"teacher/student H: {_f(_v('classroom_teacher_belief_entropy'), '.3f')} / {_f(_v('classroom_student_belief_entropy'), '.3f')}",
            ],
            style.color("accent"),
            (_f(classroom_d.get("mean_reverse_kl"), ".2f"), "mean RKL"),
        )
        evidence_card(
            5.90,
            5.85,
            3.65,
            2.25,
            "Energy bridge",
            "VFE / EFE",
            [
                "reverse KL is VFE",
                f"prior VFE: {_f(vfe_d.get('vfe_complexity_accuracy'), '.2f')} nats",
                f"risk + ambiguity: {_f(efe_d.get('efe_risk_ambiguity'), '.2f')}",
            ],
            "#7c3aed",
            (_f(efe_d.get("efe_risk_ambiguity"), ".2f"), "EFE nats"),
        )
        evidence_card(
            5.90,
            1.05,
            3.65,
            2.35,
            "Lean + gates",
            "fail closed",
            [
                f"{_i(_v('sheaf_track_count'))} tracks; {_i(_v('coverage_bound'))} bound cells",
                f"{_i(_v('sheaf_laws_verified'))}/{_i(_v('sheaf_law_count'))} laws; {_i(_v('counterexample_count'))} controls",
                f"{_i(_v('token_provenance_count'))} tokens; {_i(_v('hardcoded_variable_issue_count'))} issues",
            ],
            style.color("pass"),
            (_i(_v("proof_extraction_theorem_count")), "Lean proofs"),
        )

        center = (5.0, 4.72)
        ax.add_patch(Circle(center, 1.38, facecolor="#ffffff", edgecolor="#0f172a", linewidth=2.0, alpha=0.96, zorder=3))
        ax.add_patch(Circle(center, 1.10, facecolor="#0f172a", edgecolor="#93c5fd", linewidth=1.25, alpha=0.985, zorder=4))
        ax.text(5.0, 5.05, "correspondence", fontsize=11.8, fontweight="bold", color="#bfdbfe", ha="center", zorder=5)
        ax.text(5.0, 4.73, "reverse KL", fontsize=18.5, fontweight="bold", color="white", ha="center", zorder=5)
        ax.text(5.0, 4.39, "= free energy", fontsize=14.8, fontweight="bold", color="white", ha="center", zorder=5)
        ax.text(5.0, 4.05, "active sampling loop", fontsize=style.font_size("small"), color="#dbeafe", ha="center", zorder=5)

        loop_nodes = [
            (5.0, 6.30, "teacher", "p(o,s)", "#f59e0b"),
            (6.55, 4.72, "student", "q(s)", style.color("secondary")),
            (5.0, 3.12, "rollouts", "o ~ q", style.color("accent")),
            (3.45, 4.72, "gates", "PDF", style.color("pass")),
        ]
        for idx, (x, y, title, body, color) in enumerate(loop_nodes):
            ax.add_patch(Circle((x, y), 0.47, facecolor="#ffffff", edgecolor=color, linewidth=2.0, zorder=6))
            ax.add_patch(Circle((x, y), 0.28, facecolor=color, edgecolor="white", linewidth=0.8, zorder=7))
            ax.text(x, y + 0.02, str(idx + 1), fontsize=12.8, fontweight="bold", color="white", ha="center", va="center", zorder=8)
            if title == "teacher":
                title_y = y + 0.64
                body_y = y + 0.39
            else:
                title_y = y - 0.67
                body_y = y - 0.92
            ax.text(x, title_y, title, fontsize=10.2, fontweight="bold", color=color, ha="center", zorder=8)
            ax.text(x, body_y, body, fontsize=style.font_size("dense"), color="#334155", ha="center", zorder=8)

        for start, end, rad in [
            ((5.45, 6.18), (6.38, 5.15), -0.18),
            ((6.38, 4.30), (5.45, 3.25), -0.18),
            ((4.55, 3.25), (3.62, 4.30), -0.18),
            ((3.62, 5.15), (4.55, 6.18), -0.18),
        ]:
            ax.add_patch(
                FancyArrowPatch(
                    start,
                    end,
                    arrowstyle="-|>",
                    mutation_scale=15,
                    linewidth=1.7,
                    color="#475569",
                    alpha=0.72,
                    connectionstyle=f"arc3,rad={rad}",
                    zorder=5,
                )
            )

        ax.text(
            9.52,
            0.36,
            "generated from repository artifacts; toy scope only",
            fontsize=style.font_size("source"),
            color="#334155",
            ha="right",
        )
        save_figure_png(
            fig,
            out,
            dpi=style.dpi,
            facecolor=background,
            transparent=False,
            bbox_inches=None,
        )
    return out


FIGURE_GENERATORS: dict[str, Callable[[Path], Path | None]] = {
    "ising_mi_curve": figure_ising_mi_curve,
    "free_energy_curve": figure_free_energy_curve,
    "si_belief_entropy_curve": figure_si_belief_entropy_curve,
    "si_obs_action_trace": figure_si_obs_action_trace,
    "si_tmaze_actions": figure_si_tmaze_actions,
    "si_tmaze_model_matrices": figure_si_tmaze_model_matrices,
    "distillation_divergence_geometry": figure_distillation_divergence_geometry,
    "exposure_bias_recovery": figure_exposure_bias_recovery,
    "classroom_distillation_signal": figure_classroom_distillation_signal,
    "energy_decomposition": figure_energy_decomposition,
    "parallel_convergence": figure_parallel_convergence,
    "diversity_tradeoff": figure_diversity_tradeoff,
    "sheaf_layers_overview": figure_sheaf_layers_overview,
    "sheaf_coverage_heatmap": figure_sheaf_coverage_heatmap,
    "invariant_dashboard": figure_invariant_dashboard,
    "tmaze_schematic": figure_tmaze_schematic,
    "multi_track_architecture": figure_multi_track_architecture,
    "lean_boundary_status": figure_lean_boundary_status,
    "gnn_ontology_concordance": figure_gnn_ontology_concordance,
    "semantic_gluing_graph": figure_semantic_gluing_graph,
    "theorem_traceability_graph": figure_theorem_traceability_graph,
    "causal_ablation_heatmap": figure_causal_ablation_heatmap,
    "scholarship_source_map": figure_scholarship_source_map,
    "graphical_abstract": figure_graphical_abstract,
}


def run_figure(figure_id: str, project_root: Path) -> Path:
    """Dispatch a registry figure id to its generator."""
    load_figure_registry(project_root)  # fail fast when registry missing
    try:
        generator = FIGURE_GENERATORS[figure_id]
    except KeyError as exc:
        raise KeyError(f"unknown figure id: {figure_id}") from exc
    result = generator(project_root)
    if result is None:
        raise RuntimeError(f"figure generator returned no path for {figure_id}")
    return result


def generate_all_figures(project_root: Path) -> list[Path]:
    from orchestration.coverage_pipeline import ensure_coverage_artifacts
    from .figure_registry import write_figure_registry_json

    json_path, _, page_path = ensure_coverage_artifacts(project_root, write_page=True)
    paths: list[Path] = [json_path]
    paths.extend(run_figure(figure_id, project_root) for figure_id in FIGURE_GENERATORS)
    paths.append(write_figure_registry_json(project_root))
    if page_path is not None:
        paths.append(page_path)
    return [path for path in paths if path is not None]
