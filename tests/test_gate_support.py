"""Tests for generated gate-artifact bootstrap caching."""

from __future__ import annotations

from pathlib import Path


def test_ensure_gate_artifacts_uses_existing_valid_artifacts(monkeypatch, tmp_path: Path) -> None:
    import gate_support

    root = tmp_path.resolve()
    calls = {"refresh": 0}

    monkeypatch.setattr(gate_support, "_gate_artifacts_present", lambda project_root: True)

    def fail_refresh(project_root: Path) -> None:
        calls["refresh"] += 1
        raise AssertionError("valid artifacts should not be refreshed")

    monkeypatch.setattr(gate_support, "refresh_gate_artifacts", fail_refresh)
    gate_support._BOOTSTRAPPED_ROOTS.discard(root)

    gate_support.ensure_gate_artifacts(root)

    assert calls["refresh"] == 0
    assert root in gate_support._BOOTSTRAPPED_ROOTS


def test_refresh_generated_gate_artifacts_warms_cache_after_full_refresh(monkeypatch, tmp_path: Path) -> None:
    import gate_support

    root = tmp_path.resolve()
    calls = {"refresh": 0}

    monkeypatch.setattr(gate_support, "_gate_artifacts_present", lambda project_root: False)

    def refresh(project_root: Path, *, require_analysis_outputs: bool) -> dict[str, Path]:
        calls["refresh"] += 1
        assert require_analysis_outputs is False
        return {}

    monkeypatch.setattr(gate_support, "refresh_gate_artifacts", refresh)
    gate_support._BOOTSTRAPPED_ROOTS.discard(root)

    gate_support.refresh_generated_gate_artifacts(root)

    assert calls["refresh"] == 1
    assert root in gate_support._BOOTSTRAPPED_ROOTS


def test_ensure_gate_artifacts_verify_bypasses_warm_cache(monkeypatch, tmp_path: Path) -> None:
    import gate_support

    root = tmp_path.resolve()
    calls = {"ready": 0}

    monkeypatch.setattr(gate_support, "_gate_artifacts_present", lambda project_root: True)

    def ready(project_root: Path, *, include_manuscript: bool = False) -> bool:
        calls["ready"] += 1
        assert include_manuscript is True
        return True

    monkeypatch.setattr(gate_support, "_gate_artifacts_ready", ready)
    gate_support._BOOTSTRAPPED_ROOTS.add(root)

    gate_support.ensure_gate_artifacts(root, verify=True)

    assert calls["ready"] == 1
    assert root in gate_support._BOOTSTRAPPED_ROOTS


def test_ensure_gate_artifacts_revalidates_changed_bootstrap_fingerprint(monkeypatch, tmp_path: Path) -> None:
    import gate_support

    root = tmp_path.resolve()
    calls = {"ready": 0}

    monkeypatch.setattr(gate_support, "_gate_artifacts_present", lambda project_root: True)
    monkeypatch.setattr(gate_support, "_gate_artifact_fingerprint", lambda project_root: (("artifact", calls["ready"], 1),))

    def ready(project_root: Path, *, include_manuscript: bool = False) -> bool:
        calls["ready"] += 1
        assert include_manuscript is True
        return True

    monkeypatch.setattr(gate_support, "_gate_artifacts_ready", ready)
    gate_support._BOOTSTRAPPED_ROOTS.add(root)
    gate_support._BOOTSTRAPPED_FINGERPRINTS[root] = (("artifact", -1, 1),)

    gate_support.ensure_gate_artifacts(root)

    assert calls["ready"] == 1
    assert gate_support._BOOTSTRAPPED_FINGERPRINTS[root] == (("artifact", 1, 1),)
