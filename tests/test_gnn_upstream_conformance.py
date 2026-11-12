"""Upstream-parser conformance test for the project-owned GNN parser.

The project-owned parser (``src/gnn/parser.py``) is cited-not-vendored: it never
imports upstream GNN code. This test makes the "spec-conformant" claim checkable
by running the **real upstream parser**
(``gnn.parsers.markdown_parser.MarkdownGNNParser``) of the pinned GNN release
(``gnn/upstream.json``) against every shipped ``gnn/*.gnn.md`` spec and
comparing normalized digests. Any divergence fails.

The upstream parser runs under the GNN checkout's own interpreter, with the
pinned commit's ``src/gnn`` extracted from Git onto ``PYTHONPATH`` — so the
bytes exercised are the pinned release's bytes, not the live working tree's
(the checkout may legitimately carry in-progress edits). The checkout is treated
as read-only: this test only runs ``git archive`` / ``git cat-file``.

When the checkout or its ``.venv`` is unavailable the test skips with an
explicit reason; setting ``ON_POLICY_DISTILLATION_GNN_ROOT`` selects a checkout
explicitly (and then an unavailable checkout is a failure, not a skip).

The pin's shape, schema, repository identity and the specifications are
validated by the estate's shared reader (``gnn.importers``) in the ``gnn`` gate
arm, not here. This file reads the pin's values for its digest run and keeps the
deliberate re-pin tripwire.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from gnn.parser import parse_gnn_file
from gnn.upstream import (
    DIGEST_DRIVER_SOURCE,
    ENV_UPSTREAM_ROOT,
    PARSER_RELATIVE_PATH,
    UpstreamConformanceError,
    checkout_available,
    default_gnn_root,
    digest_divergences,
    gnn_checkout_python,
    normalize_upstream_digest,
    resolve_gnn_root,
    spec_digest,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PIN_PATH = PROJECT_ROOT / "gnn" / "upstream.json"
GNN_DIR = PROJECT_ROOT / "gnn"
SHIPPED_SPECS = sorted(GNN_DIR.glob("*.gnn.md"))

#: The canonical workstream pin. Bumping it is a deliberate act: this test pins
#: the pin, so a silent re-pin cannot pass unnoticed.
CANONICAL_TAG = "v5.1.0"
CANONICAL_COMMIT = "75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf"


def _pin() -> dict[str, Any]:
    """The pin's recorded values.

    Shape validation belongs to the shared reader the ``gnn`` arm runs; this
    read supplies the values the digest run needs and the tripwire compares.
    """
    return json.loads(PIN_PATH.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class UpstreamRun:
    """One execution of the pinned upstream parser over the shipped specs."""

    pin: dict[str, Any]
    root: Path
    payload: dict[str, Any]
    mutant: Path
    extract_dir: Path


@pytest.fixture(scope="module")
def upstream_run(tmp_path_factory: pytest.TempPathFactory) -> UpstreamRun:
    """Execute the pinned upstream parser on every shipped spec + a leniency mutant."""
    pin = _pin()
    root = resolve_gnn_root(PROJECT_ROOT)
    explicit = ENV_UPSTREAM_ROOT in os.environ
    if not checkout_available(root):
        message = (
            f"upstream GNN checkout unavailable at {root} (needs {PARSER_RELATIVE_PATH} "
            f"and .venv/bin/python); set {ENV_UPSTREAM_ROOT} to select one"
        )
        if explicit:
            pytest.fail(message)
        pytest.skip(message)

    presence = subprocess.run(
        ["git", "-C", str(root), "cat-file", "-e", f"{pin['commit']}^{{commit}}"],
        capture_output=True,
        text=True,
    )
    assert presence.returncode == 0, (
        f"pinned commit {pin['commit']} is not present in {root}; fetch the pinned release before "
        "running the upstream conformance check"
    )

    extract_dir = tmp_path_factory.mktemp("gnn_upstream_pin")
    archive = subprocess.run(
        ["git", "-C", str(root), "archive", pin["commit"], "src/gnn"],
        check=True,
        capture_output=True,
    )
    with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as stream:
        if sys.version_info >= (3, 12):
            stream.extractall(extract_dir, filter="data")
        else:  # pragma: no cover - the documented gate runs a modern interpreter
            stream.extractall(extract_dir)

    # Leniency mutant: the upstream parser collapses heading whitespace, so the
    # doubled-space spelling still parses as the ontology section, while the
    # project parser accepts only the canonical and single-spaced spellings.
    # The digests must therefore diverge. Used as the non-vacuity control.
    mutant = extract_dir / "spaced_ontology.gnn.md"
    mutant.write_text(
        (GNN_DIR / "bernoulli_toy.gnn.md")
        .read_text(encoding="utf-8")
        .replace("## ActInfOntologyAnnotation", "## ActInf  Ontology  Annotation"),
        encoding="utf-8",
    )

    spec_paths = [str(path.resolve()) for path in SHIPPED_SPECS] + [str(mutant)]
    env = {**os.environ, "PYTHONPATH": str(extract_dir / "src")}
    parser_module, parser_class = pin["parser_module"], pin["parser_class"]
    command = [
        str(gnn_checkout_python(root)),
        "-c",
        DIGEST_DRIVER_SOURCE,
        "--module",
        parser_module,
        "--class-name",
        parser_class,
    ]
    for spec in spec_paths:
        command += ["--spec", spec]
    proc = subprocess.run(command, capture_output=True, text=True, env=env, cwd=extract_dir)
    assert proc.returncode == 0, f"upstream digest driver failed:\n{proc.stderr}"

    return UpstreamRun(
        pin=pin,
        root=root,
        payload=json.loads(proc.stdout),
        mutant=mutant,
        extract_dir=extract_dir,
    )


def test_pin_file_names_the_canonical_release() -> None:
    """The shipped pin is the canonical workstream pin (v5.1.0)."""
    pin = _pin()
    assert pin["tag"] == CANONICAL_TAG
    assert pin["commit"] == CANONICAL_COMMIT
    assert pin["version"] == CANONICAL_TAG.removeprefix("v")


def test_resolve_gnn_root_honours_explicit_selection(tmp_path: Path) -> None:
    """An explicit checkout selection is final; an empty selection is refused."""
    chosen = tmp_path / "gnn"
    chosen.mkdir()
    assert resolve_gnn_root(PROJECT_ROOT, {ENV_UPSTREAM_ROOT: str(chosen)}) == chosen.resolve()
    assert resolve_gnn_root(PROJECT_ROOT, {}) == default_gnn_root(PROJECT_ROOT)
    with pytest.raises(ValueError, match="must not be empty"):
        resolve_gnn_root(PROJECT_ROOT, {ENV_UPSTREAM_ROOT: "  "})


def test_upstream_parser_ran_from_the_pinned_commit(upstream_run: UpstreamRun) -> None:
    """The executed parser module is the extracted pinned release, not the live tree."""
    parser_info = upstream_run.payload["parser"]
    assert parser_info["module"] == upstream_run.pin["parser_module"]
    assert parser_info["class"] == upstream_run.pin["parser_class"]
    parser_file = Path(parser_info["file"]).resolve()
    assert parser_file.is_relative_to(upstream_run.extract_dir.resolve())
    assert parser_info["gnn_version"] == upstream_run.pin["version"]


def test_upstream_parser_accepts_every_shipped_spec(upstream_run: UpstreamRun) -> None:
    """The pinned upstream parser parses every shipped spec without errors."""
    for spec in SHIPPED_SPECS:
        digest = upstream_run.payload["specs"][str(spec.resolve())]
        assert digest["diagnostics"]["success"] is True, f"{spec.name}: {digest['diagnostics']}"
        assert digest["diagnostics"]["errors"] == [], f"{spec.name}: {digest['diagnostics']['errors']}"


@pytest.mark.parametrize("spec", SHIPPED_SPECS, ids=lambda path: path.name)
def test_project_parser_digest_matches_upstream(upstream_run: UpstreamRun, spec: Path) -> None:
    """The project parser's normalized digest equals the pinned upstream parser's digest."""
    project = spec_digest(parse_gnn_file(spec))
    upstream = normalize_upstream_digest(upstream_run.payload["specs"][str(spec.resolve())])
    assert digest_divergences(project, upstream) == []


def test_conformance_check_discriminates_on_the_leniency_mutant(upstream_run: UpstreamRun) -> None:
    """Non-vacuity control: the doubled-space ontology heading splits the parsers.

    The upstream parser collapses heading whitespace, so the mutant still
    parses as the ontology section there; the project parser accepts only the
    canonical and single-spaced spellings, so its digest loses the ontology
    bindings and the comparison must report the divergence.
    """
    project = spec_digest(parse_gnn_file(upstream_run.mutant))
    upstream = normalize_upstream_digest(upstream_run.payload["specs"][str(upstream_run.mutant.resolve())])
    assert project["ontology"] == {}
    assert upstream["ontology"] == spec_digest(parse_gnn_file(GNN_DIR / "bernoulli_toy.gnn.md"))["ontology"]
    assert any(issue.startswith("ontology:") for issue in digest_divergences(project, upstream))


def test_digest_comparison_rejects_malformed_digests() -> None:
    """A digest field of the wrong shape is an explicit error, not a silent pass."""
    with pytest.raises(UpstreamConformanceError, match="must be a mapping"):
        digest_divergences({"variables": []}, {})
    with pytest.raises(UpstreamConformanceError, match="missing fields"):
        normalize_upstream_digest({"model_name": "x"})
    with pytest.raises(UpstreamConformanceError, match="must be a sequence"):
        normalize_upstream_digest(
            {
                "model_name": "x",
                "version": "1.1",
                "time": "",
                "variables": {},
                "connections": [],
                "ontology": [],
                "model_parameters": {},
                "parameters": {},
            }
        )


def test_digest_comparison_flags_every_field_family() -> None:
    """Each digest field family reports its own divergence."""
    base = {
        "model_name": "M",
        "version": "1.1",
        "time": "Static",
        "variables": {"a": {"dims": [2], "dtype": "float"}},
        "connections": [["a", "b", "directed", ""]],
        "ontology": {"a": "Term"},
        "model_parameters": {"num_states": "2"},
        "parameters": {"a": [0.5, 0.5]},
    }
    assert digest_divergences(base, dict(base)) == []
    mutations = {
        "model_name": {**base, "model_name": "N"},
        "version": {**base, "version": "1.0"},
        "time": {**base, "time": "Dynamic"},
        "variables": {**base, "variables": {"a": {"dims": [3], "dtype": "float"}}},
        "connections": {**base, "connections": []},
        "ontology": {**base, "ontology": {}},
        "model_parameters": {**base, "model_parameters": {"num_states": "3"}},
        "parameters": {**base, "parameters": {"a": [0.4, 0.6]}},
    }
    for field, mutated in mutations.items():
        issues = digest_divergences(base, mutated)
        assert issues, f"expected a divergence for {field}"
    # Direction tokens compare semantically, not by serialization style.
    assert digest_divergences(base, {**base, "connections": [["a", "b", "DIRECTED", ""]]}) == []


def test_time_digest_classifies_like_upstream() -> None:
    """Time sections classify to Static/Dynamic the way upstream records them."""
    spec_text = """## GNNSection

