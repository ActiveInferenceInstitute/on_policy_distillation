"""Analytical-track publication figures (Ising MI, free energy, energy decomposition)."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from analytical.hyperparameters import lambda_grid, load_hyperparameters
from analytical.sweep_io import read_parameter_sweep

from .figure_helpers import save_styled_figure, style_grid
from .figure_io import save_figure_png
from .figure_registry import figure_output_path
from .figure_style import apply_style, load_figure_style


def _read_sweep(path: Path) -> tuple[list[float], list[float], list[float]]:
    rows = read_parameter_sweep(path)
    lambdas = [row["lambda"] for row in rows]
    closed = [row["closed_form_mi"] for row in rows]
    empirical = [row["empirical_mi"] for row in rows]
    return lambdas, closed, empirical


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
        ax_main.legend(frameon=True, fontsize=style.font_size("legend"))
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
            xytext=(0.14, 0.40),
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
            0.98,
            0.30,
            "risk + ambiguity\nminus epistemic/pragmatic value",
            ha="right",
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
        curve_ax.legend(frameon=True, fontsize=style.font_size("legend"), loc="upper left")

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
