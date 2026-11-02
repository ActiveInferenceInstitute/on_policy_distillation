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
    UpstreamPin,
    UpstreamPinError,
    checkout_available,
    default_gnn_root,
    digest_divergences,
    gnn_checkout_python,
    load_upstream_pin,
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
CANONICAL_TAG = "v5.0.3"
CANONICAL_COMMIT = "8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1"


@dataclass(frozen=True)
class UpstreamRun:
    """One execution of the pinned upstream parser over the shipped specs."""

    pin: UpstreamPin
    root: Path
    payload: dict[str, Any]
    mutant: Path
    extract_dir: Path


@pytest.fixture(scope="module")
def upstream_run(tmp_path_factory: pytest.TempPathFactory) -> UpstreamRun:
    """Execute the pinned upstream parser on every shipped spec + a leniency mutant."""
    pin = load_upstream_pin(PIN_PATH)
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
        ["git", "-C", str(root), "cat-file", "-e", f"{pin.commit}^{{commit}}"],
        capture_output=True,
        text=True,
    )
    assert presence.returncode == 0, (
        f"pinned commit {pin.commit} is not present in {root}; fetch the pinned release before "
        "running the upstream conformance check"
    )

    extract_dir = tmp_path_factory.mktemp("gnn_upstream_pin")
    archive = subprocess.run(
        ["git", "-C", str(root), "archive", pin.commit, "src/gnn"],
        check=True,
        capture_output=True,
    )
    with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as stream:
        if sys.version_info >= (3, 12):
            stream.extractall(extract_dir, filter="data")
        else:  # pragma: no cover - the documented gate runs a modern interpreter
            stream.extractall(extract_dir)

    # Leniency mutant: the spaced section name is ignored by the upstream
    # parser (canonical inventory: `## ActInfOntologyAnnotation`), while the
    # project parser accepts both spellings. Used as the non-vacuity control.
    mutant = extract_dir / "spaced_ontology.gnn.md"
    mutant.write_text(
        (GNN_DIR / "bernoulli_toy.gnn.md")
        .read_text(encoding="utf-8")
        .replace("## ActInfOntologyAnnotation", "## ActInf Ontology Annotation"),
        encoding="utf-8",
    )

    spec_paths = [str(path.resolve()) for path in SHIPPED_SPECS] + [str(mutant)]
    env = {**os.environ, "PYTHONPATH": str(extract_dir / "src")}
    parser_module, parser_class = pin.parser_entry_point()
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
    """The shipped pin is the canonical workstream pin (v5.0.3)."""
    pin = load_upstream_pin(PIN_PATH)
    assert pin.tag == CANONICAL_TAG
    assert pin.commit == CANONICAL_COMMIT
    assert pin.version == "5.0.3"
    assert pin.date_recorded == "2026-11-01"
    assert pin.parser_entry_point() == ("gnn.parsers.markdown_parser", "MarkdownGNNParser")


@pytest.mark.parametrize(
    "mutate, message",
    [
        (
            lambda data: {k: v for k, v in data.items() if k != "commit"},
            "complete Git object identity|must declare",
        ),
        (lambda data: {k: v for k, v in data.items() if k != "version"}, "must declare"),
        (lambda data: {k: v for k, v in data.items() if k != "date_recorded"}, "must declare"),
        (lambda data: {**data, "repository": "git@github.com:x/y.git"}, "HTTPS GitHub URL"),
        (lambda data: {**data, "tag": "5.0.3"}, "stable version"),
        (lambda data: {**data, "tag": "v5.0.4"}, "same release"),
        (lambda data: {**data, "version": "5.0"}, "release version"),
        (lambda data: {**data, "date_recorded": "2026-13-01"}, "ISO date"),
        (lambda data: {**data, "commit": "abc123"}, "complete Git object identity"),
        (lambda data: {**data, "parser_module": "markdown_parser"}, "dotted import path"),
        (lambda data: {**data, "parser_class": "not a class"}, "Python identifier"),
        (lambda data: {**data, "tag": 503}, "fields must be strings"),
    ],
)
def test_pin_loader_rejects_malformed_pins(tmp_path: Path, mutate: Any, message: str) -> None:
    """Every malformed pin shape is refused with a targeted error."""
    data = json.loads(PIN_PATH.read_text(encoding="utf-8"))
    broken = tmp_path / "upstream.json"
    broken.write_text(json.dumps(mutate(data)), encoding="utf-8")
    with pytest.raises(UpstreamPinError, match=message):
        load_upstream_pin(broken)


