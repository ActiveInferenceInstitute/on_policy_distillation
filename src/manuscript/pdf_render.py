"""Canonical PDF rendering helpers.

The public script delegates here so cover-page construction and command
assembly are testable source code, while the script name remains stable.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from manuscript.render_helpers import extract_preamble, geometry_string


def _tex_escape(text: str) -> str:
    """Escape the LaTeX special characters that occur in metadata strings."""
    for char, repl in (
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
    ):
        text = text.replace(char, repl)
    return text


def build_cover_tex(config: dict, project_root: Path) -> str:
    """Build a standalone title page: title, subtitle, author block, graphical abstract."""
    paper = config.get("paper") or {}
    title = _tex_escape(str(paper.get("title") or "Manuscript"))
    subtitle = _tex_escape(str(paper.get("subtitle") or ""))
    version = _tex_escape(str(paper.get("version") or ""))
    date = _tex_escape(str(paper.get("date") or ""))
    front = (config.get("front_matter") or {}).get("graphical_abstract") or {}
    abstract_img = project_root / "output" / "figures" / "graphical_abstract.png"
    caption = _tex_escape(str(front.get("caption") or ""))
    abstract_width = str(front.get("width") or r"0.96\textwidth")
    abstract_max_height = str(front.get("max_height") or r"0.42\textheight")

    author_lines: list[str] = []
    for author in config.get("authors") or []:
        name = _tex_escape(str(author.get("name") or ""))
        affil = _tex_escape(str(author.get("affiliation") or ""))
        email = _tex_escape(str(author.get("email") or ""))
        orcid = _tex_escape(str(author.get("orcid") or ""))
        meta = " \\quad ".join(
            part
            for part in (
                f"\\texttt{{{email}}}" if email else "",
                f"ORCID:~{orcid}" if orcid else "",
            )
            if part
        )
        author_lines.append(
            f"{{\\large\\bfseries {name}\\par}}\n"
            + (f"{{\\normalsize {affil}\\par}}\n" if affil else "")
            + (f"{{\\small {meta}\\par}}\n" if meta else "")
            + "\\vspace{0.6em}\n"
        )
    authors_block = "".join(author_lines)
    footer = " \\,\\textbullet\\, ".join(
        part for part in (f"Version {version}" if version else "", date) if part
    )

    abstract_block = ""
    if front.get("enabled") and abstract_img.is_file():
        abstract_block = (
            "\\vspace{1.0em}\n"
            f"\\includegraphics[width={abstract_width},height={abstract_max_height},keepaspectratio]"
            f"{{{abstract_img}}}\\par\n"
            + (f"\\vspace{{0.5em}}{{\\footnotesize {caption}\\par}}\n" if caption else "")
        )

    return (
        f"\\hypersetup{{pdftitle={{{title}}}}}\n"
        "\\begin{titlepage}\n\\centering\n\\vspace*{0.3in}\n"
        f"{{\\LARGE\\bfseries {title}\\par}}\n\\vspace{{0.5em}}\n"
        + (f"{{\\large\\itshape {subtitle}\\par}}\n\\vspace{{1.4em}}\n" if subtitle else "\\vspace{1.0em}\n")
        + authors_block
        + (f"\\vspace{{0.4em}}{{\\small {footer}\\par}}\n" if footer else "")
        + abstract_block
        + "\\end{titlepage}\n"
    )


def _combine_manuscript_markdown(project_root: Path) -> tuple[Path, Path]:
    """Compose + hydrate the sheaf sections into the combined manuscript markdown.

    Shared by the canonical PDF render and the `.tex` consumed-inventory render so the
    two never diverge. Returns (combined_md_path, out_pdf_dir)."""
    from manuscript.hydrate import write_resolved_manuscript
    from manuscript.sheaf import compose_all_sections
    from manuscript.variables import generate_variables

    root = project_root.resolve()
    manuscript_dir = root / "manuscript"
    out_pdf_dir = root / "output" / "pdf"
    out_pdf_dir.mkdir(parents=True, exist_ok=True)

    compose_all_sections(root, manuscript_dir=manuscript_dir)
    variables = generate_variables(root, require_analysis_outputs=False)
    resolved_dir = write_resolved_manuscript(root, variables)

    sections = sorted(p for p in resolved_dir.glob("[0-9][0-9]_*.md"))
    if not sections:
        sections = sorted(p for p in manuscript_dir.glob("[0-9][0-9]_*.md"))
    coverage_pages = [p for p in sections if "sheaf_coverage" in p.name]
    sections = [p for p in sections if "sheaf_coverage" not in p.name] + coverage_pages
    combined_text = "\n\n".join(p.read_text(encoding="utf-8") for p in sections)
    combined_md = out_pdf_dir / "_combined_manuscript.md"
    combined_md.write_text(combined_text, encoding="utf-8")
    return combined_md, out_pdf_dir


def render_combined_tex(project_root: Path) -> Path:
    """Render the combined manuscript to standalone LaTeX (`_combined_manuscript.tex`).

    Pandoc emits the `.tex` without compiling a PDF (no xelatex), so this is a cheap,
    deterministic way to materialise the *rendered* LaTeX that the typography
    consumed-inventory gate checks: declared geometry and the preamble font-scale must
    survive into the render, not just be declared. Uses the SAME preamble include and
    geometry variable as `render_pdf`, so what this proves about the `.tex` holds for
    the canonical PDF. Raises if pandoc is unavailable."""
    if shutil.which("pandoc") is None:
        raise RuntimeError("pandoc not found on PATH (required to render the combined .tex)")
    root = project_root.resolve()
    manuscript_dir = root / "manuscript"
    combined_md, out_pdf_dir = _combine_manuscript_markdown(root)
    header_tex = out_pdf_dir / "_standalone_preamble.tex"
    header_tex.write_text(extract_preamble(manuscript_dir / "preamble.md") + "\n", encoding="utf-8")
    tex_out = out_pdf_dir / "_combined_manuscript.tex"
    cmd = [
        "pandoc",
        str(combined_md),
        "-o",
        str(tex_out),
        "--from=markdown+tex_math_dollars+raw_tex",
        "--to=latex",
        "--standalone",
        "--number-sections",
        "-H",
        str(header_tex),
        "-V",
        f"geometry:{geometry_string(manuscript_dir / 'config.yaml')}",
        "-V",
        "colorlinks=true",
        f"--resource-path={manuscript_dir}",
    ]
    result = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"pandoc latex render failed: {result.stderr.strip()}")
    return tex_out


def render_pdf(project_root: Path) -> int:
    """Compose, hydrate, and render the canonical manuscript PDF."""
    root = project_root.resolve()
    for tool in ("pandoc", "xelatex"):
        if shutil.which(tool) is None:
            print(f"error: `{tool}` not found on PATH (required for standalone render)", file=sys.stderr)
            return 2

    manuscript_dir = root / "manuscript"
    combined_md, out_pdf_dir = _combine_manuscript_markdown(root)
    combined_text = combined_md.read_text(encoding="utf-8")
    # Keep the historical standalone path as a mirror so older diagnostics do
    # not accidentally compare against a stale combined manuscript.
    (out_pdf_dir / "_standalone_combined.md").write_text(combined_text, encoding="utf-8")

    header_tex = out_pdf_dir / "_standalone_preamble.tex"
    header_tex.write_text(extract_preamble(manuscript_dir / "preamble.md") + "\n", encoding="utf-8")

    config = yaml.safe_load((manuscript_dir / "config.yaml").read_text(encoding="utf-8")) or {}

    cover_tex = out_pdf_dir / "_standalone_cover.tex"
    cover_tex.write_text(build_cover_tex(config, root), encoding="utf-8")

    pdf_out = out_pdf_dir / "on_policy_distillation.pdf"
    cmd = [
        "pandoc",
        str(combined_md),
        "-o",
        str(pdf_out),
        "--from=markdown+tex_math_dollars+raw_tex",
        "--pdf-engine=xelatex",
        "--standalone",
        "--number-sections",
        "-H",
        str(header_tex),
        "--include-before-body",
        str(cover_tex),
        "-V",
        f"geometry:{geometry_string(manuscript_dir / 'config.yaml')}",
        "-V",
        "colorlinks=true",
        "-V",
        "linkcolor=red",
        "-V",
        "urlcolor=red",
        "-V",
        "citecolor=red",
        f"--resource-path={manuscript_dir}",
    ]
    crossref = shutil.which("pandoc-crossref")
    if crossref:
        cmd += ["--filter", crossref]
    bib = manuscript_dir / "references.bib"
    if bib.is_file():
        cmd += [
            "--citeproc",
            "--bibliography",
            str(bib),
            "-M",
            "link-citations=true",
            "-M",
            "reference-section-title=References",
        ]

    print("rendering (canonical):", " ".join(cmd))
    result = subprocess.run(cmd, cwd=root)
    if result.returncode != 0:
        print("error: pandoc render failed", file=sys.stderr)
        return result.returncode
    print(f"canonical PDF: {pdf_out} ({pdf_out.stat().st_size} bytes)")
    return 0


__all__ = ["_tex_escape", "build_cover_tex", "render_combined_tex", "render_pdf"]
