import re
from pathlib import Path

import matplotlib.pyplot as plt
import pytest
from PIL import Image

from visualizations.figure_io import save_figure_png
from visualizations.figure_registry import (
    load_figure_registry,
    load_section_figures,
    render_figure_markdown,
    render_section_figures,
)
from visualizations.figure_style import apply_style, load_figure_style


def test_load_figure_style_defaults() -> None:
    root = Path(__file__).resolve().parents[1]
    style = load_figure_style(root)
    assert style.dpi == 160
    assert style.font_scale == 1.5
    assert style.color("primary") == "#111827"


def test_figure_style_named_font_roles_are_readable() -> None:
    root = Path(__file__).resolve().parents[1]
    style = load_figure_style(root)
    assert style.base_font_size == 15.0
    assert style.font_size("title") > style.font_size("label")
    assert style.font_size("label") >= 15.0
    assert style.font_size("legend") >= 12.0
    assert style.font_size("annotation") >= 11.0
    assert style.font_size("source") >= 10.0
    assert style.font_size("table") >= 10.0
    assert style.font_size("dense") >= 9.5


def test_visualization_modules_do_not_reintroduce_tiny_literal_fonts() -> None:
    root = Path(__file__).resolve().parents[1]
    visual_modules = [
        root / "src" / "visualizations" / "figures.py",
        root / "src" / "visualizations" / "figures_diagrams.py",
        root / "src" / "visualizations" / "figures_sheaf.py",
        root / "src" / "visualizations" / "figures_sheaf_draw.py",
    ]
    patterns = [
        re.compile(r"fontsize\s*=\s*([0-9]+(?:\.[0-9]+)?)"),
        re.compile(r"\.set_fontsize\(\s*([0-9]+(?:\.[0-9]+)?)\s*\)"),
    ]
    offenders: list[str] = []
    for module in visual_modules:
        text = module.read_text(encoding="utf-8")
        for pattern in patterns:
            for match in pattern.finditer(text):
                value = float(match.group(1))
                if value < 9.5:
                    line = text[: match.start()].count("\n") + 1
                    offenders.append(f"{module.relative_to(root)}:{line}: fontsize {value}")
    assert not offenders, "tiny literal font sizes must use FigureStyleConfig.font_size roles: " + ", ".join(offenders)


def test_figure_yaml_has_no_duplicate_figure_metadata_keys() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "figures.yaml").read_text(encoding="utf-8")
    current_id: str | None = None
    seen: dict[str, set[str]] = {}
    duplicate_keys: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if match := re.match(r"^  ([a-zA-Z0-9_]+):\s*$", line):
            current_id = match.group(1)
            seen.setdefault(current_id, set())
            continue
        if current_id and (match := re.match(r"^    ([a-zA-Z0-9_]+):", line)):
            key = match.group(1)
            if key in seen[current_id]:
                duplicate_keys.append(f"{current_id}.{key}:{line_number}")
            seen[current_id].add(key)
    assert not duplicate_keys, f"duplicate figure metadata keys: {duplicate_keys}"


def test_apply_style_restores_active() -> None:
    root = Path(__file__).resolve().parents[1]
    style = load_figure_style(root)
    from visualizations.figure_style import active_style

    before = active_style()
    with apply_style(style):
        assert active_style() is style
    assert active_style() is before


def test_save_figure_png_normalizes_rgb_atomically(tmp_path: Path) -> None:
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])

    out = tmp_path / "figures" / "line.png"
    assert save_figure_png(fig, out, dpi=72) == out

    with Image.open(out) as img:
        assert img.mode == "RGB"
        assert img.size[0] > 0
        assert img.size[1] > 0
    assert not list(out.parent.glob(".line.*.png"))


def test_save_figure_png_can_skip_rgb_normalization(tmp_path: Path) -> None:
    fig, ax = plt.subplots()
    ax.scatter([0, 1], [1, 0])

    out = tmp_path / "transparent.png"
    assert save_figure_png(fig, out, dpi=72, transparent=True, normalize_rgb=False) == out

    with Image.open(out) as img:
        assert img.mode in {"RGBA", "LA", "P"}


def test_figure_registry_and_markdown() -> None:
    root = Path(__file__).resolve().parents[1]
    registry = load_figure_registry(root)
    assert "ising_mi_curve" in registry
    assert len(registry["ising_mi_curve"].alt) >= 80
    md = render_figure_markdown(root, "ising_mi_curve", figure_number=1)
    # pandoc-crossref owns numbering: a single label, the caption in the alt slot, no hand number.
    assert "Figure 1." not in md
    assert "*Figure" not in md
    assert "../output/figures/ising_mi_curve.png" in md
    assert md.count("{#fig:ising_mi_curve") == 1
    assert "closed-form" in md


