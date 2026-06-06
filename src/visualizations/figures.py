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
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch
from matplotlib.ticker import MaxNLocator

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


def figure_ising_mi_curve(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    sweep = root / "output" / "data" / "parameter_sweep.csv"
    lambdas, closed, empirical = _read_sweep(sweep)
    out = figure_output_path(root, "ising_mi_curve")
    with apply_style(style):
        fig, axes = plt.subplots(1, 2, figsize=(9, 3.8), gridspec_kw={"width_ratios": [2.2, 1]})
        ax_main, ax_resid = axes
        ax_main.plot(lambdas, closed, label="closed form", color=style.color("primary"), linewidth=2)
        ax_main.plot(
            lambdas,
            empirical,
            "--",
            label="exact recompute",
            color=style.color("secondary"),
            linewidth=2,
        )
        ax_main.set_xlabel(r"Coupling strength $\lambda$")
        ax_main.set_ylabel("Mutual information (nats)")
        ax_main.set_title("Bernoulli–Ising MI sweep")
        style_grid(ax_main, style)
        ax_main.legend(frameon=False, fontsize=8)
        residuals = [e - c for e, c in zip(empirical, closed, strict=True)]
        ax_resid.axhline(0.0, color=style.color("reference"), linewidth=1)
        ax_resid.plot(lambdas, residuals, color=style.color("accent"), linewidth=1.5)
        ax_resid.set_xlabel(r"$\lambda$")
        ax_resid.set_ylabel("residual")
        ax_resid.set_title("recompute − closed", fontsize=9)
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
        fig, ax = plt.subplots(figsize=(8.2, 4.0))
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
                fontsize=8.2,
                color=style.color("accent"),
                arrowprops={"arrowstyle": "->", "color": style.color("accent"), "linewidth": 0.8},
            )
        ax.set_xlabel("Timestep")
        ax.set_ylabel("Belief entropy (nats)")
        ax.set_title("Full TMaze SI belief entropy from persisted rollout trace")
        style_grid(ax, style)
        fig.text(0.01, 0.01, "Source: output/data/si_tmaze_trace.json", fontsize=7.8, color=style.color("muted"))
        save_styled_figure(fig, out, style)
    return out


def figure_si_obs_action_trace(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    summary_path = root / "output" / "data" / "si_tmaze_summary.json"
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    observations_by_modality = data.get("observations_by_modality") or {"location": data.get("observations") or []}
    actions = data.get("actions") or []
    out = figure_output_path(root, "si_obs_action_trace")
    with apply_style(style):
        fig, axes = plt.subplots(2, 1, figsize=(9.2, 5.4), sharex=True, gridspec_kw={"height_ratios": [1.6, 1]})
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
        obs_ax.set_title("Full TMaze multimodal observations and selected actions")
        _style_discrete_y(obs_ax, style)
        obs_ax.legend(frameon=False, ncol=3, loc="upper left", title="Observation modality")
        act_ax.step(xs, actions, where="post", linewidth=2.4, marker="s", markersize=4.6, color=style.color("primary"))
        act_ax.set_xlabel("Timestep")
        act_ax.set_ylabel("Action")
        action_names = data.get("action_names") or []
        if action_names:
            act_ax.set_yticks(range(len(action_names)))
            act_ax.set_yticklabels(
                [name.replace("move_to_", "").replace("_", " ") for name in action_names], fontsize=8
            )
        for x, action in enumerate(actions):
            action_idx = int(action)
            name = action_names[action_idx] if 0 <= action_idx < len(action_names) else str(action)
            act_ax.text(
                x,
                float(action) + 0.22,
                name.replace("move_to_", "").replace("_", " "),
                ha="center",
                va="bottom",
                fontsize=7.5,
                color=style.color("primary"),
            )
        _style_discrete_y(act_ax, style)
        fig.text(0.01, 0.01, "Source: output/data/si_tmaze_summary.json", fontsize=7.8, color=style.color("muted"))
        save_styled_figure(fig, out, style)
    return out


def figure_si_tmaze_actions(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    summary_path = root / "output" / "data" / "si_tmaze_summary.json"
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    actions = data.get("actions", [])
    action_probabilities = data.get("action_probabilities") or []
    planning_horizon = data.get("planning_horizon", "?")
    tree_warnings = (data.get("expected_known_warnings") or {}).get("tree_max_nodes", 0)
    out = figure_output_path(root, "si_tmaze_actions")
    with apply_style(style):
        fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.6), gridspec_kw={"width_ratios": [1.05, 1.75]})
        ax, prob_ax = axes
        steps = list(range(len(actions)))
        ax.step(steps, actions, where="post", linewidth=2, color=style.color("primary"))
        ax.fill_between(steps, actions, step="post", alpha=0.08, color=style.color("secondary"))
        ax.set_xlabel("Timestep")
        ax.set_ylabel("Action index")
        ax.set_title("Selected first action")
        action_names_for_ticks = data.get("action_names") or []
        if action_names_for_ticks:
            ax.set_yticks(range(len(action_names_for_ticks)))
            ax.set_yticklabels(
                [name.replace("move_to_", "").replace("_", " ") for name in action_names_for_ticks],
                fontsize=8,
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
                fontsize=8,
                color=style.color("primary"),
                arrowprops={"arrowstyle": "->", "color": style.color("primary"), "linewidth": 0.8},
            )
        prob_ax.set_ylim(-0.02, 1.02)
        prob_ax.set_xlabel("Timestep")
        prob_ax.set_ylabel("Marginal first-action probability")
        prob_ax.set_title(
            f"qπ marginals from SI search; horizon={planning_horizon}, known tree warnings={tree_warnings}"
        )
        style_grid(prob_ax, style)
        prob_ax.legend(frameon=False, ncol=2, fontsize=7)
        fig.text(0.01, 0.01, "Source: output/data/si_tmaze_summary.json", fontsize=7.8, color=style.color("muted"))
        save_styled_figure(fig, out, style)
    return out


