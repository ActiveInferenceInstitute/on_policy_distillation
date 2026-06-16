"""Fast tests for deterministic artifact writer call structure."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def test_write_sheaf_track_artifacts_writes_each_generated_path_once(monkeypatch, tmp_path: Path) -> None:
    import manuscript.sheaf.semantic as semantic
    import manuscript.sheaf.status as status
    import roadmap_tracks
    import roadmap_tracks.scholarship as scholarship
    import roadmap_tracks.sheaf_tracks as sheaf_tracks
    import roadmap_tracks.supplemental as supplemental

    calls: Counter[str] = Counter()

    def payload(name: str):
        def _build(root: Path) -> dict[str, object]:
            calls[f"build:{name}"] += 1
            return {"schema": name}

        return _build

    for name in (
        "build_adversarial_audit",
        "build_artifact_provenance",
        "build_blocked_scope_manifest",
        "build_counterexample_matrix",
        "build_evidence_field_index",
        "build_interop_roundtrip_report",
        "build_model_checking_witnesses",
        "build_release_bundle_manifest",
        "build_replay_matrix",
        "build_sensitivity_sweep",
        "build_theorem_traceability_matrix",
        "build_track_improvement_scope",
        "build_uncertainty_summary",
        "build_validation_dependency_graph",
    ):
        monkeypatch.setattr(sheaf_tracks, name, payload(name))

    def fake_write_json(path: Path, data: dict[str, object]) -> Path:
        rel = path.relative_to(tmp_path).as_posix()
        calls[f"json:{rel}"] += 1
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def phase(name: str):
        def _write(root: Path) -> dict[str, Path]:
            calls[name] += 1
            path = root / "output" / "data" / f"{name}.json"
            return {name: fake_write_json(path, {"schema": name})}

        return _write

    monkeypatch.setattr(sheaf_tracks, "_write_json", fake_write_json)
    monkeypatch.setattr(sheaf_tracks, "_refresh_hydrated_manuscript", lambda root: calls.update(["hydrate"]))
    monkeypatch.setattr(roadmap_tracks, "write_toy_sweep_artifacts", phase("toy"))
    monkeypatch.setattr(roadmap_tracks, "write_formal_interop_artifacts", phase("formal"))
    monkeypatch.setattr(roadmap_tracks, "write_integration_audit_artifacts", phase("audit"))
    monkeypatch.setattr(
        scholarship,
        "write_scholarship_source_matrix",
        lambda root: fake_write_json(root / "output" / "data" / "scholarship_source_matrix.json", {"schema": "scholarship"}),
    )
    monkeypatch.setattr(
        supplemental,
        "write_supplemental_artifacts",
        lambda root: {
            "release_attestation": fake_write_json(
                root / "output" / "reports" / "release_attestation.json",
                {"schema": "release_attestation"},
            )
        },
    )
    monkeypatch.setattr(
        status,
        "write_sheaf_status_outputs",
        lambda root: {
            "section_status": fake_write_json(
                root / "output" / "data" / "sheaf_section_status_matrix.json",
                {"schema": "section_status"},
            )
        },
    )
    monkeypatch.setattr(semantic, "build_evidence_crosswalk", payload("crosswalk"))
    monkeypatch.setattr(semantic, "build_semantic_gluing_certificate", payload("semantic"))
    monkeypatch.setattr(semantic, "_with_proof_obligations", lambda root, data: data)

    paths = sheaf_tracks.write_sheaf_track_artifacts(tmp_path, refresh_dependencies=True, refresh_hydration=True)

    assert paths["semantic"] == tmp_path / "output" / "data" / "sheaf_gluing_certificate.json"
    assert calls["toy"] == 1
    assert calls["formal"] == 1
    assert calls["audit"] == 1
    assert calls["hydrate"] == 1
    assert all(count == 1 for key, count in calls.items() if key.startswith("json:"))


def test_write_semantic_gluing_outputs_emits_one_status_supplement_and_certificate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    import manuscript.sheaf.semantic as semantic
    import manuscript.sheaf.status as status
    import roadmap_tracks.supplemental as supplemental

    calls: Counter[str] = Counter()

    monkeypatch.setattr(semantic, "_refresh_hydrated_manuscript", lambda root: calls.update(["hydrate"]))
    monkeypatch.setattr(
        status,
        "write_sheaf_status_outputs",
        lambda root: calls.update(["status"]) or {"section_status": root / "output" / "data" / "status.json"},
    )
    monkeypatch.setattr(supplemental, "write_supplemental_artifacts", lambda root: calls.update(["supplement"]) or {})
    monkeypatch.setattr(
        semantic,
        "build_evidence_crosswalk",
        lambda root: calls.update(["crosswalk"]) or {"schema": "crosswalk"},
    )
    monkeypatch.setattr(
        semantic,
        "build_validation_dependency_graph",
        lambda root: calls.update(["dependency"]) or {"schema": "dependency"},
    )
    monkeypatch.setattr(
        semantic,
        "build_semantic_gluing_certificate",
        lambda root: calls.update(["certificate"]) or {"schema": "certificate"},
    )
    monkeypatch.setattr(semantic, "_with_proof_obligations", lambda root, data: data)

    paths = semantic.write_semantic_gluing_outputs(tmp_path, refresh_hydration=True)

    assert paths["certificate"].read_text(encoding="utf-8")
    assert calls == Counter(
        {
            "hydrate": 1,
            "status": 1,
            "supplement": 1,
            "crosswalk": 1,
            "dependency": 1,
            "certificate": 1,
        }
    )
