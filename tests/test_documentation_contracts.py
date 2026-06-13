"""Documentation contract checks for reproducibility-facing references."""

from __future__ import annotations

from pathlib import Path

from visualizations.figure_registry import load_figure_registry

DOC_CONTRACT_SUFFIXES = {".bib", ".lean", ".md", ".py", ".toml", ".yaml", ".yml"}
DOC_FILENAMES = {"AGENTS.md", "README.md"}
IGNORED_DIR_NAMES = {
    ".benchmarks",
    ".git",
    ".lake",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "htmlcov",
    "output",
}


def _ignored_repo_path(path: Path, project_root: Path) -> bool:
    rel = path.relative_to(project_root)
    return any(
        part in IGNORED_DIR_NAMES or part.endswith(".egg-info") for part in rel.parts
    )


def _repo_doc_contract_dirs(project_root: Path) -> list[Path]:
    required: set[Path] = set()
    for path in project_root.rglob("*"):
        if not path.is_file() or _ignored_repo_path(path, project_root):
            continue
        if path.name in DOC_FILENAMES or path.suffix not in DOC_CONTRACT_SUFFIXES:
            continue
        parent = path.parent
        while True:
            if not _ignored_repo_path(parent, project_root):
                required.add(parent)
            if parent == project_root:
                break
            parent = parent.parent
    return sorted(required)


def _relative_doc_path(path: Path, project_root: Path) -> str:
    rel = path.relative_to(project_root)
    return path.name if rel == Path(".") else str(rel)


def test_meaningful_project_dirs_have_agents_and_readme(project_root: Path) -> None:
    missing: list[str] = []
    for directory in _repo_doc_contract_dirs(project_root):
        for filename in sorted(DOC_FILENAMES):
            doc = directory / filename
            if not doc.is_file():
                rel_dir = directory.relative_to(project_root)
                prefix = "" if rel_dir == Path(".") else f"{rel_dir}/"
                missing.append(f"{prefix}{filename}")

    assert not missing, "missing local documentation contracts: " + ", ".join(missing)


def test_lean_docs_and_config_use_current_module_name(project_root: Path) -> None:
    surfaces = [
        project_root / "AGENTS.md",
        project_root / "tracks.yaml",
        project_root / "lean" / "README.md",
        project_root / "lean" / "OnPolicyDistillation" / "README.md",
        project_root / "lean" / "lake-manifest.json",
    ]
    for path in surfaces:
        text = path.read_text(encoding="utf-8")
        assert "TemplateActiveInference" not in text, _relative_doc_path(path, project_root)
        assert "OnPolicyDistillation" in text, _relative_doc_path(path, project_root)


def test_source_docs_include_firstprinciples_package(project_root: Path) -> None:
    for path in (project_root / "src" / "README.md", project_root / "src" / "AGENTS.md"):
        text = path.read_text(encoding="utf-8")
        assert "firstprinciples/" in text


def test_imrad_docs_use_local_validation_contracts(project_root: Path) -> None:
    for path in (project_root / "manuscript" / "sections" / "imrad").rglob("*"):
        if path.name not in DOC_FILENAMES:
            continue
        text = path.read_text(encoding="utf-8")
        assert "infrastructure.validation.evidence_registry" not in text
        assert "manuscript injection / rendering pipeline" not in text


def test_rendering_reproducibility_reference_is_signposted(project_root: Path) -> None:
    docs_readme = (project_root / "docs" / "README.md").read_text(encoding="utf-8")
    project_readme = (project_root / "README.md").read_text(encoding="utf-8")
    reference = project_root / "docs" / "reference" / "rendering-reproducibility.md"

    assert "rendering-reproducibility.md" in docs_readme
    assert "rendering-reproducibility.md" in project_readme
    assert reference.is_file()

    text = reference.read_text(encoding="utf-8")
    for phrase in (
        "single hydration boundary",
        "Generated artifacts",
        "Authored surfaces",
        "Root output parity",
        "Figure rendering contract",
    ):
        assert phrase in text


def test_readiness_docs_signpost_canonical_chain_and_soak_validator(project_root: Path) -> None:
    project_readme = (project_root / "README.md").read_text(encoding="utf-8")
    config_guide = (project_root / "docs" / "reference" / "configuration-and-extension.md").read_text(
        encoding="utf-8"
    )

    assert "scripts/run_full_chain.py --render" in project_readme
    assert "manuscript/config.yaml" in project_readme
    assert "run_test_isolation_soak.py --validate-report" in config_guide
    assert "--require-complete" in config_guide
    assert "scripts/audit_roadmap_tasks.py" in config_guide
    assert "`tasks.yaml`" in config_guide
    assert "taskboard surface" in config_guide


def test_public_docs_list_every_registered_current_figure(project_root: Path) -> None:
    registry = load_figure_registry(project_root)
    surfaces = {
        "README.md": (project_root / "README.md").read_text(encoding="utf-8"),
        "AGENTS.md": (project_root / "AGENTS.md").read_text(encoding="utf-8"),
        "manuscript/SYNTAX.md": (project_root / "manuscript" / "SYNTAX.md").read_text(encoding="utf-8"),
    }
    for surface, text in surfaces.items():
        for figure_id in registry:
            assert figure_id in text, f"{surface} does not mention registered figure {figure_id}"


def test_public_docs_pin_canonical_si_artifacts_without_legacy_modes(project_root: Path) -> None:
    surfaces = [
        (project_root / "README.md").read_text(encoding="utf-8"),
        (project_root / "AGENTS.md").read_text(encoding="utf-8"),
        (project_root / "docs" / "AGENTS.md").read_text(encoding="utf-8"),
    ]
    combined = "\n".join(surfaces)
    for phrase in (
        "full_tmaze_sophisticated_inference",
        "sophisticated_inference",
        "si_tmaze_summary.json",
        "si_tmaze_model_matrices.json",
        "pymdp_policy_posterior_grid.json",
        "pymdp_runtime_diagnostics.json",
        "vanilla planning is comparison-only",
    ):
        assert phrase in combined
    for stale in ("--mode", "state_inference", "policy_inference", "pymdp_mode"):
        assert stale not in combined


def test_public_docs_use_working_lifecycle_paths(project_root: Path) -> None:
    """Reader-facing docs must not drift back to template or active lifecycle paths."""
    surfaces = [
        project_root / "README.md",
        project_root / "STANDALONE.md",
        project_root / "AGENTS.md",
        project_root / "docs" / "README.md",
        project_root / "docs" / "AGENTS.md",
        project_root / "docs" / "reference" / "README.md",
        project_root / "docs" / "reference" / "AGENTS.md",
        project_root / "docs" / "reference" / "rendering-reproducibility.md",
        project_root / "manuscript" / "sheaf" / "README.md",
        project_root / "tests" / "AGENTS.md",
        project_root / "src" / "validation_spine" / "AGENTS.md",
    ]
    forbidden = (
        "projects/active/active_inference_on_policy_distillation",
        "active/active_inference_on_policy_distillation",
        "projects/templates/template_active_inference",
        "template_active_inference",
        "output/templates/active_inference_on_policy_distillation",
        "--project active_inference_on_policy_distillation",
    )
    for path in surfaces:
        text = path.read_text(encoding="utf-8")
        for stale in forbidden:
            assert stale not in text, f"{path.relative_to(project_root)} contains stale path {stale}"

    assert "working/active_inference_on_policy_distillation" in (
        project_root / "README.md"
    ).read_text(encoding="utf-8")
