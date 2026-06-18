"""First-principles figures (divergence geometry, exposure bias, classroom, convergence, diversity)."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FixedFormatter, FixedLocator

from .figure_helpers import save_styled_figure, style_grid
from .figure_io import save_figure_png
from .figure_registry import figure_output_path
from .figure_style import apply_style, load_figure_style


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
        mass_ax.legend(frameon=True, fontsize=style.font_size("legend"))

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


def figure_active_selection_landscape(project_root: Path) -> Path:
    """Render the EFE active-selection landscape: validity-sweep identity + per-policy EFE bars.

    Left: as cue validity rises, the epistemic value (information gain) rises and
    the residual distillation gap falls; their sum is the constant prior entropy
    H(r) -- the ``gap_closed = epistemic`` identity, shown across the sweep.
    Right: the expected-free-energy decomposition per canonical data-collection
    policy, making explicit that minimising EFE selects the cue while a
    pragmatic-only rule would commit to an arm.
    """
    root = project_root.resolve()
    style = load_figure_style(root)
    data_path = root / "output" / "data" / "firstprinciples" / "active_selection_demo.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    sweep = list(data.get("validity_sweep") or [])
    policies = list(data.get("policies") or [])
    prior_entropy = float(data.get("prior_entropy_nats", 0.0))
    efe_pick = str(data.get("efe_selected_policy", ""))

    validities = [float(row["cue_validity"]) for row in sweep]
    epistemic_sweep = [float(row["epistemic_value"]) for row in sweep]
    residual_sweep = [float(row["residual_gap"]) for row in sweep]

    names = [str(p["name"]) for p in policies]
    efe = [float(p["efe"]) for p in policies]
    epistemic = [float(p["epistemic_value"]) for p in policies]
    pragmatic = [float(p["pragmatic_value"]) for p in policies]
    residual = [float(p["residual_gap"]) for p in policies]

    out = figure_output_path(root, "active_selection_landscape")
    with apply_style(style):
        fig, (sweep_ax, bar_ax) = plt.subplots(
            1, 2, figsize=(14.0, 5.3), gridspec_kw={"width_ratios": [1.0, 1.15]}
        )
        sweep_ax.plot(
            validities, epistemic_sweep, marker="o",
            color=style.color("accent"), label="epistemic value I(o;r)",
        )
        sweep_ax.plot(
            validities, residual_sweep, marker="s",
            color=style.color("secondary"), label="residual gap E_o[H(r|o)]",
        )
        sweep_ax.axhline(
            prior_entropy, ls="--", color=style.color("reference"),
            label=f"prior entropy H(r)={prior_entropy:.3f}",
        )
        sweep_ax.set_xlabel("Cue validity")
        sweep_ax.set_ylabel("Nats")
        sweep_ax.set_title("Cue-validity sweep")
        sweep_ax.set_ylim(0.0, max(prior_entropy * 1.15, 0.1))
        style_grid(sweep_ax, style)
        sweep_ax.legend(frameon=True, fontsize=style.font_size("legend"), loc="center left")
        sweep_ax.annotate(
            "epistemic + residual = H(r)",
            xy=(0.62, 0.5), xycoords="axes fraction",
            fontsize=style.font_size("annotation"), color=style.color("primary"),
        )

        x = np.arange(len(names))
        width = 0.2
        bar_ax.bar(x - 1.5 * width, efe, width, label="EFE G", color=style.color("primary"))
        bar_ax.bar(x - 0.5 * width, epistemic, width, label="epistemic", color=style.color("accent"))
        bar_ax.bar(x + 0.5 * width, pragmatic, width, label="pragmatic", color="#7c3aed")
        bar_ax.bar(x + 1.5 * width, residual, width, label="residual", color=style.color("secondary"))
        bar_ax.axhline(0.0, color=style.color("muted"), lw=0.8)
        bar_ax.set_xticks(x, names, fontsize=style.font_size("dense"))
        bar_ax.set_ylabel("Nats")
        bar_ax.set_title(f"Expected free energy selects '{efe_pick}'")
        style_grid(bar_ax, style)
        bar_ax.legend(frameon=True, fontsize=style.font_size("legend"), ncol=2)

        fig.tight_layout(rect=(0.0, 0.03, 1.0, 1.0))
        fig.text(
            0.01, 0.01,
            "Source: output/data/firstprinciples/active_selection_demo.json; finite flat-prior toy, exact.",
            fontsize=style.font_size("source"), color=style.color("muted"),
        )
        save_styled_figure(fig, out, style)
    return out


def figure_si_belief_entropy_trajectory(project_root: Path) -> Path:
    """Per-step bridge: analytical belief-entropy prediction overlaid on the pymdp SI trace.

    The closed-form running-Bayesian belief entropy (line) is overlaid on the pymdp
    sophisticated-inference agent's measured belief entropy at each step (points);
    they coincide at every step, demonstrating the trajectory-level match.
    """
    root = project_root.resolve()
    style = load_figure_style(root)
    data = json.loads((root / "output" / "data" / "firstprinciples" / "si_bridge_demo.json").read_text(encoding="utf-8"))
    analytical = [float(x) for x in data["analytical_entropy_by_step"]]
    pymdp = [float(x) for x in data["belief_entropy_by_step"]]
    max_err = float(data["max_trajectory_error_abs"])
    steps = list(range(len(pymdp)))

    out = figure_output_path(root, "si_belief_entropy_trajectory")
    with apply_style(style):
        fig, ax = plt.subplots(1, 1, figsize=(8.4, 5.3))
        ax.plot(steps, analytical, color=style.color("secondary"), marker="o", markersize=4,
                label="analytical running-Bayesian H(r)")
        ax.scatter(steps, pymdp, s=90, zorder=5, facecolor="none",
                   edgecolor=style.color("accent"), linewidths=1.8, label="pymdp SI belief entropy")
        ax.set_xlabel("Rollout step")
        ax.set_ylabel("Belief entropy (nats)")
        ax.set_title("Closed-form prediction matches the SI agent at every step")
        ax.set_xticks(steps)
        style_grid(ax, style)
        ax.legend(frameon=True, fontsize=style.font_size("legend"), loc="upper right")
        ax.annotate(
            f"max trajectory error: {max_err:.1e} nats",
            xy=(0.04, 0.06), xycoords="axes fraction",
            fontsize=style.font_size("annotation"), color=style.color("primary"),
        )
        fig.tight_layout(rect=(0.0, 0.03, 1.0, 1.0))
        fig.text(0.01, 0.01,
                 "Source: output/data/firstprinciples/si_bridge_demo.json; finite toy, observable bridge.",
                 fontsize=style.font_size("source"), color=style.color("muted"))
        save_styled_figure(fig, out, style)
    return out


def figure_si_bridge_match(project_root: Path) -> Path:
    """Analytical residual curve with the pymdp SI agent's post-cue entropy on it.

    The closed-form residual E_o[H(r|o)] (reused from the active-selection module)
    is plotted as a smooth curve against cue validity; the pymdp sophisticated-
    inference agent's measured post-cue belief entropy is overlaid as a single
    point that lands on the curve at the environment's own cue validity --
    the quantitative analytical<->simulation bridge.
    """
    from firstprinciples import si_bridge

    root = project_root.resolve()
    style = load_figure_style(root)
    data = json.loads((root / "output" / "data" / "firstprinciples" / "si_bridge_demo.json").read_text(encoding="utf-8"))
    env_validity = float(data["cue_validity"])
    pymdp_entropy = float(data["post_cue_belief_entropy"])
    match_abs = float(data["residual_entropy_match_abs"])

    grid = [0.5 + 0.01 * i for i in range(51)]  # 0.50 .. 1.00
    residual_curve = [si_bridge.analytical_residual_at_validity(v) for v in grid]

    out = figure_output_path(root, "si_bridge_match")
    with apply_style(style):
        fig, ax = plt.subplots(1, 1, figsize=(8.4, 5.3))
        ax.plot(grid, residual_curve, color=style.color("secondary"),
                label="analytical residual $E_o[H(r\\mid o)]$")
        ax.scatter([env_validity], [pymdp_entropy], s=120, zorder=5,
                   color=style.color("accent"), edgecolor="white",
                   label="pymdp SI post-cue belief entropy")
        ax.axvline(env_validity, ls=":", color=style.color("muted"), lw=1.0)
        ax.set_xlabel("Cue validity")
        ax.set_ylabel("Nats")
        ax.set_title("Closed-form residual predicts the pymdp SI agent")
        style_grid(ax, style)
        ax.legend(frameon=True, fontsize=style.font_size("legend"), loc="upper right")
        ax.annotate(
            f"match at validity {env_validity:.2f}: |Δ| = {match_abs:.1e} nats",
            xy=(env_validity, pymdp_entropy), xytext=(0.30, 0.30), textcoords="axes fraction",
            fontsize=style.font_size("annotation"), color=style.color("primary"),
            arrowprops=dict(arrowstyle="->", color=style.color("muted")),
        )
        fig.tight_layout(rect=(0.0, 0.03, 1.0, 1.0))
        fig.text(0.01, 0.01,
                 "Source: output/data/firstprinciples/{si_bridge_demo,active_selection_demo}.json; finite toy, observable bridge.",
                 fontsize=style.font_size("source"), color=style.color("muted"))
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
                fixed_value + 0.085,
                f"fixed point={fixed_value:.3f}",
                transform=ax.get_yaxis_transform(),
                fontsize=style.font_size("annotation"),
                color=style.color("reference"),
            )
        ax.annotate(
            "teacher-forced path",
            xy=(xs[min(1, len(xs) - 1)], off_policy[min(1, len(off_policy) - 1)] if off_policy else 0.0),
            xytext=(42, -28),
            textcoords="offset points",
            fontsize=style.font_size("annotation"),
            color=style.color("fail"),
            arrowprops={"arrowstyle": "->", "color": style.color("fail"), "linewidth": 0.8},
        )
        if on_policy:
            mid = min(max(len(on_policy) // 2, 1), len(on_policy) - 1)
            ax.annotate(
                "student-visited correction loop",
                xy=(xs[mid], on_policy[mid]),
                xytext=(18, 42),
                textcoords="offset points",
                fontsize=style.font_size("annotation"),
                color=style.color("pass"),
                arrowprops={"arrowstyle": "->", "color": style.color("pass"), "linewidth": 0.8},
            )
        ax.set_xlabel("Generated step")
        ax.set_ylabel("Expected correctness (closed form)")
        ax.set_ylim(0.0, 1.02)
        ax.set_title("On-policy correction changes the generated trajectory (toy drift model)")
        style_grid(ax, style)
        ax.legend(frameon=True, fontsize=style.font_size("legend"))
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
        div_ax.legend(frameon=True, fontsize=style.font_size("legend"))
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


def figure_sequential_shift_recovery(project_root: Path) -> Path:
    """Render the deterministic finite sequential train/test shift witness."""
    root = project_root.resolve()
    style = load_figure_style(root)
    data_path = root / "output" / "data" / "firstprinciples" / "sequential_shift.json"
    if not data_path.exists():
        from firstprinciples import sequential_shift

        data_path.parent.mkdir(parents=True, exist_ok=True)
        data_path.write_text(
            json.dumps(sequential_shift.build_payload(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    data = json.loads(data_path.read_text(encoding="utf-8"))
    state_names = [str(name).replace("_", "\n") for name in data.get("state_names") or []]
    train = np.array(data.get("train_visitation") or [], dtype=np.float64)
    test_before = np.array(data.get("student_test_visitation_before") or [], dtype=np.float64)
    test_after = np.array(data.get("student_test_visitation_after") or [], dtype=np.float64)
    losses = [
        float(data.get("train_loss", 0.0)),
        float(data.get("test_loss_before", data.get("student_induced_test_loss_before", 0.0))),
        float(data.get("test_loss_after", 0.0)),
    ]
    shift_mass = float(data.get("shift_mass", 0.0))
    gap_closed = float(data.get("gap_closed", 0.0))
    out = figure_output_path(root, "sequential_shift_recovery")
    with apply_style(style):
        fig, axes = plt.subplots(
            1,
            2,
            figsize=(12.6, 5.1),
            gridspec_kw={"width_ratios": [1.35, 0.9]},
            constrained_layout=True,
        )
        visit_ax, loss_ax = axes
        x = np.arange(len(state_names))
        width = 0.25
        visit_ax.bar(x - width, train, width, label="teacher-forced train", color=style.color("secondary"))
        visit_ax.bar(x, test_before, width, label="student test before", color=style.color("fail"), alpha=0.88)
        visit_ax.bar(x + width, test_after, width, label="student test after", color=style.color("pass"), alpha=0.88)
        visit_ax.set_xticks(x, state_names, fontsize=style.font_size("dense"))
        visit_ax.set_ylabel("Average visitation mass")
        visit_ax.set_title("Student rollouts shift the state distribution")
        visit_ax.set_ylim(0.0, max(0.72, float(max(train.max(), test_before.max(), test_after.max())) * 1.14))
        style_grid(visit_ax, style)
        visit_ax.legend(frameon=True, fontsize=style.font_size("legend"))
        visit_ax.text(
            0.02,
            0.94,
            f"shift mass = {shift_mass:.3f}",
            transform=visit_ax.transAxes,
            va="top",
            fontsize=style.font_size("annotation"),
            color=style.color("primary"),
            bbox=dict(boxstyle="round,pad=0.28", facecolor="#f8fafc", edgecolor=style.color("reference")),
        )

        loss_names = ["train\nloss", "test\nbefore", "test\nafter"]
        colors = [style.color("secondary"), style.color("fail"), style.color("pass")]
        bars = loss_ax.bar(np.arange(3), losses, color=colors, alpha=0.9)
        loss_ax.set_xticks(np.arange(3), loss_names, fontsize=style.font_size("dense"))
        loss_ax.set_ylabel("Reverse-KL loss (nats)")
        loss_ax.set_title("On-policy correction reduces test loss")
        loss_ax.set_ylim(0.0, max(losses) * 1.34)
        style_grid(loss_ax, style)
        for bar, value in zip(bars, losses, strict=True):
            loss_ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + max(losses) * 0.035,
                f"{value:.3f}",
                ha="center",
                fontsize=style.font_size("annotation"),
            )
        loss_ax.annotate(
            f"closed {gap_closed:.3f} nats",
            xy=(2, losses[2]),
            xytext=(-78, 42),
            textcoords="offset points",
            fontsize=style.font_size("annotation"),
            color=style.color("primary"),
            arrowprops={"arrowstyle": "->", "color": style.color("primary"), "linewidth": 0.9},
            bbox=dict(boxstyle="round,pad=0.28", facecolor="#f8fafc", edgecolor=style.color("reference")),
        )
        fig.suptitle("Sequential-shift witness: teacher forcing underweights student-induced states")
        fig.text(
            0.01,
            0.01,
            "Source: output/data/firstprinciples/sequential_shift.json; deterministic finite witness, not an empirical OPD benchmark.",
            fontsize=style.font_size("source"),
            color=style.color("muted"),
        )
        save_styled_figure(fig, out, style)
    return out


def figure_sequential_shift_sensitivity(project_root: Path) -> Path:
    """Render the finite correction-dose sensitivity sweep for sequential shift."""
    root = project_root.resolve()
    style = load_figure_style(root)
    data_path = root / "output" / "data" / "firstprinciples" / "sequential_shift_sensitivity.json"
    if not data_path.exists():
        from firstprinciples import sequential_shift

        data_path.parent.mkdir(parents=True, exist_ok=True)
        data_path.write_text(
            json.dumps(sequential_shift.build_sensitivity_payload(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    data = json.loads(data_path.read_text(encoding="utf-8"))
    rows = data.get("rows") or []
    fractions = np.array([float(row.get("correction_fraction", 0.0)) for row in rows], dtype=np.float64)
    train_losses = np.array([float(row.get("train_loss", 0.0)) for row in rows], dtype=np.float64)
    test_losses = np.array([float(row.get("test_loss", 0.0)) for row in rows], dtype=np.float64)
    shift_masses = np.array([float(row.get("shift_mass", 0.0)) for row in rows], dtype=np.float64)
    drift_visits = np.array([float(row.get("student_drift_visitation", 0.0)) for row in rows], dtype=np.float64)
    reduction = float(data.get("test_loss_reduction", 0.0))
    shift_reduction = float(data.get("shift_mass_reduction", 0.0))
    out = figure_output_path(root, "sequential_shift_sensitivity")
    with apply_style(style):
        fig, axes = plt.subplots(
            1,
            2,
            figsize=(12.2, 4.9),
            gridspec_kw={"width_ratios": [1.0, 1.0]},
            constrained_layout=True,
        )
        loss_ax, shift_ax = axes
        loss_ax.plot(
            fractions,
            test_losses,
            marker="o",
            linewidth=2.2,
            color=style.color("fail"),
            label="student-induced test loss",
        )
        loss_ax.plot(
            fractions,
            train_losses,
            marker="s",
            linewidth=1.8,
            color=style.color("secondary"),
            label="teacher-forced train estimate",
        )
        loss_ax.set_xlabel("Correction fraction")
        loss_ax.set_ylabel("Reverse-KL loss (nats)")
        loss_ax.set_title("Correction dose lowers induced test loss")
        loss_ax.set_ylim(0.0, max(float(test_losses.max()), float(train_losses.max())) * 1.20)
        style_grid(loss_ax, style)
        loss_ax.legend(frameon=True, fontsize=style.font_size("legend"))
        loss_ax.annotate(
            f"test loss reduced\n{reduction:.3f} nats",
            xy=(fractions[-1], test_losses[-1]),
            xytext=(-92, 34),
            textcoords="offset points",
            fontsize=style.font_size("annotation"),
            color=style.color("primary"),
            arrowprops={"arrowstyle": "->", "color": style.color("primary"), "linewidth": 0.9},
            bbox=dict(boxstyle="round,pad=0.28", facecolor="#f8fafc", edgecolor=style.color("reference")),
        )

        shift_ax.plot(
            fractions,
            shift_masses,
            marker="o",
            linewidth=2.2,
            color=style.color("accent"),
            label="train/test shift mass",
        )
        shift_ax.plot(
            fractions,
            drift_visits,
            marker="^",
            linewidth=1.8,
            color=style.color("pass"),
            label="student_drift visitation",
        )
        shift_ax.set_xlabel("Correction fraction")
        shift_ax.set_ylabel("Probability mass")
        shift_ax.set_title("Correction dose reduces the drift state")
        shift_ax.set_ylim(0.0, max(float(shift_masses.max()), float(drift_visits.max())) * 1.22)
        style_grid(shift_ax, style)
        shift_ax.legend(frameon=True, fontsize=style.font_size("legend"))
        shift_ax.annotate(
            f"shift mass reduced\n{shift_reduction:.3f}",
            xy=(fractions[-1], shift_masses[-1]),
            xytext=(-90, 42),
            textcoords="offset points",
            fontsize=style.font_size("annotation"),
            color=style.color("primary"),
            arrowprops={"arrowstyle": "->", "color": style.color("primary"), "linewidth": 0.9},
            bbox=dict(boxstyle="round,pad=0.28", facecolor="#f8fafc", edgecolor=style.color("reference")),
        )
        fig.suptitle("Sequential-shift sensitivity: finite correction-dose sweep")
        fig.text(
            0.01,
            0.01,
            "Source: output/data/firstprinciples/sequential_shift_sensitivity.json; deterministic finite sweep, not an empirical OPD benchmark.",
            fontsize=style.font_size("source"),
            color=style.color("muted"),
        )
        save_styled_figure(fig, out, style)
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
            frameon=True,
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
        ax.legend(frameon=True, fontsize=style.font_size("legend"), loc="best")
        style_grid(ax, style)
        fig.text(0.01, 0.01, "Source: output/data/firstprinciples/diversity_demo.json", fontsize=style.font_size("source"), color=style.color("muted"))
        save_styled_figure(fig, out, style)
    return out


def figure_privilege_dose_response(project_root: Path) -> Path:
    """Teacher-privilege dose-response: entropy gap is a threshold, reverse KL is the sensitive detector."""
    root = project_root.resolve()
    style = load_figure_style(root)
    data = json.loads(
        (root / "output" / "data" / "firstprinciples" / "privilege_sweep.json").read_text(encoding="utf-8")
    )
    levels = data["levels"]
    validities = [float(row["teacher_cue_validity"]) for row in levels]
    gaps = [float(row["entropy_gap"]) for row in levels]
    signals = [float(row["mean_reverse_kl"]) for row in levels]
    out = figure_output_path(root, "privilege_dose_response")
    with apply_style(style):
        fig, (gap_ax, kl_ax) = plt.subplots(1, 2, figsize=(11.6, 4.6))
        gap_ax.plot(validities, gaps, marker="o", color=style.color("secondary"), linewidth=2.0)
        gap_ax.axhline(0.0, color=style.color("muted"), linewidth=0.9, linestyle=":")
        gap_ax.set_xlabel("teacher cue validity")
        gap_ax.set_ylabel("belief-entropy gap (student − teacher, nats)")
        gap_ax.set_title("Entropy advantage is a threshold")
        gap_ax.annotate(
            f"baseline gap = {data['baseline_gap']:.1f}\n(identical agents)",
            xy=(validities[0], gaps[0]),
            xytext=(8, 18),
            textcoords="offset points",
            fontsize=style.font_size("annotation"),
            color=style.color("primary"),
            arrowprops={"arrowstyle": "->", "color": style.color("muted"), "linewidth": 0.8},
        )
        gap_ax.annotate(
            f"{gaps[-1]:+.3f}",
            xy=(validities[-1], gaps[-1]),
            xytext=(-38, -2),
            textcoords="offset points",
            fontsize=style.font_size("annotation"),
            color=style.color("primary"),
        )
        gap_ax.set_ylim(min(gaps) - 0.01, max(gaps) * 1.25 + 0.01)
        style_grid(gap_ax, style)

        kl_ax.semilogy(
            validities,
            [max(value, 1e-4) for value in signals],
            marker="s",
            color=style.color("accent"),
            linewidth=2.0,
        )
        kl_ax.set_xlabel("teacher cue validity")
        kl_ax.set_ylabel("mean reverse KL (nats, log scale)")
        kl_ax.set_title("The distillation signal detects privilege earlier")
        for validity, signal in zip(validities, signals, strict=True):
            if signal > 0.0:
                kl_ax.annotate(
                    f"{signal:.3g}",
                    xy=(validity, max(signal, 1e-4)),
                    xytext=(0, 8),
                    textcoords="offset points",
                    ha="center",
                    fontsize=style.font_size("annotation"),
                    color=style.color("primary"),
                )
        kl_ax.set_ylim(5e-5, max(max(signals), 1e-3) * 8.0)
        kl_ax.text(
            0.03,
            0.92,
            "values below 1e-4 plotted at the axis floor",
            transform=kl_ax.transAxes,
            fontsize=style.font_size("source"),
            color=style.color("muted"),
        )
        style_grid(kl_ax, style)
        fig.suptitle("Teacher-privilege dose-response (deterministic classroom sweep)")
        fig.text(
            0.01,
            0.01,
            "Source: output/data/firstprinciples/privilege_sweep.json",
            fontsize=style.font_size("source"),
            color=style.color("muted"),
        )
        save_styled_figure(fig, out, style)
    return out
