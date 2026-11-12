#!/usr/bin/env python3
"""The project's single gate entry point: one arm per separately runnable check.

CI calls these arms, and the docs quote these arms; the argv of every check is
declared once, here. Nothing in `.github/workflows/ci.yml` restates a command.

Arms
----
``lint``    ruff over `src tests scripts` plus a byte-compile of the same trees.
``fast``    the tightest edit loop: whole suite minus `artifact_slow` and
            `render_slow`, no coverage. This is the default arm.
``full``    the release gate: whole suite under coverage with the 90% floor.
``docs``    relative-link check over tracked Markdown plus the documentation
            contract tests.
``gnn``     upstream conformance: provision/select the checkout pinned by
            `gnn/upstream.json`, run the estate reader (`gnn.importers`) from
            that revision, then run the conformance and parser tests.
``chain``   the convergent artifact chain (`scripts/run_full_chain.py`), which a
            clean checkout must run before `full` and `render`.
``render``  the canonical manuscript PDF (`scripts/render_pdf.py`); needs the
            `chain` arm's artifacts, pandoc, and xelatex.
``all``     the CI sequence: lint, docs, gnn, chain, full.

There is no `types` arm: the project configures no static type checker.

Usage:
    uv run --extra dev python scripts/gate.py            # fast arm
    uv run --extra dev python scripts/gate.py full       # release gate
    uv run --extra dev python scripts/gate.py all        # the CI sequence
    uv run --extra dev python scripts/gate.py --list     # arms and their argv
"""

from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC = PROJECT_ROOT / "src"

#: Pin file whose revision the `gnn` arm provisions and tests.
PIN_PATH = PROJECT_ROOT / "gnn" / "upstream.json"
#: Conformance workflow and job key `.github/GNN.md` must name (estate registry).
CONFORMANCE_WORKFLOW = ".github/workflows/ci.yml"
CONFORMANCE_JOB = "release-gate"
#: Checkout used when no explicit or sibling checkout is available. Gitignored.
GNN_CACHE = PROJECT_ROOT / "output" / "gnn-pin"
#: Parser dependencies, installed into the pinned checkout's own interpreter.
GNN_PARSER_DEPENDENCIES = ("numpy", "defusedxml", "psutil")
#: Interpreter the pinned parser runs under (upstream supports 3.12 here).
GNN_PYTHON = "3.12"

#: Arms the CI sequence runs, in order. `render` stays a separate arm: CI does
#: not build the PDF, and neither does `all`.
CI_ARM_ORDER = ("lint", "docs", "gnn", "chain", "full")
#: Every selectable arm name.
ARM_NAMES = ("lint", "fast", "full", "docs", "gnn", "chain", "render", "all")


def _python() -> str:
    """The interpreter running this gate, so every arm shares one environment."""
    return sys.executable


def _upstream():
    """Checkout selection and conformance support, imported only by the `gnn` arms."""
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    # Lazy so the other arms do not pay numpy/pin-loader import cost.
    import gnn.upstream as upstream

    return upstream


def lint_commands() -> list[list[str]]:
    """Static checks: ruff, then a byte-compile of the shipped trees."""
    return [
        [_python(), "-m", "ruff", "check", "src", "tests", "scripts"],
        [_python(), "-m", "compileall", "-q", "src", "scripts", "tests"],
    ]


def fast_commands() -> list[list[str]]:
    """The tightest documented edit loop (no coverage, no slow lanes)."""
    return [[_python(), "-m", "pytest", "tests/", "-m", "not artifact_slow and not render_slow", "--no-cov", "-q"]]


def full_commands() -> list[list[str]]:
    """The release gate: whole suite under coverage with the 90% floor."""
    return [[_python(), "-m", "pytest", "tests/", "--cov=src", "--cov-fail-under=90", "-q"]]


def docs_commands() -> list[list[str]]:
    """Documentation checks: relative links, then the doc-contract tests."""
    return [
        [_python(), str(PROJECT_ROOT / "scripts" / "check_docs_links.py")],
        [_python(), "-m", "pytest", "tests/test_documentation_contracts.py", "-q", "--no-cov"],
    ]


def chain_commands() -> list[list[str]]:
    """The convergent artifact chain; `full` and `render` read its tree."""
    return [[_python(), str(PROJECT_ROOT / "scripts" / "run_full_chain.py"), "--max-passes", "4"]]


def render_commands() -> list[list[str]]:
    """The canonical manuscript PDF render."""
    return [[_python(), str(PROJECT_ROOT / "scripts" / "render_pdf.py")]]


def gnn_commands() -> list[list[str]]:
    """Conformance and parser tests, executed against the pinned checkout."""
    return [
        [
            _python(),
            "-m",
            "pytest",
            "tests/test_gnn_upstream_conformance.py",
            "tests/test_gnn.py",
            "-q",
            "--no-cov",
        ],
    ]


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    """Run one Git command against a checkout, with stdin closed."""
    return subprocess.run(
        ["git", "-C", str(root), *args],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )


