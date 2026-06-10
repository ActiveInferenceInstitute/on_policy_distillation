"""Cover-page graphical abstract figure assembled from generated evidence artifacts."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

from .figure_io import save_figure_png
from .figure_registry import figure_output_path
from .figure_style import apply_style, load_figure_style


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
