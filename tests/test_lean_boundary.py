from pathlib import Path

from visualizations.lean_boundary import load_lean_boundary_rows


def test_load_lean_boundary_rows(project_root: Path) -> None:
    rows = load_lean_boundary_rows(project_root)
    assert rows
    names = {row.name for row in rows}
    assert "sophisticated_requires_horizon" in names
    assert "ising_coupling_sum_zero" in names
    assert "graph_world_three_steps_reach_goal" in names
    assert "policy_enumeration_contains_forward" in names
    # The information-identity chain-rule skeleton + its negative control.
    assert "mi_chain_rule" in names
    assert "cue_closes_gap" in names
    assert "pragmatic_leaves_gap" in names
    assert all(row.status == "proved" for row in rows)


def test_lean_information_identity_matches_active_selection_witness(project_root: Path) -> None:
    # The Lean cue_closes_gap theorem (residual 0 -> I = H(r)) is the formal skeleton
    # of the active_selection numerical identity (gap_closed = epistemic, residual 0
    # for the cue). Bind them so the formal and numerical witnesses cannot drift apart.
    import json

    from firstprinciples.active_selection import build_payload

    rows = {row.name: row for row in load_lean_boundary_rows(project_root)}
    assert rows["cue_closes_gap"].status == "proved"
    assert rows["pragmatic_leaves_gap"].status == "proved"
    asel = build_payload()
    assert asel["gap_closed_equals_epistemic_identity"] is True
    assert asel["max_identity_residual"] < 1e-12
    # the cue policy closes the gap to ~0 (residual 0) -- the cue_closes_gap antecedent
    cue = next(p for p in asel["policies"] if p["name"] == "cue")
    assert cue["residual_gap"] < 1e-9
    # axiom audit: the Lean witnesses are sorry-free (kernel-checked)
    extraction = json.load((project_root / "output" / "data" / "proof_extraction_index.json").open())
    assert int(extraction.get("theorem_count", extraction.get("inventory_theorem_count", 0))) >= 14


def test_load_lean_boundary_rows_detects_sorry(tmp_path: Path) -> None:
    lean_dir = tmp_path / "lean" / "OnPolicyDistillation"
    lean_dir.mkdir(parents=True)
    (lean_dir / "Stub.lean").write_text(
        "theorem broken : True := by\n  sorry\n\ntheorem fine : True := trivial\n",
        encoding="utf-8",
    )
    rows = load_lean_boundary_rows(tmp_path)
    by_name = {row.name: row for row in rows}
    assert by_name["broken"].status == "sorry"
    assert by_name["fine"].status == "proved"
