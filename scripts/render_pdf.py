#!/usr/bin/env python3
"""Self-contained PDF renderer for the standalone repository.

This is the standalone build path: it composes, hydrates, and renders the
manuscript to PDF using only this project's own code plus the external `pandoc`
and `xelatex` command-line tools — **no monorepo `infrastructure` import**. A
checkout of this repository alone can produce its PDF with::

    uv run python scripts/render_pdf.py

Typography is read from this project's own sources: page margins from
``manuscript/config.yaml`` (``metadata.geometry``), the dense body font from
``manuscript/preamble.md`` (the ``fontsize`` package), and red hyperlinks via
pandoc's ``colorlinks`` variables. The richer monorepo pipeline
(``scripts/03_render_pdf.py`` in the template repo) adds transmission bookends,
QR strips, and LaTeX post-processing; this renderer is the portable subset.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from manuscript.render_helpers import extract_preamble, geometry_string  # noqa: E402


def _tex_escape(text: str) -> str:
    """Escape the LaTeX special characters that occur in metadata strings."""
    for char, repl in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"),
                        ("#", r"\#"), ("_", r"\_"), ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}")):
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

    author_lines: list[str] = []
    for author in config.get("authors") or []:
        name = _tex_escape(str(author.get("name") or ""))
        affil = _tex_escape(str(author.get("affiliation") or ""))
        email = _tex_escape(str(author.get("email") or ""))
        orcid = _tex_escape(str(author.get("orcid") or ""))
        meta = " \\quad ".join(part for part in (f"\\texttt{{{email}}}" if email else "",
                                                 f"ORCID:~{orcid}" if orcid else "") if part)
        author_lines.append(
            f"{{\\large\\bfseries {name}\\par}}\n"
            + (f"{{\\normalsize {affil}\\par}}\n" if affil else "")
            + (f"{{\\small {meta}\\par}}\n" if meta else "")
            + "\\vspace{0.6em}\n"
        )
    authors_block = "".join(author_lines)
    footer = " \\,\\textbullet\\, ".join(part for part in (f"Version {version}" if version else "", date) if part)

    abstract_block = ""
    if front.get("enabled") and abstract_img.is_file():
        abstract_block = (
            "\\vspace{1.0em}\n"
            f"\\includegraphics[width=0.97\\textwidth,height=0.52\\textheight,keepaspectratio]{{{abstract_img}}}\\par\n"
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


def main() -> int:
    for tool in ("pandoc", "xelatex"):
        if shutil.which(tool) is None:
            print(f"error: `{tool}` not found on PATH (required for standalone render)", file=sys.stderr)
            return 2

    from manuscript.hydrate import write_resolved_manuscript
    from manuscript.sheaf import compose_all_sections
    from manuscript.variables import generate_variables

    manuscript_dir = PROJECT_ROOT / "manuscript"
    out_pdf_dir = PROJECT_ROOT / "output" / "pdf"
    out_pdf_dir.mkdir(parents=True, exist_ok=True)

    # 1. compose flat sections from sheaf fragments, 2. hydrate {{tokens}}.
    compose_all_sections(PROJECT_ROOT, manuscript_dir=manuscript_dir)
    variables = generate_variables(PROJECT_ROOT, require_analysis_outputs=False)
    resolved_dir = write_resolved_manuscript(PROJECT_ROOT, variables)

    # 3. concatenate composed+hydrated sections in lexical (manifest) order.
    sections = sorted(p for p in resolved_dir.glob("[0-9][0-9]_*.md"))
    if not sections:
        sections = sorted(p for p in manuscript_dir.glob("[0-9][0-9]_*.md"))
    combined_md = out_pdf_dir / "_standalone_combined.md"
    combined_md.write_text("\n\n".join(p.read_text(encoding="utf-8") for p in sections), encoding="utf-8")

    # 4. preamble (font) + geometry (margins), both from project-owned sources.
    header_tex = out_pdf_dir / "_standalone_preamble.tex"
    header_tex.write_text(extract_preamble(manuscript_dir / "preamble.md") + "\n", encoding="utf-8")

    config = yaml.safe_load((manuscript_dir / "config.yaml").read_text(encoding="utf-8")) or {}
    title = str((config.get("paper") or {}).get("title") or "Manuscript")

    # Custom title page: author block + graphical abstract, inserted before body.
    cover_tex = out_pdf_dir / "_standalone_cover.tex"
    cover_tex.write_text(build_cover_tex(config, PROJECT_ROOT), encoding="utf-8")

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
        # Red hyperlinks — self-contained, no LaTeX post-processing needed.
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
    _ = title  # title is rendered by the custom cover page, not pandoc's \maketitle
    crossref = shutil.which("pandoc-crossref")
    if crossref:
        cmd += ["--filter", crossref]
    bib = manuscript_dir / "references.bib"
    if bib.is_file():
        cmd += ["--citeproc", "--bibliography", str(bib)]

    print("rendering (standalone):", " ".join(cmd))
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print("error: pandoc render failed", file=sys.stderr)
        return result.returncode
    print(f"✓ standalone PDF: {pdf_out} ({pdf_out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
