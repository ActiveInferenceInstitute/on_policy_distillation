"""Real-byte publish-bookend custody and clause-local scope regressions."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from PIL import Image

from gates.aggregate_rederivation import ARTIFACT_AGGREGATE_RULES, aggregate_rederivation_rows, rederive_aggregate
from gates.output_checks import validate_outputs_selected_strict
from roadmap_tracks.integration_audit_artifacts import (
    _figure_hash_rows_complete,
    _scope_forbidden_hits,
    build_figure_hash_manifest,
    build_scope_boundary_audit,
)

_MANIFEST = "output/reports/figure_hash_manifest.json"


def _images(root: Path) -> None:
    (root / "figures.yaml").write_text(
        "figures:\n  finite_fixture:\n    filename: finite_fixture.png\n"
        "    alt: A two-state finite fixture\n    caption: A finite fixture.\n",
        encoding="utf-8",
    )
    directory = root / "output/figures"
    directory.mkdir(parents=True)
    image = Image.new("RGB", (2, 2), color=(255, 255, 255))
    image.putpixel((0, 0), (0, 0, 0))
    image.save(directory / "finite_fixture.png")
    image.save(directory / "si_belief_trajectory.gif", format="GIF")


def _save(root: Path, payload: dict) -> None:
    path = root / _MANIFEST
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _assert_gate(root: Path, expected: bool) -> None:
    assert validate_outputs_selected_strict(root, {"figure_hash_manifest_schema"}) == {
        "figure_hash_manifest_schema": expected,
    }
    row = next(row for row in aggregate_rederivation_rows(root) if row["artifact"] == _MANIFEST)
    assert row["consistent"] is expected


def test_only_genuinely_absent_publish_bookends_defer(tmp_path: Path) -> None:
    _images(tmp_path)
    payload = build_figure_hash_manifest(tmp_path)
    deferred = [row for row in payload["rows"] if row["deferred"]]
    assert {row["path"] for row in deferred} == {
        "output/figures/transmission_integrity_strip.png",
        "output/figures/transmission_pairing.png",
    }
    assert all(not (tmp_path / row["path"]).exists() for row in deferred)
    assert _figure_hash_rows_complete(tmp_path, payload)
    _save(tmp_path, payload)
    _assert_gate(tmp_path, True)
    spec = ARTIFACT_AGGREGATE_RULES[_MANIFEST][0][1]
    assert rederive_aggregate(payload, spec, project_root=tmp_path)


@pytest.mark.parametrize(
    "mutation",
    [
        "ordinary_deferred",
        "present_bookend_deferred",
        "present_hash",
        "present_size",
        "changed_bytes",
        "absent_forged_hash",
        "duplicate_row",
    ],
)
def test_forged_deferral_and_stale_present_images_fail(tmp_path: Path, mutation: str) -> None:
    _images(tmp_path)
    bookend = tmp_path / "output/figures/transmission_pairing.png"
    Image.new("RGB", (3, 2), color=(10, 20, 30)).save(bookend)
    baseline = build_figure_hash_manifest(tmp_path)
    _save(tmp_path, baseline)
    _assert_gate(tmp_path, True)
    payload = deepcopy(baseline)
    row = next(row for row in payload["rows"] if row["path"] == bookend.relative_to(tmp_path).as_posix())
    if mutation == "ordinary_deferred":
        row = next(row for row in payload["rows"] if row["path"].endswith("finite_fixture.png"))
        (tmp_path / row["path"]).unlink()
        row.update({"exists": False, "fresh": False, "sha256": "", "size_bytes": 0, "deferred": True})
    elif mutation == "present_bookend_deferred":
        row["deferred"] = True
    elif mutation == "present_hash":
        row["sha256"] = "0" * 64
    elif mutation == "present_size":
        row["size_bytes"] += 1
    elif mutation == "changed_bytes":
        Image.new("RGB", (3, 2), color=(30, 20, 10)).save(bookend)
    elif mutation == "absent_forged_hash":
        row = next(row for row in payload["rows"] if row["deferred"])
        row["sha256"] = "0" * 64
    else:
        payload["rows"].append(deepcopy(row))
    assert payload["all_hashes_present"] is True
    assert not _figure_hash_rows_complete(tmp_path, payload)
    _save(tmp_path, payload)
    _assert_gate(tmp_path, False)


@pytest.mark.parametrize(
    "text",
    [
        "This finite toy is illustrative; we measured production LLMs.",
        "We did not measure production LLMs; we measured production LLMs.",
        "We did not measure production LLMs and we measured production LLMs.",
        "This is not a universal theorem; we establish a general theorem.",
        "No biological data are used, but we use biological data.",
        "The finite toy is limited in scope: we validate Qwen results.",
        "We do not claim OPD = Active Inference, but OPD = Active Inference.",
        "We measured production LLMs, not finite toy models.",
        "This is a general theorem, not a finite illustration.",
        "No Markov blanket is biological and Markov blanket is physical.",
        "No biological Markov blanket is claimed and a biological boundary is established.",
    ],
)
def test_each_affirmative_scope_clause_is_rejected(tmp_path: Path, text: str) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "00_abstract.md").write_text(text, encoding="utf-8")
    hits = _scope_forbidden_hits(text)
    assert hits and any(not hit["negated"] for hit in hits)
    report = build_scope_boundary_audit(tmp_path)
    assert report["all_current_claims_toy"] is False
    assert report["scope_boundary_status"] == "scope_leak"
    assert report["violations"]


@pytest.mark.parametrize(
    "text",
    [
        "No universal theorem or general theorem is claimed.",
        "We did not measure production LLMs and did not validate Qwen results.",
        "No biological Markov blanket boundary claim is made; no biological data are used.",
        "We do not claim OPD = Active Inference; this is not a universal theorem.",
        "Qwen and Thinking Machines are external context, not reproduced results.",
    ],
)
def test_all_negated_guardrails_remain_legitimate(tmp_path: Path, text: str) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "00_abstract.md").write_text(text, encoding="utf-8")
    hits = _scope_forbidden_hits(text)
    assert hits and all(hit["negated"] for hit in hits)
    report = build_scope_boundary_audit(tmp_path)
    assert report["all_current_claims_toy"] is True
    assert report["violations"] == []


def test_explicit_future_file_policy_is_unchanged(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    for name in ("15_discussion_outlook.md", "17_conclusion.md"):
        (manuscript / name).write_text("We measured production LLMs.", encoding="utf-8")
    report = build_scope_boundary_audit(tmp_path)
    assert report["all_current_claims_toy"] is True
    assert all(row["allowed"] and row["forbidden_hits"] for row in report["rows"])


def test_selected_scope_gate_authenticates_current_clauses(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    source = manuscript / "00_abstract.md"
    source.write_text("We do not measure production LLMs.\n", encoding="utf-8")
    path = tmp_path / "output/reports/scope_boundary_audit.json"
    path.parent.mkdir(parents=True)
    baseline = build_scope_boundary_audit(tmp_path)
    path.write_text(json.dumps(baseline), encoding="utf-8")
    key = "scope_boundary_audit_schema"
    assert validate_outputs_selected_strict(tmp_path, {key}) == {key: True}
    source.write_text("This finite toy is illustrative; we measured production LLMs.\n", encoding="utf-8")
    assert baseline["all_current_claims_toy"] is True
    assert validate_outputs_selected_strict(tmp_path, {key}) == {key: False}
    assert validate_outputs_selected_strict(tmp_path, {key}, payloads={"scope_boundary": baseline}) == {key: False}