def _pin_usable(root: Path, commit: str) -> tuple[bool, str]:
    """Whether a checkout supplies the pinned parser, interpreter, and commit."""
    if not (root / ".git").exists():
        return False, f"{root} is not a Git checkout"
    if not _upstream().checkout_available(root):
        return False, f"{root} lacks the upstream parser source or its .venv/bin/python"
    presence = _git(root, "cat-file", "-e", f"{commit}^{{commit}}")
    if presence.returncode != 0:
        return False, f"{root} does not contain the pinned commit {commit}"
    return True, f"{root} carries the pinned commit"


def _provision(root: Path, repository: str, commit: str, tag: str | None) -> None:
    """Fetch exactly the pinned release into `root` and install parser deps."""
    root.mkdir(parents=True, exist_ok=True)
    steps: list[list[str]] = [
        ["git", "init", "--quiet", str(root)],
        ["git", "-C", str(root), "remote", "add", "origin", repository],
    ]
    fetch = ["git", "-C", str(root), "fetch", "--depth", "1", "origin", commit]
    if tag:
        fetch.append(f"refs/tags/{tag}:refs/tags/{tag}")
    steps.append(fetch)
    steps.append(["git", "-C", str(root), "checkout", "--quiet", "--detach", commit])
    steps.append(["uv", "venv", "--python", GNN_PYTHON, "--no-project", str(root / ".venv")])
    steps.append(
        [
            "uv",
            "pip",
            "install",
            "--python",
            str(root / ".venv" / "bin" / "python"),
            *GNN_PARSER_DEPENDENCIES,
        ]
    )
    for step in steps:
        print("+", " ".join(step), flush=True)
        code = subprocess.run(step, stdin=subprocess.DEVNULL, check=False).returncode
        if code != 0:
            raise SystemExit(f"gnn arm: provisioning step failed (exit {code}): {' '.join(step)}")


