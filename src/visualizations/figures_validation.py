"""Validation/scholarship figures (gluing graph, traceability, ablation, source map)."""

from __future__ import annotations

import json
import textwrap
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .figure_helpers import save_styled_figure, style_grid, subset_note
from .figure_io import save_figure_png
from .figure_registry import figure_output_path
from .figure_style import apply_style, load_figure_style


def _wrap_label(text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(str(text), width=width, break_long_words=False)) or str(text)


def _compact_list_label(values: list[str], *, width: int, max_items: int, more_word: str) -> str:
    cleaned = [str(value).strip() for value in values if str(value).strip()]
    shown = [_wrap_label(value, width) for value in cleaned[:max_items]]
    if len(cleaned) > max_items:
        shown.append(f"+{len(cleaned) - max_items} more {more_word}")
    return "\n".join(shown) or "validate_outputs"


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
        fig, ax = plt.subplots(figsize=(14.7, 11.4))
        ax.axis("off")
        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(0.0, 1.0)
        producer_x, artifact_x, consumer_x = 0.05, 0.40, 0.74
        fig.text(
            0.05,
            0.965,
            "Every generated claim flows through a producer, artifact, and checked binding",
            fontsize=style.font_size("title"),
            color=style.color("primary"),
            ha="left",
            va="top",
        )
        header_y = 0.89
        y_positions = np.linspace(0.80, 0.10, len(selected))
        ax.text(
            producer_x,
            header_y,
            "Producer script",
            weight="bold",
            color=style.color("primary"),
            fontsize=style.font_size("annotation"),
        )
        ax.text(
            artifact_x,
            header_y,
            "Evidence artifact",
            weight="bold",
            color=style.color("primary"),
            fontsize=style.font_size("annotation"),
        )
        ax.text(
            consumer_x,
            header_y,
            "Compact consumers / gates",
            weight="bold",
            color=style.color("primary"),
            fontsize=style.font_size("annotation"),
        )
        for y, rel in zip(y_positions, selected, strict=True):
            record = artifacts.get(rel, {})
            producer = str(record.get("producer", "?"))
            consumer_values = record.get("consumers") or record.get("validation_gates") or ["validate_outputs"]
            consumers = _compact_list_label(consumer_values, width=30, max_items=2, more_word="bindings")
            ok = bool(record.get("produced_by_configured_analysis"))
            box_color = style.color("pass") if ok else style.color("fail")
            band_alpha = 0.055 if selected.index(rel) % 2 == 0 else 0.0
            ax.axhspan(y - 0.028, y + 0.028, xmin=0.025, xmax=0.97, color=style.color("muted"), alpha=band_alpha, lw=0)
            ax.text(
                producer_x,
                y,
                _wrap_label(producer, 25),
                fontsize=style.font_size("dense"),
                va="center",
                linespacing=1.12,
                bbox=dict(boxstyle="round,pad=0.24", facecolor="#f8fafc", edgecolor=box_color),
            )
            ax.text(
                artifact_x,
                y,
                _wrap_label(rel.replace("output/", ""), 35),
                fontsize=style.font_size("dense"),
                va="center",
                linespacing=1.12,
                bbox=dict(boxstyle="round,pad=0.24", facecolor="#ffffff", edgecolor=style.color("secondary")),
            )
            ax.text(
                consumer_x,
                y,
                consumers,
                fontsize=style.font_size("dense"),
                va="center",
                linespacing=1.10,
                bbox=dict(boxstyle="round,pad=0.24", facecolor="#f8fafc", edgecolor=style.color("accent")),
            )
            arrow = {"arrowstyle": "->", "linewidth": 0.9, "color": style.color("muted"), "alpha": 0.82}
            ax.annotate("", xy=(artifact_x - 0.025, y), xytext=(producer_x + 0.255, y), arrowprops=arrow)
            ax.annotate("", xy=(consumer_x - 0.025, y), xytext=(artifact_x + 0.285, y), arrowprops=arrow)
        fig.text(
            0.05,
            0.035,
            "Long consumer lists are compacted with +N counts; bindings remain sourced from validation_dependency_graph.json.",
            fontsize=style.font_size("source"),
            color=style.color("muted"),
        )
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
        # Anchor the color scale at zero: stretching a narrow effect range over
        # the full colormap exaggerates small differences into maximal contrast.
        image = ax.imshow(matrix, cmap="viridis", aspect="auto", vmin=0.0)
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
        subset_note(fig, matrix.size, len(rows), "source rows (cells are max-aggregated)")
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
