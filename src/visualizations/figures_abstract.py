"""Cover-page graphical abstract figure assembled as a source-bound schematic."""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

from .figure_io import save_figure_png
from .figure_registry import figure_output_path
from .figure_style import apply_style, load_figure_style


def figure_graphical_abstract(project_root: Path) -> Path:
    """Render the cover-page graphical abstract as a quantitative-free schematic."""
    root = project_root.resolve()
    style = load_figure_style(root)

    out = figure_output_path(root, "graphical_abstract")

    background = style.color("cover_bg")
    ink = style.color("primary")
    muted = style.color("muted")
    paper = style.color("cover_panel")
    panel_edge = style.color("panel_edge")
    analytical = style.color("analytical")
    teacher = style.color("teacher")
    student = style.color("student")
    energy = style.color("energy")
    validation = style.color("validation")

    with apply_style(style):
        fig = plt.figure(figsize=(10.5, 10.5), facecolor=background)
        ax = fig.add_axes((0.0, 0.0, 1.0, 1.0))
        ax.set_xlim(0, 10.0)
        ax.set_ylim(0, 10.0)
        ax.axis("off")
        ax.set_facecolor(background)

        ax.add_patch(Rectangle((0, 0), 10.0, 10.0, facecolor=background, edgecolor="none"))
        ax.add_patch(Rectangle((0, 8.72), 10.0, 1.28, facecolor=ink, edgecolor="none"))
        ax.add_patch(Rectangle((0, 8.58), 10.0, 0.14, facecolor=analytical, edgecolor="none"))
        ax.add_patch(Rectangle((0, 0), 10.0, 0.36, facecolor="#dbeafe", edgecolor="none", alpha=0.82))

        ax.text(
            0.52,
            9.58,
            "On-Policy Distillation as Active Inference",
            fontsize=style.font_size("hero") * 0.78,
            fontweight="bold",
            color="white",
            va="center",
        )
        ax.text(
            0.54,
            9.12,
            "in Finite Variational Models",
            fontsize=style.font_size("title") * 1.18,
            fontweight="bold",
            color="#dbeafe",
            va="center",
        )
        ax.text(
            0.56,
            8.80,
            "reverse-KL free energy, student-induced sampling, deterministic toy witnesses",
            fontsize=style.font_size("small"),
            color="#eff6ff",
            va="center",
        )

        def concept_panel(
            x: float,
            y: float,
            width: float,
            height: float,
            title: str,
            eyebrow: str,
            lines: list[str],
            color: str,
        ) -> None:
            ax.add_patch(
                FancyBboxPatch(
                    (x, y),
                    width,
                    height,
                    boxstyle="round,pad=0.05,rounding_size=0.08",
                    linewidth=1.05,
                    edgecolor=panel_edge,
                    facecolor=paper,
                )
            )
            ax.add_patch(Rectangle((x, y + height - 0.13), width, 0.13, facecolor=color, edgecolor="none"))
            ax.text(
                x + 0.18,
                y + height - 0.40,
                eyebrow.upper(),
                fontsize=style.font_size("dense"),
                color=muted,
                fontweight="bold",
            )
            ax.text(
                x + 0.18,
                y + height - 0.76,
                title,
                fontsize=style.font_size("label"),
                fontweight="bold",
                color=color,
            )
            text_top = y + height - 1.08
            cursor_y = text_top
            for line in lines:
                for wrapped in textwrap.wrap(line, width=34):
                    ax.text(
                        x + 0.20,
                        cursor_y,
                        wrapped,
                        fontsize=style.font_size("dense"),
                        color=ink,
                        va="top",
                    )
                    cursor_y -= 0.24
                cursor_y -= 0.08

        concept_panel(
            0.46,
            5.78,
            3.72,
            2.18,
            "Finite variational model",
            "declared object",
            [
                "declared states and policies",
                "teacher as generative model",
                "toy-only scope boundary",
            ],
            analytical,
        )
        concept_panel(
            0.46,
            0.86,
            3.72,
            2.05,
            "Student-induced sampling",
            "trajectory",
            [
                "student visits its own states",
                "observations are sampled there",
                "no production-scale claim",
            ],
            student,
        )
        concept_panel(
            5.82,
            5.78,
            3.72,
            2.18,
            "VFE / EFE split",
            "VFE and EFE roles",
            [
                "reverse KL appears in VFE update",
                "EFE marks action selection only",
                "artifact-backed boundary",
            ],
            energy,
        )
        concept_panel(
            5.82,
            0.86,
            3.72,
            2.05,
            "Validation spine",
            "source bound",
            [
                "claim ledger plus source map",
                "figure registry plus PDF gates",
                "fails closed on drift",
            ],
            validation,
        )

        def node(x: float, y: float, label: str, body: str, color: str) -> None:
            ax.add_patch(Circle((x, y), 0.43, facecolor=paper, edgecolor=color, linewidth=1.7, zorder=5))
            ax.add_patch(Circle((x, y), 0.24, facecolor=color, edgecolor=paper, linewidth=0.8, zorder=6))
            ax.text(
                x,
                y + 0.02,
                label,
                fontsize=style.font_size("dense"),
                fontweight="bold",
                color="white",
                ha="center",
                va="center",
                zorder=7,
            )
            ax.text(x, y - 0.65, body, fontsize=style.font_size("dense"), color=ink, ha="center", zorder=7)

        center_x = 5.0
        ax.add_patch(
            FancyBboxPatch(
                (3.08, 3.15),
                3.84,
                2.52,
                boxstyle="round,pad=0.08,rounding_size=0.10",
                linewidth=1.4,
                edgecolor=ink,
                facecolor=paper,
                zorder=2,
            )
        )
        ax.text(
            center_x,
            5.32,
            "finite variational-model reading",
            fontsize=style.font_size("annotation"),
            fontweight="bold",
            color=ink,
            ha="center",
            zorder=3,
        )
        ax.text(
            center_x,
            4.94,
            "teacher / generative model -> student posterior",
            fontsize=style.font_size("annotation") * 1.06,
            fontweight="bold",
            color=analytical,
            ha="center",
            zorder=3,
        )
        ax.text(
            center_x,
            4.58,
            "student-induced observations close the loop",
            fontsize=style.font_size("annotation") * 0.96,
            fontweight="bold",
            color=energy,
            ha="center",
            zorder=3,
        )
        ax.text(
            center_x,
            4.08,
            "reverse-KL loss as VFE up to evidence constant",
            fontsize=style.font_size("small"),
            color=muted,
            ha="center",
            zorder=3,
        )
        ax.text(
            center_x,
            3.78,
            "correspondence, not universal identity",
            fontsize=style.font_size("dense"),
            color=ink,
            ha="center",
            zorder=3,
        )
        ax.add_patch(
            FancyBboxPatch(
                (3.24, 3.18),
                3.52,
                0.50,
                boxstyle="round,pad=0.035,rounding_size=0.06",
                linewidth=0.9,
                edgecolor=teacher,
                facecolor="#fff7ed",
                zorder=3,
            )
        )
        ax.text(
            center_x,
            3.48,
            "EFE: planning-side action selection",
            fontsize=style.font_size("dense"),
            color=teacher,
            fontweight="bold",
            ha="center",
            va="center",
            zorder=4,
        )
        ax.text(
            center_x,
            3.29,
            "not part of the reverse-KL update claim",
            fontsize=style.font_size("dense") * 0.92,
            color=teacher,
            ha="center",
            va="center",
            zorder=4,
        )

        loop_nodes = [
            (5.00, 6.64, "G", "teacher / generative", teacher),
            (7.28, 4.50, "Q", "student posterior", student),
            (5.00, 2.46, "O", "student observations", analytical),
            (2.72, 4.50, "F", "reverse-KL / VFE", energy),
        ]
        for x, y, label, body, color in loop_nodes:
            node(x, y, label, body, color)

        arrow_specs = [
            ((5.38, 6.45), (6.98, 4.88), -0.10, teacher),
            ((6.98, 4.12), (5.38, 2.68), -0.10, student),
            ((4.62, 2.68), (3.02, 4.12), -0.10, analytical),
            ((3.02, 4.88), (4.62, 6.45), -0.10, validation),
        ]
        for start, end, rad, color in arrow_specs:
            ax.add_patch(
                FancyArrowPatch(
                    start,
                    end,
                    arrowstyle="-|>",
                    mutation_scale=16,
                    linewidth=1.7,
                    color=color,
                    alpha=0.82,
                    connectionstyle=f"arc3,rad={rad}",
                    zorder=4,
                )
            )

        ax.text(
            9.55,
            0.16,
            "generated from repository artifacts; quantitative evidence stays in body figures and tables",
            fontsize=style.font_size("source"),
            color=ink,
            ha="right",
            va="center",
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