def _read_bootstrap_pin() -> dict[str, str]:
    """Read the pin fields the arm needs before a pinned environment exists.

    Provisioning has no interpreter yet that could import the shared reader, so
    the revision, repository and tag are read literally. Everything the
    GNN-FEP contract makes a finding — schema, repository identity, commit
    shape, tag against version, pointer completeness and the specifications —
    is `gnn.importers`' job in :func:`run_reader`, from the environment this
    read enables.
    """
    try:
        data = json.loads(PIN_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"gnn arm: cannot read {PIN_PATH.relative_to(PROJECT_ROOT)}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"gnn arm: {PIN_PATH.name} must be a JSON object")
    missing = [
        key for key in ("commit", "repository") if not isinstance(data.get(key), str) or not data[key]
    ]
    if missing:
        raise SystemExit(f"gnn arm: {PIN_PATH.name} records no {missing}")
    tag = data.get("tag")
    version = data.get("version")
    return {
        "commit": data["commit"],
        "repository": data["repository"],
        "tag": tag if isinstance(tag, str) else "",
        "version": version if isinstance(version, str) else "",
    }


def ensure_gnn_checkout(pin: dict[str, str]) -> Path:
    """Select the pinned upstream checkout, provisioning it when nothing usable exists."""
    upstream = _upstream()
    commit = pin["commit"]
    explicit = os.environ.get(upstream.ENV_UPSTREAM_ROOT)
    if explicit is not None and not explicit.strip():
        raise SystemExit(f"gnn arm: {upstream.ENV_UPSTREAM_ROOT} must not be empty")
    target = Path(explicit.strip()).resolve() if explicit is not None else GNN_CACHE
    candidates = [target] if explicit is not None else [upstream.default_gnn_root(PROJECT_ROOT), target]
    for candidate in candidates:
        usable, reason = _pin_usable(candidate, commit)
        if usable:
            print(f"gnn arm: {reason}")
            return candidate
        if candidate == target and candidate.exists() and (not candidate.is_dir() or any(candidate.iterdir())):
            raise SystemExit(f"gnn arm: {reason}; refusing to provision into an occupied path")
    print(f"gnn arm: provisioning {pin['tag'] or pin['version'] or commit} ({commit}) into {target}")
    _provision(target, pin["repository"], commit, pin["tag"])
    usable, reason = _pin_usable(target, commit)
    if not usable:
        raise SystemExit(f"gnn arm: provisioning did not produce a usable checkout: {reason}")
    print(f"gnn arm: {reason}")
    return target


def _report_pin(pin: dict[str, str], checkout: Path) -> None:
    """Print the resolved pin and, under GitHub Actions, add it to the summary."""
    version = (pin["version"] or pin["tag"]).removeprefix("v")
    print(
        f"gnn arm: {pin['tag'] or pin['version']} version={version or '(unrecorded)'} "
        f"commit={pin['commit']} checkout={checkout}"
    )
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as handle:
            handle.write(f"gnn-version={version}\n")


def reader_command(interpreter: str) -> list[str]:
    """The estate's shared importer reader, run against this checkout."""
    return [
        interpreter,
        "-m",
        "gnn.importers",
        "check",
        "--repo",
        ".",
        "--require-pointer",
        "--workflow",
        CONFORMANCE_WORKFLOW,
        "--job",
        CONFORMANCE_JOB,
    ]


def run_reader(checkout: Path, commit: str) -> int:
    """Run `gnn.importers` from the pinned revision, in the pinned environment.

    The reader and the parser it validates must both be the pinned release's
    bytes, so `src/gnn` is extracted from `commit` the way the conformance tests
    extract the parser, and only that tree is placed on `PYTHONPATH`. The
    interpreter is the checkout's own, so no live working tree is on the path.
    """
    command = reader_command(str(_upstream().gnn_checkout_python(checkout)))
    print(f"[gnn] $ {_display(command)}", flush=True)
    with tempfile.TemporaryDirectory(prefix="gnn-reader-") as name:
        extract = Path(name)
        archive = subprocess.run(
            ["git", "-C", str(checkout), "archive", commit, "src/gnn"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
        )
        if archive.returncode != 0:
            message = archive.stderr.decode("utf-8", "replace").strip()
            print(f"[gnn] cannot extract src/gnn at {commit} from {checkout}: {message}")
            return archive.returncode
        with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as stream:
            if sys.version_info >= (3, 12):
                stream.extractall(extract, filter="data")
            else:  # pragma: no cover - the documented gate runs a modern interpreter
                stream.extractall(extract)
        env = {**os.environ, "PYTHONPATH": str(extract / "src")}
        return subprocess.run(command, cwd=PROJECT_ROOT, env=env, check=False).returncode


def run_commands(label: str, commands: list[list[str]], env: dict[str, str] | None = None) -> int:
    """Run one arm's commands in order, stopping at the first non-zero exit."""
    started = time.monotonic()
    for command in commands:
        print(f"[{label}] $ {' '.join(command)}", flush=True)
        result = subprocess.run(command, cwd=PROJECT_ROOT, env=env, check=False)
        if result.returncode != 0:
            print(f"[{label}] FAIL exit {result.returncode} after {time.monotonic() - started:.1f}s")
            return result.returncode
    print(f"[{label}] OK {time.monotonic() - started:.1f}s")
    return 0


def run_arm(arm: str) -> int:
    """Dispatch one arm by name."""
    if arm in ("gnn", "full"):
        pin = _read_bootstrap_pin()
        checkout = ensure_gnn_checkout(pin)
        _report_pin(pin, checkout)
        env = {**os.environ, _upstream().ENV_UPSTREAM_ROOT: str(checkout)}
        if arm == "gnn":
            code = run_reader(checkout, pin["commit"])
            if code != 0:
                print(f"[gnn] FAIL exit {code} at the shared importer reader")
                return code
            return run_commands(arm, gnn_commands(), env=env)
        return run_commands(arm, full_commands(), env=env)
    commands = {
        "lint": lint_commands,
        "fast": fast_commands,
        "docs": docs_commands,
        "chain": chain_commands,
        "render": render_commands,
    }[arm]()
    return run_commands(arm, commands)


def _display(command: list[str]) -> str:
    """A command as a reader would type it: `python`, project-relative paths."""
    parts = [
        "python" if part == _python() or part.endswith("/.venv/bin/python") else part for part in command
    ]
    return " ".join(part.removeprefix(str(PROJECT_ROOT) + os.sep) for part in parts)


def arm_table() -> list[str]:
    """One documentation row per arm, listing the argv it runs."""
    gnn_steps = [
        _display(reader_command("python")),
        *(_display(cmd) for cmd in gnn_commands()),
    ]
    rows = [
        "lint   " + " | ".join(_display(cmd) for cmd in lint_commands()),
        "fast   " + " | ".join(_display(cmd) for cmd in fast_commands()),
        "full   " + " | ".join(_display(cmd) for cmd in full_commands()),
        "docs   " + " | ".join(_display(cmd) for cmd in docs_commands()),
        "gnn    provision the pin in gnn/upstream.json, then " + " | ".join(gnn_steps),
        "chain  " + " | ".join(_display(cmd) for cmd in chain_commands()),
        "render " + " | ".join(_display(cmd) for cmd in render_commands()),
        "all    " + ", ".join(CI_ARM_ORDER),
    ]
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "arm",
        nargs="?",
        default="fast",
        choices=ARM_NAMES,
        help="lint | fast | full | docs | gnn | chain | render | all (default: fast)",
    )
    parser.add_argument("--list", action="store_true", help="print each arm and the argv it runs")
    args = parser.parse_args(argv)

    if args.list:
        print("\n".join(arm_table()))
        return 0
    if args.arm == "all":
        for arm in CI_ARM_ORDER:
            code = run_arm(arm)
            if code != 0:
                print(f"[all] FAIL at arm {arm} (exit {code})")
                return code
        print("[all] OK")
        return 0
    return run_arm(args.arm)


if __name__ == "__main__":
    raise SystemExit(main())
