"""Registry-backed schematic and dashboard figures."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

from gnn.concordance import BERNOULLI_SYMBOL_MAP
from gnn.parser import parse_gnn_file
from manuscript.sheaf.counts import structural_counts
from ontology.bindings import load_section_ontology
from simulation.pymdp_config import load_pymdp_config
from simulation.tmaze_model import spec_from_config
from .figure_io import save_figure_png
from .figure_helpers import save_styled_figure, styled_figure, style_grid
from .lean_boundary import load_lean_boundary_rows


def _load_invariant_blocks(project_root: Path) -> list[tuple[str, str, bool]]:
    path = project_root / "output" / "reports" / "invariants.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows: list[tuple[str, str, bool]] = []
    for name, passed in sorted((payload.get("invariants") or {}).items()):
        rows.append(("analytical", str(name), bool(passed)))
    for name, passed in sorted((payload.get("simulation") or {}).items()):
        rows.append(("simulation", str(name), bool(passed)))
    return rows


def figure_invariant_dashboard(project_root: Path) -> Path:
    root = project_root.resolve()
    rows = _load_invariant_blocks(root)
    if not rows:
        raise FileNotFoundError("missing invariant rows in output/reports/invariants.json")
    labels = [f"{domain}: {name}" for domain, name, _ in rows]
    values = [1.0 if passed else 0.0 for _, _, passed in rows]
    with styled_figure(root, "invariant_dashboard") as (style, out):
        colors = [style.color("pass") if passed else style.color("fail") for _, _, passed in rows]
        fig_h = max(4.2, 0.36 * len(rows) + 1.5)
        fig, ax = plt.subplots(figsize=(10.4, fig_h))
        y_pos = np.arange(len(rows))
        ax.barh(y_pos, values, color=colors, height=0.65)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=style.font_size("dense"))
        ax.set_xlim(0, 1.15)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["fail", "pass"])
        ax.set_xlabel("Invariant status")
        ax.set_title("Analytical and simulation invariant dashboard")
        for idx, (_, _, passed) in enumerate(rows):
            ax.text(
                1.02,
                idx,
                "PASS" if passed else "FAIL",
                va="center",
                fontsize=style.font_size("dense"),
                color=style.color("primary"),
            )
        style_grid(ax, style)
        ax.grid(axis="x", alpha=0.25)
        save_styled_figure(fig, out, style)
    return out


def figure_tmaze_schematic(project_root: Path) -> Path:
    root = project_root.resolve()
    config = load_pymdp_config(root)
    spec = spec_from_config(config)
    matrices_path = root / "output" / "data" / "si_tmaze_model_matrices.json"
    matrices = json.loads(matrices_path.read_text(encoding="utf-8")) if matrices_path.is_file() else {}
    matrix_summary = ""
    if matrices.get("A_shapes") and matrices.get("B_shapes"):
        matrix_summary = f"A factors={len(matrices['A_shapes'])}; B factors={len(matrices['B_shapes'])}; C/D priors audited"
    with styled_figure(root, "tmaze_schematic") as (style, out):
        fig, ax = plt.subplots(figsize=(10.2, 6.4))
        ax.set_xlim(-2.15, 2.15)
        ax.set_ylim(-2.25, 1.88)
        ax.axis("off")
        positions = {
            "cue": (0.0, -1.0),
            "center": (0.0, -0.1),
            "middle": (0.0, 0.65),
            "left": (-1.0, 1.15),
            "right": (1.0, 1.15),
        }
        edges = [("center", "cue"), ("center", "middle"), ("middle", "left"), ("middle", "right")]
        for source, target in edges:
            arrow = FancyArrowPatch(
                positions[source],
                positions[target],
                arrowstyle="<->",
                mutation_scale=10,
                linewidth=1.8,
                color=style.color("primary"),
                alpha=0.75,
            )
            ax.add_patch(arrow)
        node_rows = (
            ("center", "center\nstart", style.color("secondary")),
            ("cue", "cue\nvalidity 0.95", "#7c3aed"),
            ("middle", "middle\njunction", style.color("muted")),
            ("left", "left arm\nreward if condition=0", style.color("accent")),
            ("right", "right arm\npunishment", style.color("fail")),
        )
        for key, label, color in node_rows:
            center = positions[key]
            box = FancyBboxPatch(
                (center[0] - 0.46, center[1] - 0.22),
                0.92,
                0.44,
                boxstyle="round,pad=0.04",
                linewidth=1.4,
                edgecolor=color,
                facecolor="white",
            )
            ax.add_patch(box)
            ax.text(center[0], center[1], label, ha="center", va="center", fontsize=style.font_size("dense"))
        for x, y, label in (
            (-1.92, -1.98, f"profile={spec.profile}"),
            (-1.92, -1.78, "3 obs modalities: location, outcome, cue"),
            (
                -1.92,
                -1.58,
                f"{spec.num_location_states} locations/actions; "
                f"{spec.num_reward_location_states} reward-location states",
            ),
            (-1.92, -1.38, f"SI agent policy_len={spec.policy_len}; search horizon={spec.planning_horizon}"),
            (-1.92, -1.18, matrix_summary),
        ):
            if label:
                ax.text(x, y, label, ha="left", va="center", fontsize=style.font_size("dense"), color=style.color("primary"))
        ax.text(
            1.92,
            -1.98,
            "Source: pymdp.yaml + si_tmaze_model_matrices.json",
            ha="right",
            va="center",
            fontsize=style.font_size("source"),
            color=style.color("muted"),
        )
        ax.set_title("T-maze model: cue action resolves hidden reward location")
        save_styled_figure(fig, out, style)
    return out


def _load_pipeline_track_labels(project_root: Path) -> list[str]:
    path = project_root / "tracks.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    tracks = raw.get("tracks") or []
    return [str(track.get("label") or track.get("id")) for track in tracks if track.get("required", True)]


def _load_sheaf_track_labels(project_root: Path) -> list[str]:
    path = project_root / "manuscript" / "sheaf" / "tracks.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    tracks = raw.get("tracks") or {}
    ordered = sorted(tracks.items(), key=lambda item: int((item[1] or {}).get("order", 0)))
    return [str((meta or {}).get("label") or track_id) for track_id, meta in ordered]


def figure_multi_track_architecture(project_root: Path) -> Path:
    root = project_root.resolve()
    counts = structural_counts(root)
    variables_path = root / "output" / "data" / "manuscript_variables.json"
    variables = json.loads(variables_path.read_text(encoding="utf-8")) if variables_path.is_file() else {}

    def _fmt(key: str, default: object = "--", fmt: str = "{}") -> str:
        value = variables.get(key, default)
        try:
            return fmt.format(float(value))
        except (TypeError, ValueError):
            return str(value)

    with styled_figure(root, "multi_track_architecture") as (style, out):
        fig, ax = plt.subplots(figsize=(16.2, 9.2))
        ax.set_xlim(0, 14)
        ax.set_ylim(0, 8)
        ax.axis("off")

        ax.text(
            0.25,
            7.62,
            "Evidence architecture: artifacts -> variables -> manuscript claims",
            fontsize=style.font_size("title"),
            fontweight="bold",
            color=style.color("primary"),
            va="center",
        )
        ax.text(
            0.27,
            7.28,
            (
                f"{counts['imrad_manifest_rows']} manifest rows | "
                f"{counts['coverage_present']}/{counts['coverage_bound']} bound cells | "
                f"{counts['sheaf_track_count']} fragment types"
            ),
            ha="left",
            va="center",
            fontsize=style.font_size("source"),
            color=style.color("muted"),
        )

        headers = [
            (0.25, "scientific lane"),
            (2.75, "source artifacts"),
            (5.55, "auto-injected variables"),
            (8.35, "validation gates"),
            (11.05, "reader-facing output"),
        ]
        widths = [2.15, 2.45, 2.45, 2.35, 2.65]
        for (x, title), width in zip(headers, widths, strict=True):
            ax.text(x + width / 2, 6.8, title, ha="center", fontsize=style.font_size("small"), fontweight="bold")

        lanes = [
            {
                "name": "Analytical\nBernoulli-Ising",
                "color": style.color("secondary"),
                "sources": ["parameter_sweep.csv", "decomposition.py", "energy_demo.json"],
                "variables": [
                    f"Imax {_fmt('ising_mi_saturation', fmt='{:.3f}')} nats",
                    f"mean-field gap {_fmt('free_energy_mean_field_gap_max', fmt='{:.3f}')}",
                    f"exact |F| {_fmt('free_energy_exact_target_max_abs', fmt='{:.1e}')}",
                ],
                "gates": [
                    f"MI residual {_fmt('sweep_max_residual', fmt='{:.1e}')}",
                    f"gap=MI delta {_fmt('free_energy_gap_equals_mi_max_abs', fmt='{:.1e}')}",
                    "decomposition identity",
                ],
                "outputs": ["MI sweep", "free-energy gap", "energy decomposition"],
            },
            {
                "name": "On-policy\npymdp T-maze",
                "color": style.color("accent"),
                "sources": ["si_tmaze_summary.json", "si_tmaze_trace.json", "pymdp.yaml"],
                "variables": [
                    f"H={variables.get('si_tmaze_planning_horizon', '--')}, steps={variables.get('si_tmaze_steps', '--')}",
                    f"cue step {variables.get('si_tmaze_cue_observed_step', '--')}",
                    f"policy entropy drop {_fmt('si_tmaze_policy_entropy_drop_after_cue', fmt='{:.3f}')}",
                ],
                "gates": ["SI schema", "runtime diagnostics", "simulation invariants"],
                "outputs": ["belief entropy", "obs/action trace", "q_pi action marginals"],
            },
            {
                "name": "Formal + sheaf\npublication spine",
                "color": style.color("pass"),
                "sources": ["proof_extraction_index.json", "figure_source_map.json", "tracks.yaml"],
                "variables": [
                    f"{variables.get('proof_extraction_theorem_count', '--')} Lean theorem rows",
                    f"{variables.get('sheaf_laws_verified', '--')}/{variables.get('sheaf_law_count', '--')} sheaf laws",
                    f"{variables.get('figure_source_coverage_count', '--')} figures source-mapped",
                ],
                "gates": ["lake build", "strict compose", "render + output checks"],
                "outputs": ["Lean boundary", "semantic gluing graph", "supplements"],
            },
        ]

        def draw_box(x: float, y: float, width: float, height: float, lines: list[str], color: str) -> None:
            patch = FancyBboxPatch(
                (x, y),
                width,
                height,
                boxstyle="round,pad=0.04",
                linewidth=1.1,
                edgecolor=color,
                facecolor="#f8fafc",
            )
            ax.add_patch(patch)
            text = "\n".join(textwrap.fill(line, width=max(18, int(width * 13)), break_long_words=False) for line in lines)
            ax.text(x + 0.12, y + height - 0.22, text, ha="left", va="top", fontsize=style.font_size("dense"), color=style.color("primary"))

        row_y = [5.25, 3.62, 1.99]
        row_h = 1.14
        x_positions = [0.25, 2.75, 5.55, 8.35, 11.05]
        for lane, y in zip(lanes, row_y, strict=True):
            color = str(lane["color"])
            ax.add_patch(
                FancyBboxPatch(
                    (x_positions[0], y),
                    widths[0],
                    row_h,
                    boxstyle="round,pad=0.05",
                    linewidth=1.4,
                    edgecolor=color,
                    facecolor="#ffffff",
                )
            )
            ax.text(
                x_positions[0] + 0.15,
                y + row_h - 0.24,
                str(lane["name"]),
                ha="left",
                va="top",
                fontsize=style.font_size("dense"),
                fontweight="bold",
                color=color,
            )
            for col_idx, key in enumerate(("sources", "variables", "gates", "outputs"), start=1):
                draw_box(
                    x_positions[col_idx],
                    y,
                    widths[col_idx],
                    row_h,
                    list(lane[key]),  # type: ignore[index]
                    color,
                )
            for col_idx in range(4):
                ax.annotate(
                    "",
                    xy=(x_positions[col_idx + 1] - 0.08, y + row_h / 2),
                    xytext=(x_positions[col_idx] + widths[col_idx] + 0.08, y + row_h / 2),
                    arrowprops={"arrowstyle": "-|>", "color": style.color("muted"), "lw": 1.0},
                )

        spine = ["analysis", "figures", "formal", "claims", "render", "release"]
        ax.text(0.45, 1.04, "deterministic publication spine", fontsize=style.font_size("dense"), fontweight="bold")
        for idx, label in enumerate(spine):
            x = 0.45 + idx * 1.08
            box = FancyBboxPatch(
                (x, 0.44),
                0.92,
                0.34,
                boxstyle="round,pad=0.035",
                linewidth=0.9,
                edgecolor=style.color("pass"),
                facecolor="#ecfdf5",
            )
            ax.add_patch(box)
            ax.text(x + 0.46, 0.61, label, fontsize=style.font_size("dense"), ha="center", va="center")
            if idx < len(spine) - 1:
                ax.annotate(
                    "",
                    xy=(x + 1.04, 0.61),
                    xytext=(x + 0.94, 0.61),
                    arrowprops=dict(arrowstyle="->", color=style.color("muted"), lw=0.8),
                )
        ax.text(
            13.35,
            0.61,
            (
                f"metadata: {variables.get('token_provenance_count', '--')} injected tokens | "
                f"{variables.get('validation_gate_index_count', '--')} gates | "
                f"{variables.get('hardcoded_variable_issue_count', '--')} hard-coded value issues"
            ),
            ha="right",
            fontsize=style.font_size("source"),
            color=style.color("muted"),
        )
        save_figure_png(fig, out, dpi=style.dpi, facecolor="white", transparent=style.transparent)
    return out


def figure_lean_boundary_status(project_root: Path) -> Path:
    root = project_root.resolve()
    rows = load_lean_boundary_rows(root)
    if not rows:
        raise FileNotFoundError("no Lean boundary modules under lean/OnPolicyDistillation/")

    def _wrap_snake(value: str, *, width: int) -> str:
        words = value.split("_")
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current}_{word}" if current else word
            if len(candidate) <= width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return "\n".join(lines)

    table_data = [
        [
            "\n".join(
                textwrap.wrap(
                    row.module.replace("OnPolicyDistillation.", "OPD."),
                    width=28,
                    break_long_words=False,
                )
            ),
            row.kind,
            _wrap_snake(row.name, width=30),
            row.status,
        ]
        for row in rows
    ]
    with styled_figure(root, "lean_boundary_status") as (style, out):
        fig_h = max(3.8, 0.56 * len(rows) + 1.4)
        fig, ax = plt.subplots(figsize=(11.8, fig_h))
        ax.axis("off")
        table = ax.table(
            cellText=table_data,
            colLabels=["Module", "Kind", "Name", "Status"],
            bbox=[0.0, 0.02, 1.0, 0.88],
            cellLoc="left",
            colWidths=[0.25, 0.12, 0.48, 0.15],
        )
        table.auto_set_font_size(False)
        table.set_fontsize(style.font_size("table"))
        table.scale(1, 1.85)
        for (row_idx, col_idx), cell in table.get_celld().items():
            if row_idx == 0:
                cell.set_facecolor(style.color("header_bg"))
                continue
            if col_idx == 3:
                status = table_data[row_idx - 1][3]
                cell.set_facecolor(style.color("proved") if status == "proved" else style.color("sorry"))
        ax.set_title("Lean formalization boundary status", pad=12)
        save_styled_figure(fig, out, style)
    return out


def figure_gnn_ontology_concordance(project_root: Path) -> Path:
    root = project_root.resolve()
    gnn_path = root / "gnn" / "bernoulli_toy.gnn.md"
    ontology_path = root / "manuscript" / "sections" / "imrad" / "methods_analytical" / "ontology.yaml"
    model = parse_gnn_file(gnn_path)
    section_ontology = load_section_ontology(ontology_path)
    pairs: list[tuple[str, str, str]] = []
    for symbol, var in BERNOULLI_SYMBOL_MAP.items():
        if var not in model.variables:
            continue
        onto = model.ontology.get(var) or section_ontology.get(var, "—")
        pairs.append((symbol, var, onto))
    if not pairs:
        raise ValueError("no GNN ↔ ontology pairs to plot")
    with styled_figure(root, "gnn_ontology_concordance") as (style, out):
        fig_h = max(4.0, 0.56 * len(pairs) + 1.2)
        fig, ax = plt.subplots(figsize=(10.8, fig_h))
        ax.set_xlim(0, 10)
        ax.set_ylim(-0.5, len(pairs))
        ax.axis("off")
        ax.text(1.2, len(pairs) - 0.1, "Analytical symbol", fontweight="bold", fontsize=style.font_size("dense"))
        ax.text(4.0, len(pairs) - 0.1, "GNN variable", fontweight="bold", fontsize=style.font_size("dense"))
        ax.text(7.0, len(pairs) - 0.1, "Ontology term", fontweight="bold", fontsize=style.font_size("dense"))
        for idx, (symbol, var, onto) in enumerate(pairs):
            y = len(pairs) - idx - 1
            ax.text(1.2, y, symbol, fontsize=style.font_size("dense"), va="center")
            ax.text(4.0, y, var, fontsize=style.font_size("dense"), va="center", color=style.color("secondary"))
            ax.text(7.0, y, onto, fontsize=style.font_size("dense"), va="center", color=style.color("accent"))
            ax.annotate(
                "",
                xy=(3.6, y),
                xytext=(2.0, y),
                arrowprops=dict(arrowstyle="->", color=style.color("grid")),
            )
            ax.annotate(
                "",
                xy=(6.6, y),
                xytext=(4.8, y),
                arrowprops=dict(arrowstyle="->", color=style.color("grid")),
            )
        ax.text(
            0.02,
            0.04,
            "Each row is a resolved symbol -> model variable -> ontology term binding.",
            transform=ax.transAxes,
            fontsize=style.font_size("source"),
            color=style.color("muted"),
        )
        ax.set_title(f"GNN -> ontology concordance ({model.version})")
        save_styled_figure(fig, out, style)
    return out