def figure_si_tmaze_model_matrices(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    matrices_path = root / "output" / "data" / "si_tmaze_model_matrices.json"
    data = json.loads(matrices_path.read_text(encoding="utf-8"))
    out = figure_output_path(root, "si_tmaze_model_matrices")
    with apply_style(style):
        fig, axes = plt.subplots(1, 2, figsize=(11.2, 5.6), gridspec_kw={"width_ratios": [1.25, 1]})
        shape_ax, norm_ax = axes
        shape_ax.axis("off")
        rows = [
            ("A[0]", "location obs", data["A_shapes"][0], data["dependencies"]["A"][0]),
            ("A[1]", "outcome obs", data["A_shapes"][1], data["dependencies"]["A"][1]),
            ("A[2]", "cue obs", data["A_shapes"][2], data["dependencies"]["A"][2]),
            ("B[0]", "location transition", data["B_shapes"][0], data["dependencies"]["B"][0]),
            ("B[1]", "reward-location fixed", data["B_shapes"][1], data["dependencies"]["B"][1]),
        ]
        y = 0.9
        for idx, (name, label, shape, deps) in enumerate(rows):
            color = style.color("secondary") if name.startswith("A") else style.color("accent")
            box = FancyBboxPatch(
                (0.05, y - 0.075),
                0.88,
                0.105,
                boxstyle="round,pad=0.015",
                facecolor="#f8fafc",
                edgecolor=color,
                linewidth=1.4,
            )
            shape_ax.add_patch(box)
            shape_ax.text(0.08, y, name, fontsize=10, weight="bold", color=color, va="center")
            shape_ax.text(0.22, y, label, fontsize=9, va="center", color=style.color("primary"))
            shape_ax.text(0.58, y, f"shape {shape}", fontsize=8.5, va="center", color=style.color("muted"))
            shape_ax.text(0.78, y, f"deps {deps}", fontsize=8.5, va="center", color=style.color("muted"))
            y -= 0.145
        env = data.get("environment") or {}
        shape_ax.text(
            0.05,
            0.11,
            f"TMaze reward_condition={env.get('reward_condition')}, cue_validity={env.get('cue_validity')}, dependent_outcomes={env.get('dependent_outcomes')}",
            fontsize=8.5,
            color=style.color("primary"),
        )
        preferences = data.get("preferences") or {}
        c_shapes = data.get("C_shapes") or []
        d_shapes = data.get("D_shapes") or []
        shape_ax.text(
            0.05,
            0.055,
            f"C preferences={list(preferences)} with shapes {c_shapes}; D prior shapes={d_shapes}",
            fontsize=8.2,
            color=style.color("muted"),
        )
        shape_ax.set_title("Full TMaze factorization and dependencies")

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
        norm_ax.set_title("A/B/D normalization checks")
        style_grid(norm_ax, style)
        norm_ax.legend(frameon=False, loc="upper right")
        fig.text(
            0.01,
            0.01,
            "Source: output/data/si_tmaze_model_matrices.json; all columns normalize to probability mass 1.",
            fontsize=7.8,
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
        fig, axes = plt.subplots(1, 3, figsize=(12.2, 4.8), gridspec_kw={"width_ratios": [1.0, 1.24, 0.84]})
        mass_ax, div_ax, entropy_ax = axes
        x = np.arange(len(teacher))
        width = 0.36
        mass_ax.bar(x - width / 2, teacher, width, label="teacher p", color=style.color("secondary"))
        mass_ax.bar(x + width / 2, student, width, label="student q", color=style.color("accent"))
        mass_ax.set_xticks(x, [f"mode {idx + 1}" for idx in x])
        mass_ax.set_ylim(0.0, 1.0)
        mass_ax.set_ylabel("Probability mass")
        mass_ax.set_title("Teacher and student categorical policies")
        style_grid(mass_ax, style)
        mass_ax.legend(frameon=False, fontsize=8)

        names = [name for name, _value in measures]
        values = [value for _name, value in measures]
        colors = [style.color("accent"), style.color("secondary"), "#7c3aed", "#b45309", style.color("fail")]
        bars = div_ax.bar(np.arange(len(values)), values, color=colors, alpha=0.88)
        div_ax.set_xticks(np.arange(len(values)), [name.replace(" ", "\n") for name in names], fontsize=8)
        div_ax.set_ylabel("Divergence (nats)")
        div_ax.set_title("Objective geometry used by the correspondence")
        style_grid(div_ax, style)
        for bar, value in zip(bars, values, strict=True):
            div_ax.text(bar.get_x() + bar.get_width() / 2, value + 0.006, f"{value:.3f}", ha="center", fontsize=7.5)
        entropy_names = [name for name, _value in entropy_rows]
        entropy_values = [value for _name, value in entropy_rows]
        entropy_colors = [style.color("secondary"), style.color("accent")]
        entropy_ax.barh(np.arange(len(entropy_values)), entropy_values, color=entropy_colors, alpha=0.88)
        entropy_ax.set_yticks(np.arange(len(entropy_values)), entropy_names, fontsize=8)
        entropy_ax.set_xlabel("Entropy (nats)")
        entropy_ax.set_title("Mode concentration")
        entropy_ax.set_xlim(0, max(1.0, max(entropy_values, default=0.0) * 1.28))
        style_grid(entropy_ax, style)
        for y, value in enumerate(entropy_values):
            entropy_ax.text(value + 0.025, y, f"{value:.3f}", va="center", fontsize=7.5)
        entropy_ax.text(
            0.02,
            0.05,
            f"H gap={entropy_gap:+.3f}\nmode-seeking={mode_seeking}",
            transform=entropy_ax.transAxes,
            fontsize=8,
            color=style.color("primary"),
            bbox=dict(boxstyle="round,pad=0.28", facecolor="#f8fafc", edgecolor=style.color("reference")),
        )
        fig.text(
            0.01,
            0.01,
            "Source: output/data/firstprinciples/divergence_demo.json",
            fontsize=7.8,
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
        fig, ax = plt.subplots(figsize=(8.8, 4.8))
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
                fontsize=8,
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
                fontsize=7.5,
                color=style.color("fail"),
            )
            ax.text(
                terminal_x,
                on_policy[terminal_x] + 0.035,
                f"{on_policy[terminal_x]:.3f}",
                ha="center",
                va="bottom",
                fontsize=7.5,
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
                0.02,
                fixed_value + 0.02,
                f"fixed point={fixed_value:.3f}",
                transform=ax.get_yaxis_transform(),
                fontsize=7.8,
                color=style.color("reference"),
            )
        ax.set_xlabel("Generated step")
        ax.set_ylabel("Expected correctness")
        ax.set_ylim(0.0, 1.02)
        ax.set_title("Toy exposure-bias recovery under student-induced rollouts")
        style_grid(ax, style)
        ax.legend(frameon=False, fontsize=8)
        fig.text(
            0.01,
            0.01,
            "Source: output/data/firstprinciples/exposure_bias_demo.json",
            fontsize=7.8,
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
        fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.8), gridspec_kw={"width_ratios": [1.05, 1.35]})
        div_ax, heat_ax = axes
        xs = np.arange(len(rows))
        div_ax.plot(xs, reverse, marker="o", linewidth=2.0, color=style.color("accent"), label="reverse KL")
        div_ax.plot(xs, forward, marker="s", linewidth=2.0, color=style.color("secondary"), label="forward KL")
        div_ax.plot(xs, jsd, marker="^", linewidth=1.8, color="#7c3aed", label="Jensen-Shannon")
        div_ax.set_xlabel("Classroom step")
        div_ax.set_ylabel("Divergence (nats)")
        div_ax.set_title("Per-step teacher/student distillation signal")
        style_grid(div_ax, style)
        div_ax.legend(frameon=False, fontsize=8)
        div_ax.text(
            0.02,
            0.95,
            f"argmax agreement {agreement_count}/{len(rows)}",
            transform=div_ax.transAxes,
            va="top",
            fontsize=8,
            color=style.color("primary"),
            bbox=dict(boxstyle="round,pad=0.28", facecolor="#f8fafc", edgecolor=style.color("reference")),
        )

        if deltas.size:
            image = heat_ax.imshow(deltas, cmap="coolwarm", aspect="auto", vmin=-1.0, vmax=1.0)
            action_labels = [str(action).replace("move_to_", "").replace("_", " ") for action in actions]
            heat_ax.set_xticks(
                range(len(actions)),
                [str(action).replace("move_to_", "").replace("_", "\n") for action in actions],
                fontsize=8,
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
                fontsize=7.4,
            )
            heat_ax.set_xlabel("Action")
            heat_ax.set_ylabel("Classroom step")
            for i in range(deltas.shape[0]):
                for j in range(deltas.shape[1]):
                    heat_ax.text(j, i, f"{deltas[i, j]:+.2f}", ha="center", va="center", fontsize=7)
            cbar = fig.colorbar(image, ax=heat_ax, shrink=0.84)
            cbar.set_label("teacher p - student q")
        heat_ax.set_title("Privileged teacher signal minus student posterior")
        fig.text(
            0.01,
            0.01,
            "Source: output/data/firstprinciples/classroom.json",
            fontsize=7.8,
            color=style.color("muted"),
        )
        save_styled_figure(fig, out, style)
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
        fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6))
        vfe_ax, efe_ax = axes
        vfe_labels = ["complexity\n$D_{KL}(q\\|p(s))$", "accuracy\n$E_q[\\ln p(o|s)]$", "VFE\n$F$"]
        vfe_values = [complexity, accuracy, free_energy]
        vfe_colors = [style.color("secondary"), style.color("accent"), style.color("primary")]
        vfe_ax.bar(vfe_labels, vfe_values, color=vfe_colors)
        vfe_ax.axhline(0.0, color=style.color("reference"), linewidth=0.8)
        vfe_ax.set_ylabel("nats")
        vfe_ax.set_title("Variational free energy = complexity - accuracy")
        for i, v in enumerate(vfe_values):
            vfe_ax.text(i, v, f"{v:.3f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=8)
        style_grid(vfe_ax, style)

        efe_labels = ["risk\n$D_{KL}(q(o)\\|p(o))$", "ambiguity\n$E[H[p(o|s)]]$", "epistemic\n$I(o;s)$", "pragmatic\n$E[\\ln p(o)]$"]
        efe_values = [risk, ambiguity, epistemic, pragmatic]
        efe_colors = [style.color("fail"), style.color("muted"), style.color("accent"), style.color("secondary")]
        efe_ax.bar(efe_labels, efe_values, color=efe_colors)
        efe_ax.axhline(0.0, color=style.color("reference"), linewidth=0.8)
        efe_ax.set_ylabel("nats")
        efe_ax.set_title("Expected free energy: risk + ambiguity = -(epistemic + pragmatic)")
        for i, v in enumerate(efe_values):
            efe_ax.text(i, v, f"{v:.3f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=8)
        style_grid(efe_ax, style)
        fig.text(
            0.01,
            0.01,
            "Source: output/data/firstprinciples/energy_demo.json",
            fontsize=7.8,
            color=style.color("muted"),
        )
        save_styled_figure(fig, out, style)
    return out


def figure_si_summary(project_root: Path) -> Path:
    """Deprecated alias for ``figure_si_tmaze_actions``."""
    return figure_si_tmaze_actions(project_root)


def figure_free_energy_curve(project_root: Path) -> Path:
    root = project_root.resolve()
    style = load_figure_style(root)
    from analytical.decomposition import free_energy_against_entangled_prior
    from analytical.bernoulli_toy import ising_coupling, ising_joint_posterior, symmetric_mean_field_prior

    hp_lambdas = lambda_grid(load_hyperparameters())
    mf = symmetric_mean_field_prior()
    g0 = [np.zeros(2), np.zeros(2)]
    j = ising_coupling()
    kc = np.zeros((2, 2))
    values = []
    for lam in hp_lambdas:
        q = ising_joint_posterior(float(lam))
        values.append(free_energy_against_entangled_prior(q, mf, g0, j, kc, gamma=1.0, lam=float(lam)))
    out = figure_output_path(root, "free_energy_curve")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(6.5, 4))
        ax.plot(hp_lambdas, values, linewidth=2, color=style.color("primary"))
        min_idx = int(np.argmin(values))
        ax.scatter(
            [hp_lambdas[min_idx]],
            [values[min_idx]],
            color=style.color("accent"),
            s=40,
            zorder=3,
            label=f"min at λ={hp_lambdas[min_idx]:.2f}",
        )
        ax.set_xlabel(r"Coupling strength $\lambda$")
        ax.set_ylabel("Free energy (nats)")
        ax.set_title("Free energy against entangled prior")
        style_grid(ax, style)
        ax.legend(frameon=False, fontsize=8)
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
        fig, ax = plt.subplots(figsize=(9.6, 5.6))
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
                fontsize=8,
                va="center",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#f8fafc", edgecolor=box_color),
            )
            ax.text(
                artifact_x,
                y,
                rel.replace("output/", ""),
                fontsize=8,
                va="center",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#ffffff", edgecolor=style.color("secondary")),
            )
            ax.text(
                consumer_x,
                y,
                consumers,
                fontsize=8,
                va="center",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#f8fafc", edgecolor=style.color("accent")),
            )
            ax.annotate("", xy=(artifact_x - 0.02, y), xytext=(producer_x + 0.24, y), arrowprops={"arrowstyle": "->"})
            ax.annotate("", xy=(consumer_x - 0.02, y), xytext=(artifact_x + 0.29, y), arrowprops={"arrowstyle": "->"})
        ax.set_title("Semantic sheaf gluing dependency graph", loc="left", pad=16)
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
    rows = (theorem.get("rows") or [])[:6]
    edges = dependency.get("edges") or []
    edge_count_by_theorem = {
        row.get("theorem", ""): sum(1 for edge in edges if edge.get("source") == row.get("theorem")) for row in rows
    }
    out = figure_output_path(root, "theorem_traceability_graph")
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(9.2, 4.8))
        ax.axis("off")
        columns = [0.05, 0.42, 0.78]
        headers = ["Lean theorem", "Proof dependency rows", "Finite witnesses"]
        for x, header in zip(columns, headers, strict=True):
            ax.text(x, 0.94, header, weight="bold", color=style.color("primary"), fontsize=10)
        y_positions = np.linspace(0.82, 0.14, max(1, len(rows)))
        for y, row in zip(y_positions, rows, strict=False):
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
                fontsize=7.5,
                va="center",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#f8fafc", edgecolor=edge_color),
            )
            ax.text(
                columns[1],
                y,
                proof_label,
                fontsize=8,
                va="center",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#ffffff", edgecolor=style.color("secondary")),
            )
            ax.text(
                columns[2],
                y,
                witness_label,
                fontsize=8,
                va="center",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#f8fafc", edgecolor=style.color("accent")),
            )
            ax.annotate("", xy=(columns[1] - 0.03, y), xytext=(columns[0] + 0.24, y), arrowprops={"arrowstyle": "->"})
            ax.annotate("", xy=(columns[2] - 0.03, y), xytext=(columns[1] + 0.24, y), arrowprops={"arrowstyle": "->"})
        ax.set_title("Theorem traceability graph", loc="left", pad=16)
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
        fig, ax = plt.subplots(figsize=(8.2, 4.8))
        image = ax.imshow(matrix, cmap="viridis", aspect="auto")
        ax.set_xticks(range(len(perturbations)), [label.replace("_", "\n") for label in perturbations], fontsize=8)
        ax.set_yticks(range(len(topologies)), topologies, fontsize=9)
        ax.set_xlabel("Perturbation")
        ax.set_ylabel("Toy topology")
        ax.set_title("Causal-ablation sensitivity")
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", color="white", fontsize=8)
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
    family_bucket_counts = np.zeros((len(family_order), len(buckets)))
    family_indices = {family: index for index, family in enumerate(family_order)}
    bucket_indices = {bucket: index for index, bucket in enumerate(buckets)}
    for row in rows:
        family = str(row.get("source_family", "unknown"))
        bucket = artifact_bucket(str(row.get("artifact", "")))
        family_bucket_counts[family_indices[family], bucket_indices[bucket]] += 1

    out = figure_output_path(root, "scholarship_source_map")
    with apply_style(style):
        family_count = max(1, len(family_order))
        fig_height = max(7.2, 2.2 + 0.34 * family_count)
        fig, axes = plt.subplots(
            1,
            3,
            figsize=(12.6, fig_height),
            gridspec_kw={"width_ratios": [1.45, 1.25, 1.08], "wspace": 0.48},
        )
        family_ax, bucket_ax, kind_ax = axes

        y_positions = np.arange(family_count)
        family_values = [family_counts[family] for family in family_order]
        family_labels = [
            "\n".join(textwrap.wrap(family.replace("_", " "), width=24, break_long_words=False))
            for family in family_order
        ]
        family_ax.barh(y_positions, family_values, color=style.color("secondary"), alpha=0.86)
        family_ax.set_yticks(y_positions, family_labels, fontsize=7.3)
        family_ax.invert_yaxis()
        family_ax.set_xlabel("Source rows")
        family_ax.set_title("Source families")
        style_grid(family_ax, style)
        for y, value in zip(y_positions, family_values, strict=True):
            family_ax.text(value + 0.08, y, str(value), va="center", fontsize=7.5, color=style.color("primary"))

        bucket_ax.imshow(family_bucket_counts, cmap="YlGnBu", aspect="auto")
        bucket_ax.set_xticks(
            np.arange(len(buckets)),
            ["\n".join(textwrap.wrap(bucket, width=13, break_long_words=False)) for bucket in buckets],
            fontsize=7.2,
            rotation=28,
            ha="right",
        )
        bucket_ax.tick_params(axis="y", labelleft=False, left=False)
        bucket_ax.set_title("Artifact buckets")
        for i in range(family_bucket_counts.shape[0]):
            for j in range(family_bucket_counts.shape[1]):
                value = int(family_bucket_counts[i, j])
                if value:
                    bucket_ax.text(j, i, str(value), ha="center", va="center", fontsize=7.3, color="#111827")
        kind_order = [kind for kind, _count in kind_counts.most_common()]
        kind_values = [kind_counts[kind] for kind in kind_order]
        kind_positions = np.arange(len(kind_order))
        kind_ax.barh(kind_positions, kind_values, color=style.color("accent"), alpha=0.86)
        kind_ax.set_yticks(
            kind_positions,
            ["\n".join(textwrap.wrap(kind.replace("_", " "), width=18, break_long_words=False)) for kind in kind_order],
            fontsize=7.2,
        )
        kind_ax.invert_yaxis()
        kind_ax.set_xlabel("Rows")
        kind_ax.set_title("Source kinds")
        style_grid(kind_ax, style)
        for y, value in zip(kind_positions, kind_values, strict=True):
            kind_ax.text(value + 0.08, y, str(value), va="center", fontsize=7.3, color=style.color("primary"))

        summary = (
            f"{matrix.get('source_count', 0)} sources, "
            f"{matrix.get('source_family_count', 0)} families, "
            f"{matrix.get('method_role_count', 0)} method roles, "
            f"connected={matrix.get('all_sources_connected')}"
        )
        fig.suptitle("Scholarship source map", x=0.01, ha="left", fontsize=13, color=style.color("primary"))
        fig.text(
            0.01,
            0.015,
            f"{summary}. Row-level bindings: output/data/scholarship_source_matrix.json",
            fontsize=8.2,
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
    scholarship = _json_or_empty(root / "output" / "data" / "scholarship_source_matrix.json")
    dependency = _json_or_empty(root / "output" / "data" / "validation_dependency_graph.json")
    variables = _json_or_empty(root / "output" / "data" / "manuscript_variables.json")
    validation = _json_or_empty(root / "output" / "reports" / "validation_report.json")
    fp = root / "output" / "data" / "firstprinciples"
    energy_d = _json_or_empty(fp / "energy_demo.json")
    classroom_d = _json_or_empty(fp / "classroom.json")
    empirical_d = _json_or_empty(fp / "empirical_benchmark.json")
    vfe_d = energy_d.get("vfe_at_prior") or {}
    efe_d = energy_d.get("efe") or {}

    def _f(value: object, fmt: str = ".2f") -> str:
        try:
            return format(float(value), fmt)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return "--"

    _ = (scholarship, dependency, validation)  # retained inputs; numbers now sourced from firstprinciples artifacts
    out = figure_output_path(root, "graphical_abstract")

    background = "#eef2ff"
    with apply_style(style):
        fig = plt.figure(figsize=(14.0, 7.0), facecolor=background)
        ax = fig.add_axes((0.0, 0.0, 1.0, 1.0))
        ax.set_xlim(0, 14.0)
        ax.set_ylim(0, 7.0)
        ax.axis("off")
        ax.set_facecolor(background)

        ax.fill([0, 14, 14, 0], [0, 0, 1.55, 0.85], color="#dbeafe", alpha=0.82)
        ax.fill([0, 14, 14, 0], [5.65, 6.2, 7, 7], color="#111827", alpha=0.96)
        ax.fill([5.5, 14, 14, 8.9], [0, 0, 3.0, 1.9], color="#ccfbf1", alpha=0.58)
        ax.fill([0, 4.8, 7.3, 0], [1.1, 2.0, 7, 7], color="#fef3c7", alpha=0.36)

        for x, y, radius, color in [
            (1.25, 5.15, 0.18, "#2563eb"),
            (2.5, 2.02, 0.13, "#0f766e"),
            (5.35, 5.06, 0.14, "#7c3aed"),
            (9.18, 5.08, 0.16, "#b45309"),
            (12.18, 2.18, 0.14, "#0f766e"),
        ]:
            ax.add_patch(Circle((x, y), radius, facecolor=color, edgecolor="white", linewidth=1.0, alpha=0.9))

        ax.text(
            0.55,
            6.48,
            "On-Policy Distillation is Active Inference",
            fontsize=22,
            fontweight="bold",
            color="white",
            va="center",
        )
        ax.text(
            0.58,
            6.08,
            "The variational posterior generates its own observations; the generative model is conditioned on privileged beliefs.",
            fontsize=10.5,
            color="#dbeafe",
            va="center",
        )
        ax.text(
            13.45,
            6.42,
            f"{counts['sheaf_track_count']} tracks",
            fontsize=11,
            fontweight="bold",
            color="#bfdbfe",
            ha="right",
            va="center",
        )

        hub_x, hub_y = 7.0, 3.65
        ax.add_patch(Circle((hub_x, hub_y), 1.05, facecolor="#111827", edgecolor="#93c5fd", linewidth=2.4))
        ax.add_patch(Circle((hub_x, hub_y), 0.74, facecolor="#1e3a8a", edgecolor="#c7d2fe", linewidth=1.4))
        ax.text(hub_x, hub_y + 0.2, "reverse KL", fontsize=13, fontweight="bold", color="white", ha="center")
        ax.text(hub_x, hub_y - 0.1, "= free energy", fontsize=11, color="#dbeafe", ha="center")
        ax.text(
            hub_x,
            hub_y - 0.5,
            r"$D_{KL}(\pi_S\|\pi_T)=F$",
            fontsize=8.6,
            color="#bfdbfe",
            ha="center",
        )

        def card(
            x: float,
            y: float,
            width: float,
            height: float,
            title: str,
            lines: list[str],
            color: str,
            anchor: tuple[float, float],
        ) -> None:
            ax.add_patch(
                FancyBboxPatch(
                    (x + 0.06, y - 0.07),
                    width,
                    height,
                    boxstyle="round,pad=0.08",
                    linewidth=0,
                    facecolor="#0f172a",
                    alpha=0.12,
                )
            )
            ax.add_patch(
                FancyBboxPatch(
                    (x, y),
                    width,
                    height,
                    boxstyle="round,pad=0.08",
                    linewidth=1.8,
                    edgecolor=color,
                    facecolor="#ffffff",
                )
            )
            ax.add_patch(
                FancyBboxPatch(
                    (x + 0.16, y + height - 0.48),
                    0.62,
                    0.2,
                    boxstyle="round,pad=0.04",
                    linewidth=0,
                    facecolor=color,
                    alpha=0.92,
                )
            )
            ax.text(x + 0.18, y + height - 0.82, title, fontsize=10.8, fontweight="bold", color=color)
            for line_idx, line in enumerate(lines):
                ax.text(
                    x + 0.2,
                    y + height - 1.2 - line_idx * 0.36,
                    textwrap.fill(line, width=36),
                    fontsize=7.6,
                    color=style.color("primary"),
                    va="top",
                )
            ax.add_patch(
                FancyArrowPatch(
                    anchor,
                    (hub_x, hub_y),
                    arrowstyle="-|>",
                    mutation_scale=16,
                    linewidth=1.9,
                    color=color,
                    alpha=0.78,
                    connectionstyle="arc3,rad=0.12",
                )
            )

        card(
            0.72,
            3.08,
            3.25,
            2.18,
            "Correspondence",
            [
                "teacher pi_T = generative model p(o,s)",
                "student pi_S = posterior q(s)",
                "privileged context = Markov blanket",
            ],
            style.color("secondary"),
            (3.97, 4.15),
        )
        card(
            0.94,
            0.74,
            3.25,
            2.12,
            "Two-agent classroom",
            [
                f"teacher entropy {_f(classroom_d.get('teacher_mean_belief_entropy'), '.3f')} nats",
                f"student entropy {_f(classroom_d.get('student_mean_belief_entropy'), '.3f')} nats",
                f"distillation signal {_f(classroom_d.get('mean_reverse_kl'), '.2f')} nats",
            ],
            style.color("accent"),
            (4.19, 1.92),
        )
        card(
            9.8,
            3.08,
            3.28,
            2.18,
            "Energy decomposition",
            [
                f"VFE = complexity {_f(vfe_d.get('complexity'), '.2f')} - accuracy {_f(vfe_d.get('accuracy'), '.2f')}",
                f"EFE risk {_f(efe_d.get('risk'), '.2f')} + ambiguity {_f(efe_d.get('ambiguity'), '.2f')}",
                f"epistemic {_f(efe_d.get('epistemic_value'), '.2f')} + pragmatic {_f(efe_d.get('pragmatic_value'), '.2f')}",
            ],
            "#7c3aed",
            (9.8, 4.15),
        )
        card(
            9.63,
            0.74,
            3.36,
            2.12,
            "Empirical (reported)",
            [
                f"AIME'24 OPD {_f(empirical_d.get('opd_aime24'), '.1f')} vs RL {_f(empirical_d.get('rl_aime24'), '.1f')}",
                f"{_f(empirical_d.get('compute_reduction_factor'), '.1f')}x less compute",
                "dense per-token vs sparse scalar reward",
            ],
            style.color("pass"),
            (9.63, 1.92),
        )

        gate_labels = ["analysis", "figures", "gluing", "claims", "PDF/HTML", "copy-out"]
        ax.text(4.74, 1.07, "deterministic publication spine", fontsize=9.4, fontweight="bold", color="#1f2937")
        for idx, label in enumerate(gate_labels):
            x = 4.74 + idx * 0.78
            y = 0.56
            face = "#ecfdf5" if idx < len(gate_labels) - 1 else "#dbeafe"
            ax.add_patch(
                FancyBboxPatch(
                    (x, y),
                    0.66,
                    0.32,
                    boxstyle="round,pad=0.035",
                    linewidth=0.9,
                    edgecolor=style.color("pass"),
                    facecolor=face,
                )
            )
            ax.text(x + 0.33, y + 0.16, label, fontsize=6.5, ha="center", va="center", color="#111827")
            if idx < len(gate_labels) - 1:
                ax.annotate(
                    "",
                    xy=(x + 0.78, y + 0.16),
                    xytext=(x + 0.67, y + 0.16),
                    arrowprops={"arrowstyle": "->", "color": "#64748b", "lw": 0.9},
                )

        ax.text(
            13.36,
            0.32,
            "generated from repository artifacts",
            fontsize=7.5,
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