def test_pin_loader_keeps_extra_fields_and_accepts_a_tagless_core(tmp_path: Path) -> None:
    """Extra keys live in ``extras``; the parser entry point is optional."""
    data = json.loads(PIN_PATH.read_text(encoding="utf-8"))
    minimal = {key: data[key] for key in ("repository", "commit", "version", "date_recorded")}
    minimal["checkout_hint"] = {"sibling": "Generalized_Notation_Notation"}
    path = tmp_path / "upstream.json"
    path.write_text(json.dumps(minimal), encoding="utf-8")
    pin = load_upstream_pin(path)
    assert pin.tag is None
    assert pin.parser_module is None
    assert pin.extras == {"checkout_hint": {"sibling": "Generalized_Notation_Notation"}}
    with pytest.raises(UpstreamPinError, match="parser entry point"):
        pin.parser_entry_point()


def test_pin_loader_rejects_duplicate_keys(tmp_path: Path) -> None:
    """A pin with a duplicated field is ambiguous and refused."""
    text = PIN_PATH.read_text(encoding="utf-8").replace(
        '"commit":', '"commit": "8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1",\n  "commit":', 1
    )
    broken = tmp_path / "upstream.json"
    broken.write_text(text, encoding="utf-8")
    with pytest.raises(UpstreamPinError, match="duplicate"):
        load_upstream_pin(broken)


def test_pin_loader_reports_missing_file(tmp_path: Path) -> None:
    """A missing pin file is an explicit error, not an empty pin."""
    with pytest.raises(UpstreamPinError, match="cannot read upstream pin"):
        load_upstream_pin(tmp_path / "absent.json")


def test_resolve_gnn_root_honours_explicit_selection(tmp_path: Path) -> None:
    """An explicit checkout selection is final; an empty selection is refused."""
    chosen = tmp_path / "gnn"
    chosen.mkdir()
    assert resolve_gnn_root(PROJECT_ROOT, {ENV_UPSTREAM_ROOT: str(chosen)}) == chosen.resolve()
    assert resolve_gnn_root(PROJECT_ROOT, {}) == default_gnn_root(PROJECT_ROOT)
    with pytest.raises(UpstreamPinError, match="must not be empty"):
        resolve_gnn_root(PROJECT_ROOT, {ENV_UPSTREAM_ROOT: "  "})


def test_upstream_parser_ran_from_the_pinned_commit(upstream_run: UpstreamRun) -> None:
    """The executed parser module is the extracted pinned release, not the live tree."""
    parser_info = upstream_run.payload["parser"]
    assert parser_info["module"] == upstream_run.pin.parser_module
    assert parser_info["class"] == upstream_run.pin.parser_class
    parser_file = Path(parser_info["file"]).resolve()
    assert parser_file.is_relative_to(upstream_run.extract_dir.resolve())
    assert parser_info["gnn_version"] == "5.0.3"


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
    """Non-vacuity control: the spaced ontology heading is invisible to upstream.

    The project parser accepts the historical spaced spelling; the upstream
    parser does not read it, so the mutant's digest must lose its ontology
    bindings and the comparison must report the divergence.
    """
    project = spec_digest(parse_gnn_file(upstream_run.mutant))
    upstream = normalize_upstream_digest(upstream_run.payload["specs"][str(upstream_run.mutant.resolve())])
    assert project["ontology"] == spec_digest(parse_gnn_file(GNN_DIR / "bernoulli_toy.gnn.md"))["ontology"]
    assert upstream["ontology"] == {}
    assert any(issue.startswith("ontology:") for issue in digest_divergences(project, upstream))


def test_digest_comparison_rejects_malformed_digests() -> None:
    """A digest field of the wrong shape is an explicit error, not a silent pass."""
    with pytest.raises(UpstreamPinError, match="must be a mapping"):
        digest_divergences({"variables": []}, {})
    with pytest.raises(UpstreamPinError, match="missing fields"):
        normalize_upstream_digest({"model_name": "x"})
    with pytest.raises(UpstreamPinError, match="must be a sequence"):
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
