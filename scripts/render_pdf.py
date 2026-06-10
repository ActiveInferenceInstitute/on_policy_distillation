#!/usr/bin/env python3
"""Public CLI facade for the standalone PDF renderer."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from manuscript.pdf_render import _tex_escape, build_cover_tex, render_pdf  # noqa: E402,F401


def main() -> int:
    return render_pdf(PROJECT_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