def test_render_section_figures_for_results_mi_sweep() -> None:
    root = Path(__file__).resolve().parents[1]

    md = render_section_figures(root, "results_mi_sweep")
    assert "ising_mi_curve.png" in md
    # The MI sweep is the canonical results figure, not an unnumbered methods repeat.
    assert "{#fig:ising_mi_curve" in md
    assert "Figure 2 (results)." not in md
    assert "Reproduced from [@fig:ising_mi_curve]" not in md
    assert len(md.split("\n\n")) == 1


def test_appendix_does_not_repeat_mi_sweep_figure() -> None:
    root = Path(__file__).resolve().parents[1]
    appendix_refs = load_section_figures(root).get("appendix_full_sheaf", ())
    assert all(ref.figure_id != "ising_mi_curve" for ref in appendix_refs)


def test_render_figure_markdown_unlabeled_repeat() -> None:
    """A reused figure is a cross-reference, not a duplicated page-scale image."""
    root = Path(__file__).resolve().parents[1]
    md = render_figure_markdown(root, "ising_mi_curve", labeled=False)
    assert "{#fig:ising_mi_curve" not in md
    assert "![" not in md  # no second rendering of the image
    assert "[@fig:ising_mi_curve]" in md  # points at the canonical occurrence


def test_render_figure_markdown_pandoc_owns_numbering() -> None:
    """A labeled figure emits exactly one pandoc-crossref label and NO hand-written number.

    Regression guard for the triple-numbering defect: render_figure_markdown must not emit
    any ``Figure N`` / ``*Figure ...*`` hand label even when a legacy caption_prefix/number
    is passed; pandoc-crossref is the single source of figure numbers.
    """
    root = Path(__file__).resolve().parents[1]
    md = render_figure_markdown(
        root,
        "sheaf_layers_overview",
        figure_number=6,
        caption_prefix="Figure 6 (methods). ",
    )
    assert "{#fig:sheaf_layers_overview" in md
    assert md.count("#fig:sheaf_layers_overview") == 1
    assert "Figure 6" not in md
    assert "*Figure" not in md
    # The clean caption rides the image alt slot so pandoc numbers it once.
    assert "Sheaf layers overview" in md


@pytest.mark.render_slow
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_no_orphan_hand_figure_labels_in_composed_manuscript() -> None:
    """No composed section may carry a hand-written ``*Figure N ...*`` caption line.

    Render-aware guard (not source-blind): pandoc-crossref numbers figures, so a leftover
    italic ``*Figure ...*`` line means a double-number regression slipped back in.
    """
    import re as _re

    from manuscript.sheaf import compose_all_sections

    root = Path(__file__).resolve().parents[1]
    compose_all_sections(root)
    offenders = []
    for md in sorted((root / "manuscript").glob("[0-9][0-9]_*.md")):
        text = md.read_text(encoding="utf-8")
        assert "Reproduced from [@fig:ising_mi_curve]" not in text
        for i, line in enumerate(text.splitlines(), 1):
            if _re.match(r"\*Figure\s+[0-9IMA]", line.strip()):
                offenders.append(f"{md.name}:{i}:{line.strip()[:50]}")
    assert not offenders, f"orphan hand Figure labels: {offenders}"


@pytest.mark.render_slow
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_model_surface_map_clarifies_no_gridworld_claim() -> None:
    from manuscript.sheaf import compose_all_sections

    root = Path(__file__).resolve().parents[1]
    compose_all_sections(root)
    text = "\n".join(
        [
            (root / "manuscript" / "02_intro_motivation.md").read_text(encoding="utf-8"),
            (root / "manuscript" / "17_conclusion.md").read_text(encoding="utf-8"),
        ]
    )
    for phrase in (
        "Bernoulli-Ising",
        "pymdp T-maze",
        "Classroom",
        "Graph-world",
        "No gridworld result is reported or claimed",
    ):
        assert phrase in text


def test_subset_note_stamps_only_filtered_views() -> None:
    """Filtered figures must say so in pixels; full views get no stamp."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from visualizations.figure_helpers import subset_note

    fig = plt.figure()
    subset_note(fig, 13, 33, "tracks")
    stamped = [t.get_text() for t in fig.texts]
    assert any("showing 13 of 33 tracks" in t for t in stamped)
    plt.close(fig)

    fig = plt.figure()
    subset_note(fig, 33, 33, "tracks")
    assert not fig.texts  # no-op when nothing was dropped
    plt.close(fig)
