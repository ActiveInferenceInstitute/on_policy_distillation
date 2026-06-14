"""Cover-page graphical abstract figure assembled from generated evidence artifacts."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

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
    sequential_d = _json_or_empty(fp / "sequential_shift.json")
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
            "A Finite-Model Active-Inference Reading",
            fontsize=style.font_size("hero") * 0.78,
            fontweight="bold",
            color="white",
            va="center",
        )
        ax.text(
            0.54,
            9.12,
            "of On-Policy Distillation",
            fontsize=style.font_size("title") * 1.18,
            fontweight="bold",
            color="#dbeafe",
            va="center",
        )
        ax.text(
            0.56,
            8.80,
            "declared finite objects, toy witnesses, and fail-closed publication gates",
            fontsize=style.font_size("small"),
            color="#eff6ff",
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
            ax.text(x + 0.18, y + height - 0.76, title, fontsize=style.font_size("label"), fontweight="bold", color=color)
            text_top = y + height - 1.08
            for line_idx, line in enumerate(lines):
                ax.text(
                    x + 0.20,
                    text_top - line_idx * 0.35,
                    textwrap.fill(line, width=30),
                    fontsize=style.font_size("dense"),
                    color=ink,
                    va="top",
                )
            if metric is not None:
                ax.add_patch(
                    FancyBboxPatch(
                        (x + width - 1.48, y + 0.14),
                        1.24,
                        0.66,
                        boxstyle="round,pad=0.04,rounding_size=0.07",
                        linewidth=0,
                        facecolor=color,
                        alpha=0.97,
                    )
                )
                ax.text(
                    x + width - 0.86,
                    y + 0.55,
                    metric[0],
                    fontsize=style.font_size("label"),
                    fontweight="bold",
                    color="white",
                    ha="center",
                )
                ax.text(
                    x + width - 0.86,
                    y + 0.27,
                    metric[1],
                    fontsize=style.font_size("dense"),
                    color="white",
                    ha="center",
                )

        evidence_card(
            0.46,
            5.78,
            3.72,
            2.18,
            "Analytical oracle",
            "finite closed form",
            [
                "declared Bernoulli-Ising variational object",
                f"I(lambda) max {_f(_v('ising_mi_saturation'), '.3f')} nats",
                f"MI recompute RMSE {_f(_v('sweep_rmse_mi'), '.1e')}",
            ],
            analytical,
            (_f(_v("free_energy_mean_field_gap_max"), ".2f"), "gap nats"),
        )
        evidence_card(
            0.46,
            0.86,
            3.72,
            2.05,
            "Rollout witness",
            "pymdp + classroom",
            [
                f"cue observed at step {_i(_v('si_tmaze_cue_observed_step'))}",
                f"policy entropy drop {_f(_v('si_tmaze_policy_entropy_drop_after_cue'), '.3f')} nats",
                f"mean reverse KL {_f(classroom_d.get('mean_reverse_kl'), '.2f')}",
            ],
            student,
            (_f(_v("classroom_teacher_cue_validity"), ".2f"), "teacher cue"),
        )
        evidence_card(
            5.82,
            5.78,
            3.72,
            2.18,
            "Finite energy bridge",
            "VFE and EFE",
            [
                "reverse KL read as a VFE term",
                f"prior VFE {_f(vfe_d.get('vfe_complexity_accuracy'), '.2f')} nats",
                f"risk + ambiguity {_f(efe_d.get('efe_risk_ambiguity'), '.2f')}",
            ],
            energy,
            (_f(efe_d.get("efe_risk_ambiguity"), ".2f"), "EFE nats"),
        )
        evidence_card(
            5.82,
            0.86,
            3.72,
            2.05,
            "Lean + gates",
            "fail closed",
            [
                f"{_i(_v('sheaf_track_count'))} tracks; {_i(_v('claim_evidence_audit_count'))} claim rows",
                f"{_i(_v('proof_extraction_theorem_count'))} Lean proofs",
                f"{_i(_v('figure_source_coverage_count'))} source-bound figures",
            ],
            validation,
            (_i(_v("validation_gate_index_count")), "gates"),
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
            "finite correspondence object",
            fontsize=style.font_size("annotation"),
            fontweight="bold",
            color=ink,
            ha="center",
            zorder=3,
        )
        ax.text(
            center_x,
            4.94,
            "reverse KL target",
            fontsize=style.font_size("title") * 0.92,
            fontweight="bold",
            color=analytical,
            ha="center",
            zorder=3,
        )
        ax.text(
            center_x,
            4.58,
            "read as finite VFE",
            fontsize=style.font_size("annotation") * 1.12,
            fontweight="bold",
            color=energy,
            ha="center",
            zorder=3,
        )
        ax.text(center_x, 4.08, "under the declared rollout measure", fontsize=style.font_size("small"), color=muted, ha="center", zorder=3)
        ax.text(center_x, 3.78, "correspondence, not universal identity", fontsize=style.font_size("dense"), color=ink, ha="center", zorder=3)
        ax.add_patch(
            FancyBboxPatch(
                (3.42, 3.26),
                3.16,
                0.34,
                boxstyle="round,pad=0.035,rounding_size=0.06",
                linewidth=0.9,
                edgecolor=teacher,
                facecolor="#fff7ed",
                zorder=3,
            )
        )
        ax.text(
            center_x,
            3.43,
            "Sequential shift: loss "
            f"{_f(sequential_d.get('test_loss_before'), '.2f')} -> "
            f"{_f(sequential_d.get('test_loss_after'), '.2f')}; "
            f"gap {_f(sequential_d.get('gap_closed'), '.2f')}",
            fontsize=style.font_size("dense"),
            color=teacher,
            fontweight="bold",
            ha="center",
            va="center",
            zorder=4,
        )

        loop_nodes = [
            (5.00, 6.64, "T", "teacher model", teacher),
            (6.72, 4.50, "S", "student", student),
            (5.00, 2.46, "R", "own rollouts", analytical),
            (3.28, 4.50, "G", "gates", validation),
        ]
        for x, y, label, body, color in loop_nodes:
            node(x, y, label, body, color)

        arrow_specs = [
            ((5.38, 6.45), (6.42, 4.88), -0.10, teacher),
            ((6.42, 4.12), (5.38, 2.68), -0.10, student),
            ((4.62, 2.68), (3.58, 4.12), -0.10, analytical),
            ((3.58, 4.88), (4.62, 6.45), -0.10, validation),
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
            "generated from repository artifacts; deterministic toy scope only",
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