S

## GNNVersionAndFlags

GNN v1.1

## ModelName

M

## StateSpaceBlock

a[2,type=float]

## Connections

a>a

## Time

{time}

## ActInfOntologyAnnotation

a=Term
"""
    from gnn.parser import parse_gnn

    for body, expected in (("Static", "Static"), ("Dynamic", "Dynamic"), ("", "Static"), ("dynamic", "Dynamic")):
        digest = spec_digest(parse_gnn(spec_text.format(time=body)))
        assert digest["time"] == expected


def test_normalize_upstream_digest_maps_enums_and_sequences() -> None:
    """Enum names, one-element lists, and duplicate-free mappings normalize cleanly."""
    payload = {
        "model_name": " M ",
        "version": "GNN v1.1",
        "time": "",
        "variables": [{"name": "a", "dims": [2, 1], "dtype": "DataType.INTEGER"}],
        "connections": [["a", "b", "ConnectionType.DIRECTED", None]],
        "ontology": [{"variable": "a", "term": "Term"}],
        "model_parameters": {"num_states": "2"},
        "parameters": {"a": [[0.5], [0.5]]},
    }
    digest = normalize_upstream_digest(payload)
    assert digest["model_name"] == "M"
    assert digest["version"] == "1.1"
    assert digest["time"] == "Static"
    assert digest["variables"] == {"a": {"dims": [2, 1], "dtype": "int"}}
    assert digest["connections"] == [["a", "b", "directed", ""]]
    assert digest["ontology"] == {"a": "Term"}
