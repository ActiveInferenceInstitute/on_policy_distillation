from pathlib import Path

import pytest

from gnn.parser import GNNParseError, parse_gnn_file
from gnn.concordance import concordance_holds, parity_gaps

ROOT = Path(__file__).resolve().parents[1]
TOY = ROOT / "gnn" / "bernoulli_toy.gnn.md"


def test_parse_bernoulli_toy() -> None:
    model = parse_gnn_file(TOY)
    assert model.has("J")
    assert model.ontology["J"] == "CrossStreamCouplingPotential"


def test_concordance_holds_for_toy() -> None:
    model = parse_gnn_file(TOY)
    assert concordance_holds(model)


def test_missing_section_raises() -> None:
    from gnn.parser import parse_gnn

    with pytest.raises(GNNParseError):
        parse_gnn("## GNNSection\nonly\n")


def test_parity_gaps_when_ontology_incomplete() -> None:
    from dataclasses import replace

    model = parse_gnn_file(TOY)
    broken = replace(model, ontology={k: v for k, v in model.ontology.items() if k != "J"})
    gaps = parity_gaps(broken)
    assert any("J" in g for g in gaps)


def test_gnn_roundtrip_detects_lossy_payload(project_root: Path) -> None:
    """The GNN round-trip must FAIL on an unrepresentable field (not be a dict==itself tautology)."""
    from roadmap_tracks.formal_interop import _gnn_paths, _model_payload, roundtrip_payload_lossless

    paths = _gnn_paths(project_root)
    assert paths, "expected at least one .gnn.md file"
    payload = _model_payload(paths[0])
    # Clean real payload round-trips losslessly through GNN text.
    assert roundtrip_payload_lossless(payload) is True
    # A connection label with whitespace cannot survive the `\\w+` edge grammar:
    # serializing and re-parsing must report a loss, proving the gate is not vacuous.
    assert payload["connections"], "expected connections in the toy model"
    corrupted = {**payload, "connections": [dict(payload["connections"][0]), *payload["connections"][1:]]}
    corrupted["connections"][0]["label"] = "bad label"
    assert roundtrip_payload_lossless(corrupted) is False


# --- _parse_param_blocks unit coverage (Run-6, AI-HYGIENE-1) -----------------


def test_parse_param_blocks_happy_path() -> None:
    from gnn.parser import _parse_param_blocks

    body = """
A = {(0.9, 0.1), (0.1, 0.9)}
b = {0.5, 0.5}
"""
    params = _parse_param_blocks(body)
    assert set(params) == {"A", "b"}
    assert params["A"].shape == (2, 2)
    assert abs(float(params["A"][0, 0]) - 0.9) < 1e-12
    assert params["b"].shape == (2,)


def test_parse_param_blocks_unbalanced_braces_raise() -> None:
    import pytest as _pytest

    from gnn.parser import GNNParseError, _parse_param_blocks

    with _pytest.raises(GNNParseError, match="unbalanced braces"):
        _parse_param_blocks("A = {(0.9, 0.1), (0.1, 0.9)")


def test_parse_param_blocks_empty_and_comment_only_bodies() -> None:
    from gnn.parser import _parse_param_blocks

    assert _parse_param_blocks("") == {}
    assert _parse_param_blocks("# only a comment line\n# another\n") == {}


def test_parse_param_blocks_skips_comment_lines_between_blocks() -> None:
    from gnn.parser import _parse_param_blocks

    body = """
# C = {9.0, 9.0}  (commented out -- must NOT be parsed)
D = {0.25, 0.75}
"""
    params = _parse_param_blocks(body)
    assert set(params) == {"D"}
    assert abs(float(params["D"][1]) - 0.75) < 1e-12
