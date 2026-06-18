"""Introductory reader-map figures for the manuscript's early sections."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

from .figure_io import save_figure_png
from .figure_registry import figure_output_path
from .figure_style import apply_style, load_figure_style


def _load_required_json(root: Path, rel: str) -> dict[str, Any]:
    path = root / rel
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"expected object payload in {rel}")
    return payload


def figure_opd_reader_map(project_root: Path) -> Path:
    """Render the first-read mechanism map for the opening motivation section."""
    root = project_root.resolve()
    style = load_figure_style(root)
    correspondence = _load_required_json(root, "output/data/firstprinciples/correspondence_map.json")
    exposure = _load_required_json(root, "output/data/firstprinciples/exposure_bias_demo.json")
    sequential = _load_required_json(root, "output/data/firstprinciples/sequential_shift.json")
    dependency_graph = _load_required_json(root, "output/data/validation_dependency_graph.json")
    if not (
        correspondence.get("rows")
        and (exposure.get("curves") or {}).get("off_policy")
        and sequential.get("student_test_visitation_after")
        and dependency_graph.get("edges")
    ):
        raise RuntimeError("reader map source artifacts are incomplete")

    out = figure_output_path(root, "opd_reader_map")
    paper = style.color("paper")
    panel_bg = style.color("panel_bg")
    ink = style.color("primary")
    muted = style.color("muted")
    edge = style.color("panel_edge")
    teacher = style.color("teacher")
    student = style.color("student")
    analytical = style.color("analytical")
    energy = style.color("energy")
    validation = style.color("validation")

    def draw_panel(
        ax: plt.Axes,
        x: float,
        y: float,
        width: float,
        height: float,
        *,
        title: str,
        eyebrow: str,
        body: list[str],
        color: str,
    ) -> None:
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                width,
                height,
                boxstyle="round,pad=0.045,rounding_size=0.08",
                linewidth=1.05,
                edgecolor=edge,
                facecolor=paper,
            )
        )
        ax.add_patch(Rectangle((x, y + height - 0.16), width, 0.16, facecolor=color, edgecolor="none"))
        ax.text(
            x + 0.17,
            y + height - 0.43,
            eyebrow.upper(),
            fontsize=style.font_size("dense"),
            color=muted,
            fontweight="bold",
        )
        ax.text(
            x + 0.17,
            y + height - 0.78,
            title,
            fontsize=style.font_size("small"),
            color=color,
            fontweight="bold",
        )
        cursor = y + height - 1.18
        for line in body:
            wrapped = textwrap.wrap(line, width=max(24, int(width * 9.4)), break_long_words=False)
            for text in wrapped:
                ax.text(x + 0.17, cursor, text, fontsize=style.font_size("dense"), color=ink, va="top")
                cursor -= 0.25
            cursor -= 0.06

    def arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float], color: str) -> None:
        ax.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>",
                mutation_scale=15,
                linewidth=1.35,
                color=color,
                alpha=0.78,
            )
        )

    with apply_style(style):
        fig = plt.figure(figsize=(15.0, 8.4), facecolor=paper)
        ax = fig.add_axes((0.0, 0.0, 1.0, 1.0))
        ax.set_xlim(0.0, 15.0)
        ax.set_ylim(0.0, 8.4)
        ax.axis("off")
        ax.add_patch(Rectangle((0, 0), 15.0, 8.4, facecolor=paper, edgecolor="none"))
        ax.add_patch(Rectangle((0, 7.58), 15.0, 0.82, facecolor=ink, edgecolor="none"))
        ax.add_patch(Rectangle((0, 7.47), 15.0, 0.11, facecolor=analytical, edgecolor="none"))
        ax.text(
            0.48,
            8.02,
            "Figure 1 mechanism map: OPD in finite active-inference terms",
            fontsize=style.font_size("title"),
            color="white",
            fontweight="bold",
            va="center",
        )
        ax.text(
            0.50,
            7.66,
            "Problem -> teacher target -> student-owned rollout -> VFE update, with EFE kept on the planning side",
            fontsize=style.font_size("source"),
            color="#e0f2fe",
            va="center",
        )

        draw_panel(
            ax,
            0.56,
            5.07,
            3.05,
            1.86,
            title="Problem surface",
            eyebrow="why on-policy",
            body=[
                "off-policy teacher forcing can train on states the student will not visit",
                "the finite object names the distribution being compared",
            ],
            color=analytical,
        )
        draw_panel(
            ax,
            4.05,
            5.07,
            2.85,
            1.86,
            title="Teacher target",
            eyebrow="generative model",
            body=[
                "privileged policy supplies the finite target",
                "scope is declared before comparison",
            ],
            color=teacher,
        )
        draw_panel(
            ax,
            7.36,
            5.07,
            2.85,
            1.86,
            title="Student rollout",
            eyebrow="posterior path",
            body=[
                "student induces the observations it learns from",
                "posterior family is evaluated on that path",
            ],
            color=student,
        )
        draw_panel(
            ax,
            10.68,
            5.07,
            3.76,
            1.86,
            title="Reverse-KL / VFE update",
            eyebrow="perception lane",
            body=[
                "reverse KL is read as finite VFE up to an evidence constant",
                "sequential-shift witness tests the correction",
            ],
            color=energy,
        )

        for start, end, color in (
            ((3.62, 6.00), (4.01, 6.00), analytical),
            ((6.91, 6.00), (7.32, 6.00), teacher),
            ((10.22, 6.00), (10.64, 6.00), student),
        ):
            arrow(ax, start, end, color)

        ax.add_patch(
            FancyBboxPatch(
                (0.80, 3.66),
                6.28,
                0.50,
                boxstyle="round,pad=0.04,rounding_size=0.06",
                linewidth=0.9,
                edgecolor=energy,
                facecolor="#fff7ed",
            )
        )
        ax.text(
            1.06,
            3.97,
            "VFE lane",
            fontsize=style.font_size("dense"),
            color=energy,
            fontweight="bold",
            va="center",
        )
        ax.text(
            2.04,
            3.97,
            "posterior update / reverse-KL comparison on the student-induced measure",
            fontsize=style.font_size("dense"),
            color=ink,
            va="center",
        )
        ax.add_patch(
            FancyBboxPatch(
                (7.48, 3.66),
                6.72,
                0.50,
                boxstyle="round,pad=0.04,rounding_size=0.06",
                linewidth=0.9,
                edgecolor=validation,
                facecolor="#ecfeff",
            )
        )
        ax.text(
            7.74,
            3.97,
            "EFE lane",
            fontsize=style.font_size("dense"),
            color=validation,
            fontweight="bold",
            va="center",
        )
        ax.text(
            8.72,
            3.97,
            "planning-side action selection; separated from the reverse-KL/VFE identity",
            fontsize=style.font_size("dense"),
            color=ink,
            va="center",
        )

        ax.add_patch(
            FancyBboxPatch(
                (1.08, 1.38),
                12.84,
                2.08,
                boxstyle="round,pad=0.06,rounding_size=0.10",
                linewidth=1.15,
                edgecolor=validation,
                facecolor=panel_bg,
            )
        )
        ax.text(
            1.36,
            3.02,
            "Validation boundary keeps the early picture finite",
            fontsize=style.font_size("subtitle"),
            color=validation,
            fontweight="bold",
            va="center",
        )
        spine_steps = [
            ("source artifacts", "first-principles JSON and sheaf registries"),
            ("figure source map", "caption claims bind to artifact fields"),
            ("hash manifest", "declared images are fresh and non-stray"),
            ("strict compose", "figures enter through section_figures only"),
        ]
        for idx, (title, body) in enumerate(spine_steps):
            x = 1.38 + idx * 3.05
            ax.add_patch(
                FancyBboxPatch(
                    (x, 1.78),
                    2.52,
                    0.74,
                    boxstyle="round,pad=0.04,rounding_size=0.06",
                    linewidth=0.85,
                    edgecolor=edge,
                    facecolor=paper,
                )
            )
            ax.text(x + 0.12, 2.30, title, fontsize=style.font_size("dense"), color=ink, fontweight="bold")
            ax.text(
                x + 0.12,
                2.04,
                "\n".join(textwrap.wrap(body, width=29, break_long_words=False)),
                fontsize=style.font_size("dense"),
                color=muted,
                va="top",
            )
            if idx < len(spine_steps) - 1:
                arrow(ax, (x + 2.58, 2.15), (x + 2.95, 2.15), validation)
        for x in (2.08, 5.48, 8.78, 12.20):
            arrow(ax, (x, 4.96), (x, 3.52), validation)

        ax.add_patch(Rectangle((0, 0), 15.0, 0.64, facecolor="#eff6ff", edgecolor="none"))
        ax.text(
            0.46,
            0.41,
            (
                "Sources: correspondence_map.json, exposure_bias_demo.json, sequential_shift.json, "
                "validation_dependency_graph.json. Finite toy/artifact claims only; not a production-LLM "
                "benchmark, biological mechanism, or universal theorem."
            ),
            fontsize=style.font_size("source"),
            color=ink,
            va="center",
        )
        save_figure_png(fig, out, dpi=style.dpi, facecolor=paper, transparent=False)
    return out


def figure_opd_situational_awareness(project_root: Path) -> Path:
    """Render the early situational-awareness atlas for OPD and active inference."""
    root = project_root.resolve()
    style = load_figure_style(root)
    correspondence = _load_required_json(root, "output/data/firstprinciples/correspondence_map.json")
    sequential = _load_required_json(root, "output/data/firstprinciples/sequential_shift.json")
    classroom = _load_required_json(root, "output/data/firstprinciples/classroom.json")
    energy = _load_required_json(root, "output/data/firstprinciples/energy_demo.json")
    taxonomy = _load_required_json(root, "output/data/firstprinciples/opd_taxonomy.json")
    dependency_graph = _load_required_json(root, "output/data/validation_dependency_graph.json")
    variables = _load_required_json(root, "output/data/manuscript_variables.json")
    if not all(
        (
            correspondence.get("rows"),
            sequential.get("student_test_visitation_after"),
            classroom.get("per_step"),
            energy.get("vfe_at_prior"),
            taxonomy.get("methods"),
            dependency_graph.get("edges"),
            variables.get("sheaf_track_count"),
        )
    ):
        raise RuntimeError("situational-awareness source artifacts are incomplete")

    out = figure_output_path(root, "opd_situational_awareness")
    paper = style.color("paper")
    panel_bg = style.color("panel_bg")
    ink = style.color("primary")
    muted = style.color("muted")
    edge = style.color("panel_edge")
    teacher = style.color("teacher")
    student = style.color("student")
    analytical = style.color("analytical")
    energy_color = style.color("energy")
    validation = style.color("validation")

    def arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float], color: str) -> None:
        ax.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>",
                mutation_scale=14,
                linewidth=1.25,
                color=color,
                alpha=0.76,
            )
        )

    def atlas_box(
        ax: plt.Axes,
        x: float,
        y: float,
        width: float,
        height: float,
        *,
        eyebrow: str,
        title: str,
        lines: list[str],
        color: str,
        wrap: int,
    ) -> None:
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                width,
                height,
                boxstyle="round,pad=0.05,rounding_size=0.08",
                linewidth=1.0,
                edgecolor=edge,
                facecolor=paper,
            )
        )
        ax.add_patch(Rectangle((x, y + height - 0.16), width, 0.16, facecolor=color, edgecolor="none"))
        ax.text(
            x + 0.18,
            y + height - 0.42,
            eyebrow.upper(),
            fontsize=style.font_size("dense"),
            color=muted,
            fontweight="bold",
        )
        ax.text(
            x + 0.18,
            y + height - 0.76,
            title,
            fontsize=style.font_size("small"),
            color=color,
            fontweight="bold",
        )
        cursor = y + height - 1.12
        for line in lines:
            for wrapped in textwrap.wrap(line, width=wrap, break_long_words=False):
                ax.text(x + 0.20, cursor, wrapped, fontsize=style.font_size("dense"), color=ink, va="top")
                cursor -= 0.24
            cursor -= 0.06

    with apply_style(style):
        fig = plt.figure(figsize=(15.6, 9.0), facecolor=paper)
        ax = fig.add_axes((0.0, 0.0, 1.0, 1.0))
        ax.set_xlim(0.0, 15.6)
        ax.set_ylim(0.0, 9.0)
        ax.axis("off")
        ax.add_patch(Rectangle((0, 0), 15.6, 9.0, facecolor=paper, edgecolor="none"))
        ax.add_patch(Rectangle((0, 8.12), 15.6, 0.88, facecolor=ink, edgecolor="none"))
        ax.add_patch(Rectangle((0, 8.00), 15.6, 0.12, facecolor=analytical, edgecolor="none"))
        ax.text(
            0.50,
            8.58,
            "Situational awareness atlas: Active Inference, OPD, and this paper",
            fontsize=style.font_size("title"),
            color="white",
            fontweight="bold",
            va="center",
        )
        ax.text(
            0.52,
            8.20,
            "Orient concepts, local witnesses, validation spine, and non-claims before the correspondence dictionary",
            fontsize=style.font_size("source"),
            color="#e0f2fe",
            va="center",
        )

        atlas_box(
            ax,
            0.52,
            5.82,
            3.28,
            1.84,
            eyebrow="active inference",
            title="Finite agent model",
            lines=[
                "generative model, posterior belief, observation, and action are declared objects",
                "VFE scores inference; EFE scores planning",
            ],
            color=analytical,
            wrap=34,
        )
        atlas_box(
            ax,
            4.16,
            5.82,
            3.28,
            1.84,
            eyebrow="OPD",
            title="Teacher-student loop",
            lines=[
                "teacher policy defines the target distribution",
                "student rollout determines where the target is queried",
            ],
            color=teacher,
            wrap=34,
        )
        atlas_box(
            ax,
            7.80,
            5.82,
            3.28,
            1.84,
            eyebrow="shared object",
            title="Correspondence map",
            lines=[
                "finite rows connect active-inference terms to OPD counterparts",
                "dictionary is scoped before results",
            ],
            color=student,
            wrap=34,
        )
        atlas_box(
            ax,
            11.44,
            5.82,
            3.62,
            1.84,
            eyebrow="this paper",
            title="Deterministic witnesses",
            lines=[
                "Bernoulli-Ising, pymdp T-maze, classroom, and sequential-shift artifacts",
                "claims are local to generated sources",
            ],
            color=energy_color,
            wrap=38,
        )
        for start, end, color in (
            ((3.86, 6.74), (4.12, 6.74), teacher),
            ((7.50, 6.74), (7.76, 6.74), student),
            ((11.14, 6.74), (11.40, 6.74), energy_color),
        ):
            arrow(ax, start, end, color)

        ax.add_patch(
            FancyBboxPatch(
                (0.72, 4.18),
                14.16,
                0.92,
                boxstyle="round,pad=0.05,rounding_size=0.08",
                linewidth=1.0,
                edgecolor=validation,
                facecolor=panel_bg,
            )
        )
        ax.text(
            0.98,
            4.78,
            "Reader route",
            fontsize=style.font_size("subtitle"),
            color=validation,
            fontweight="bold",
            va="center",
        )
        route_items = [
            ("Mechanism", "Figure 1"),
            ("Atlas", "this figure"),
            ("Dictionary", "correspondence map"),
            ("Evidence", "source-bound result figures"),
            ("Gates", "claim ledger and hash checks"),
        ]
        for idx, (label, detail) in enumerate(route_items):
            x = 2.88 + idx * 2.32
            ax.add_patch(
                FancyBboxPatch(
                    (x, 4.42),
                    1.78,
                    0.42,
                    boxstyle="round,pad=0.03,rounding_size=0.06",
                    linewidth=0.75,
                    edgecolor=edge,
                    facecolor=paper,
                )
            )
            ax.text(x + 0.10, 4.70, label, fontsize=style.font_size("dense"), color=ink, fontweight="bold")
            ax.text(x + 0.10, 4.52, detail, fontsize=style.font_size("dense"), color=muted)
            if idx < len(route_items) - 1:
                arrow(ax, (x + 1.84, 4.64), (x + 2.10, 4.64), validation)

        atlas_box(
            ax,
            0.70,
            1.42,
            4.42,
            2.08,
            eyebrow="not claimed",
            title="Boundary conditions",
            lines=[
                "not a production-LLM benchmark",
                "not a biological mechanism",
                "not a universal theorem about all distillation",
                "not a replacement for source-bound results",
            ],
            color=validation,
            wrap=42,
        )
        atlas_box(
            ax,
            5.58,
            1.42,
            4.38,
            2.08,
            eyebrow="local evidence",
            title="What is actually witnessed",
            lines=[
                "closed finite correspondence rows",
                "energy demo separates VFE and EFE roles",
                "classroom and sequential-shift artifacts show the local rollout correction",
            ],
            color=energy_color,
            wrap=43,
        )
        atlas_box(
            ax,
            10.42,
            1.42,
            4.44,
            2.08,
            eyebrow="trust surface",
            title="Why the atlas is source-bound",
            lines=[
                "figure source map binds captions to fields",
                "dependency graph links producers and consumers",
                "manuscript variables and validation gates fail closed on drift",
            ],
            color=analytical,
            wrap=43,
        )

        ax.add_patch(Rectangle((0, 0), 15.6, 0.70, facecolor="#f8fafc", edgecolor="none"))
        ax.text(
            0.52,
            0.45,
            (
                "Sources: correspondence_map.json, sequential_shift.json, classroom.json, energy_demo.json, "
                "opd_taxonomy.json, validation_dependency_graph.json, manuscript_variables.json."
            ),
            fontsize=style.font_size("source"),
            color=ink,
            va="center",
        )
        ax.text(
            15.04,
            0.18,
            "Situational atlas; finite source-bound orientation, not evidentiary inflation.",
            fontsize=style.font_size("source"),
            color=muted,
            ha="right",
            va="center",
        )
        save_figure_png(fig, out, dpi=style.dpi, facecolor=paper, transparent=False)
    return out
