"""Tests for the self-contained canonical PDF renderer's pure helpers.

The full render shells out to pandoc/xelatex (covered by manual/CI runs, too slow for
the unit timeout); here we bind the project-owned typography-source parsing so the
standalone renderer reads margins and font from the same files the manuscript declares.

The pure helper functions (extract_preamble, geometry_string) live in
``src/manuscript/render_helpers.py`` — tested directly here so the suite has a clean
import path without exec_module gymnastics on the script.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Add project src to path so manuscript.render_helpers resolves stand-alone.
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from manuscript.render_helpers import extract_preamble, geometry_string  # noqa: E402
from manuscript import pdf_render  # noqa: E402
from manuscript.pdf_render import _tex_escape, build_cover_tex  # noqa: E402


def test_extract_preamble_reads_fenced_latex(tmp_path: Path) -> None:
    f = tmp_path / "preamble.md"
    f.write_text("intro\n```latex\n\\changefontsize[11pt]{9pt}\n```\n", encoding="utf-8")
    assert "\\changefontsize[11pt]{9pt}" in extract_preamble(f)


def test_extract_preamble_missing_returns_empty(tmp_path: Path) -> None:
    assert extract_preamble(tmp_path / "nope.md") == ""


def test_geometry_from_config(tmp_path: Path) -> None:
    f = tmp_path / "config.yaml"
    f.write_text("metadata:\n  geometry: margin=0.5in\n", encoding="utf-8")
    assert geometry_string(f) == "margin=0.5in"


def test_geometry_default_when_absent(tmp_path: Path) -> None:
    f = tmp_path / "config.yaml"
    f.write_text("metadata:\n  license: MIT\n", encoding="utf-8")
    assert geometry_string(f) == "margin=0.5in"


def test_render_pdf_imports_no_infrastructure() -> None:
    """The renderer script must not import the monorepo infrastructure."""
    script = (PROJECT_ROOT / "scripts" / "render_pdf.py").read_text(encoding="utf-8")
    module = (PROJECT_ROOT / "src" / "manuscript" / "pdf_render.py").read_text(encoding="utf-8")
    assert "import infrastructure" not in script
    assert "from infrastructure" not in script
    assert "import infrastructure" not in module
    assert "from infrastructure" not in module


def test_cover_image_dimensions_are_config_driven() -> None:
    """The title-page graphical abstract uses config width/max_height, not hard-coded sizing."""
    src = (PROJECT_ROOT / "src" / "manuscript" / "pdf_render.py").read_text(encoding="utf-8")
    assert "front.get(\"width\")" in src
    assert "front.get(\"max_height\")" in src
    assert "width={abstract_width},height={abstract_max_height}" in src
    assert "0.52\\textheight" not in src
    config = yaml.safe_load((PROJECT_ROOT / "manuscript" / "config.yaml").read_text(encoding="utf-8"))
    front = config["front_matter"]["graphical_abstract"]
    assert front["max_height"] == r"0.58\textheight"


def test_render_pdf_script_is_thin_facade() -> None:
    src = (PROJECT_ROOT / "scripts" / "render_pdf.py").read_text(encoding="utf-8")
    assert "from manuscript.pdf_render import" in src
    assert "def build_cover_tex" not in src
    assert "subprocess.run" not in src


def test_render_helpers_imports_no_infrastructure() -> None:
    """render_helpers.py is self-contained — no monorepo infrastructure import."""
    src = (PROJECT_ROOT / "src" / "manuscript" / "render_helpers.py").read_text(encoding="utf-8")
    assert "import infrastructure" not in src
    assert "from infrastructure" not in src


def test_tex_escape_covers_latex_specials() -> None:
    escaped = _tex_escape("A&B%$#_{}~\\")
    assert escaped == r"A\&B\%\$\#\_\{\}\textasciitilde{}\textbackslash\{\}"


def test_build_cover_tex_uses_metadata_authors_and_graphical_abstract(tmp_path: Path) -> None:
    image = tmp_path / "output" / "figures" / "graphical_abstract.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"png")
    config = {
        "paper": {
            "title": "A&B Study",
            "subtitle": "Active_Inference",
            "version": "1.2",
            "date": "2026-06-08",
        },
        "authors": [
            {
                "name": "Ada_Lovelace",
                "affiliation": "Lab & Field",
                "email": "ada@example.test",
                "orcid": "0000-0000",
            }
        ],
        "front_matter": {
            "graphical_abstract": {
                "enabled": True,
                "caption": "Caption_with_%_sign",
                "width": r"0.8\textwidth",
                "max_height": r"0.3\textheight",
            }
        },
    }

    tex = build_cover_tex(config, tmp_path)

    assert r"A\&B Study" in tex
    assert r"Active\_Inference" in tex
    assert r"Ada\_Lovelace" in tex
    assert r"Lab \& Field" in tex
    assert r"\texttt{ada@example.test}" in tex
    assert "ORCID:~0000-0000" in tex
    assert f"{{{image}}}" in tex
    assert r"width=0.8\textwidth,height=0.3\textheight" in tex
    assert r"Caption\_with\_\%\_sign" in tex


def test_build_cover_tex_omits_graphical_abstract_when_missing(tmp_path: Path) -> None:
    tex = build_cover_tex({"front_matter": {"graphical_abstract": {"enabled": True}}}, tmp_path)
    assert r"\includegraphics" not in tex


def test_render_pdf_returns_two_when_tools_missing(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setattr(pdf_render.shutil, "which", lambda tool: None)
    assert pdf_render.render_pdf(tmp_path) == 2
    assert "`pandoc` not found" in capsys.readouterr().err


def _prepare_pdf_project(tmp_path: Path) -> Path:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "config.yaml").write_text(
        "metadata:\n  geometry: margin=0.6in\npaper:\n  title: Test PDF\n", encoding="utf-8"
    )
    (manuscript / "preamble.md").write_text("```latex\n\\usepackage{xcolor}\n```\n", encoding="utf-8")
    (manuscript / "references.bib").write_text("@article{x, title={X}}\n", encoding="utf-8")
    resolved = tmp_path / "output" / "manuscript"
    resolved.mkdir(parents=True)
    (resolved / "00_00_sheaf_coverage.md").write_text("coverage", encoding="utf-8")
    (resolved / "01_main.md").write_text("main", encoding="utf-8")
    return resolved


def test_render_pdf_builds_pandoc_command_without_shelling_out(monkeypatch, tmp_path: Path) -> None:
    resolved = _prepare_pdf_project(tmp_path)
    calls: dict[str, object] = {}

    import manuscript.hydrate
    import manuscript.sheaf
    import manuscript.variables

    monkeypatch.setattr(pdf_render.shutil, "which", lambda tool: f"/bin/{tool}")
    monkeypatch.setattr(manuscript.sheaf, "compose_all_sections", lambda *args, **kwargs: None)
    monkeypatch.setattr(manuscript.variables, "generate_variables", lambda *args, **kwargs: {"x": 1})
    monkeypatch.setattr(manuscript.hydrate, "write_resolved_manuscript", lambda *args, **kwargs: resolved)

    def fake_run(cmd: list[str], cwd: Path) -> SimpleNamespace:
        calls["cmd"] = cmd
        calls["cwd"] = cwd
        pdf_out = Path(cmd[cmd.index("-o") + 1])
        pdf_out.write_bytes(b"%PDF")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(pdf_render.subprocess, "run", fake_run)

    assert pdf_render.render_pdf(tmp_path) == 0
    cmd = calls["cmd"]
    assert isinstance(cmd, list)
    assert Path(cmd[1]).name == "_combined_manuscript.md"
    assert "--pdf-engine=xelatex" in cmd
    assert "--filter" in cmd
    assert "/bin/pandoc-crossref" in cmd
    assert "--citeproc" in cmd
    assert "--bibliography" in cmd
    assert "geometry:margin=0.6in" in cmd
    assert calls["cwd"] == tmp_path.resolve()
    combined = tmp_path / "output" / "pdf" / "_combined_manuscript.md"
    legacy = tmp_path / "output" / "pdf" / "_standalone_combined.md"
    assert combined.read_text(encoding="utf-8") == "main\n\ncoverage"
    assert legacy.read_text(encoding="utf-8") == combined.read_text(encoding="utf-8")


def test_render_pdf_returns_pandoc_failure(monkeypatch, tmp_path: Path, capsys) -> None:
    resolved = _prepare_pdf_project(tmp_path)

    import manuscript.hydrate
    import manuscript.sheaf
    import manuscript.variables

    monkeypatch.setattr(pdf_render.shutil, "which", lambda tool: f"/bin/{tool}")
    monkeypatch.setattr(manuscript.sheaf, "compose_all_sections", lambda *args, **kwargs: None)
    monkeypatch.setattr(manuscript.variables, "generate_variables", lambda *args, **kwargs: {})
    monkeypatch.setattr(manuscript.hydrate, "write_resolved_manuscript", lambda *args, **kwargs: resolved)
    monkeypatch.setattr(pdf_render.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=7))

    assert pdf_render.render_pdf(tmp_path) == 7
    assert "pandoc render failed" in capsys.readouterr().err
