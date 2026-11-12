#!/usr/bin/env python3
"""Check every relative link in the repository's Markdown surface.

The project has no mkdocs or markdown-link-check dependency, so this is the
documentation arm of the gate entry point: it walks the Markdown files that Git
tracks, extracts inline links/images and reference-style definitions, and
resolves each relative target against the containing file.

Checked: relative paths, relative paths with a `#fragment` or `?query` suffix,
`<...>`-wrapped targets, and reference-style definitions.
Skipped: absolute URLs with a scheme, protocol-relative `//` targets, pure
fragments, and targets under generated or tool-owned trees (`output/`, `.venv/`,
`htmlcov/`, `lean/.lake/`) that a clean checkout does not contain.

Exit code is honest: 0 only when every checked target exists.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

PROJECT_ROOT = Path(__file__).resolve().parent.parent

#: Link target prefixes that are generated or tool-owned, never tracked.
GENERATED_PREFIXES = ("output/", ".venv/", "htmlcov/", "lean/.lake/", "lean/build/")

#: `[text](target)` and `![alt](target)`, with an optional quoted title.
INLINE_LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*(<[^>]*>|[^)\s]+)(?:\s+\"[^\"]*\")?\s*\)")
#: `[label]: target` reference definitions.
REFERENCE_DEF_RE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(<[^>]*>|\S+)")
FENCE_RE = re.compile(r"^\s{0,3}(```|~~~)")


def tracked_markdown(project_root: Path) -> list[Path]:
    """The Markdown files Git tracks under the project root.

    A copy-out checkout without `.git` (the standalone case the project
    documents) falls back to a tree walk over the same ignored set.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "ls-files", "-z", "--", "*.md"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        ignored = {".git", ".lake", ".pytest_cache", ".ruff_cache", ".venv", "__pycache__", "htmlcov", "output"}
        return sorted(
            path
            for path in project_root.rglob("*.md")
            if not ignored.intersection(path.relative_to(project_root).parts)
        )
    names = [name for name in result.stdout.decode("utf-8").split("\0") if name]
    return [project_root / name for name in sorted(names)]


def iter_link_targets(text: str) -> list[tuple[int, str]]:
    """Every link target in one file, with its 1-based line number."""
    targets: list[tuple[int, str]] = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in INLINE_LINK_RE.finditer(line):
            targets.append((number, match.group(1)))
        definition = REFERENCE_DEF_RE.match(line)
        if definition:
            targets.append((number, definition.group(1)))
    return targets


def target_path(target: str) -> str:
    """The path part of a link target, without its `#fragment` or `?query`."""
    return unquote(target.split("#", 1)[0].split("?", 1)[0])


def is_checkable(project_root: Path, source: Path, target: str) -> bool:
    """Whether a link target names a repository-relative path this check owns."""
    if not target or target.startswith("#") or target.startswith("//"):
        return False
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
        return False
    if target.startswith("/") or target.startswith("~"):
        return False
    path = target_path(target)
    if not path:
        return False
    try:
        relative = (source.parent / path).resolve().relative_to(project_root.resolve())
    except ValueError:
        return True
    return not relative.as_posix().startswith(GENERATED_PREFIXES)


def broken_links(project_root: Path, files: list[Path]) -> list[str]:
    """Every unresolved relative target, as `file:line -> target` rows."""
    broken: list[str] = []
    for source in files:
        for number, raw in iter_link_targets(source.read_text(encoding="utf-8")):
            target = raw.strip("<>")
            if not is_checkable(project_root, source, target):
                continue
            resolved = (source.parent / target_path(target)).resolve()
            if not resolved.exists():
                broken.append(f"{source.relative_to(project_root)}:{number} -> {target}")
    return broken


def main() -> int:
    files = tracked_markdown(PROJECT_ROOT)
    broken = broken_links(PROJECT_ROOT, files)
    for row in broken:
        print(f"broken link: {row}")
    print(f"checked {len(files)} markdown files; {len(broken)} broken relative link(s)")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
