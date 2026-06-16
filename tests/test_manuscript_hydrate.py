from pathlib import Path

import re

from manuscript.hydrate import format_variables, substitute_snake_case_tokens, write_resolved_manuscript
from manuscript.variables import generate_variables

_TOKEN_RE = re.compile(r"\{\{[a-z][a-z0-9_]*(?::[+]?\.\d+[efg])?\}\}")


def test_provenance_token_regex_matches_renderer_scientific_notation() -> None:
    # Regression: the provenance/staleness scanner regex must match the renderer's
    # format specs (e/f/g), or scientific-notation tokens ({{x:.1e}}) silently escape
    # token provenance and the hardcoded-variable audit (vacuous-green gates).
    from manuscript.hydrate import _TOKEN_RE as RENDER_RE
    from roadmap_tracks.integration_audit_builders import (
        TOKEN_MATCH_RE,
        TOKEN_RE,
        _expected_token_value,
    )

    text = "a {{alpha:.1e}} b {{beta:.3f}} c {{gamma:.2g}} d {{delta}}"
    rendered = {m.group(1) for m in RENDER_RE.finditer(text)}
    scanned = set(TOKEN_RE.findall(text))
    matched = {token for token, _spec in TOKEN_MATCH_RE.findall(text)}
    assert rendered == {"alpha", "beta", "gamma", "delta"}
    assert scanned == rendered, "provenance scanner must enumerate every rendered token"
    assert matched == rendered
    # expected value renders identically to the live renderer across format specs
    assert _expected_token_value("alpha", ":.1e", {"alpha": 4.44e-16}) == "4.4e-16"
    assert _expected_token_value("beta", ":.3f", {"beta": 0.0}) == "0.000"


def test_generate_variables_includes_structural_counts() -> None:
    root = Path(__file__).resolve().parents[1]
    vars_ = generate_variables(root, require_analysis_outputs=False)
    assert vars_["pipeline_track_count"] == 30
    assert vars_["sheaf_track_count"] == 33
    assert vars_["appendix_sheaf_track_count"] == 22
    assert vars_["appendix_sheaf_track_count"] < vars_["sheaf_track_count"]
    assert vars_["imrad_manifest_rows"] == 17
    assert vars_["composed_section_count"] == 12
    assert vars_["imrad_group_count"] == 5
    assert vars_["coverage_bound"] >= vars_["coverage_present"]


def test_format_variables_adds_entropy_formatted() -> None:
    formatted = format_variables({"si_tmaze_mean_belief_entropy": 1.234567})
    assert formatted["si_tmaze_mean_belief_entropy_formatted"] == "1.2346"


def test_substitute_snake_case_tokens_supports_precision() -> None:
    text = "entropy {{si_tmaze_mean_belief_entropy:.4f}}"
    resolved, unresolved = substitute_snake_case_tokens(
        text,
        {"si_tmaze_mean_belief_entropy": "1.234567"},
    )
    assert unresolved == []
    assert resolved == "entropy 1.2346"


def test_validate_manuscript_tokens_flags_unknown() -> None:
    root = Path(__file__).resolve().parents[1]
    from manuscript.hydrate import validate_manuscript_tokens

    keys = set(generate_variables(root, require_analysis_outputs=False))
    unknown = validate_manuscript_tokens(root / "manuscript", keys)
    assert unknown == []


def test_collect_malformed_token_names_flags_single_brace() -> None:
    from manuscript.hydrate import collect_malformed_token_names

    text = "Appendix binds {appendix_sheaf_track_count} but {{sheaf_track_count}} is fine."
    assert collect_malformed_token_names(text) == ["appendix_sheaf_track_count"]


def test_collect_malformed_token_names_ignores_latex_fenced_blocks() -> None:
    from manuscript.hydrate import collect_malformed_token_names

    text = (
        "```{=latex}\n"
        "\\addcontentsline{toc}{section}{Introduction}\n"
        "```\n"
        "Valid {{pipeline_track_count}}.\n"
    )
    assert collect_malformed_token_names(text) == []


def test_write_resolved_manuscript_raises_on_single_brace_token(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "00_abstract.md").write_text(
        "Bad {appendix_sheaf_track_count} token.\n",
        encoding="utf-8",
    )
    import pytest

    with pytest.raises(ValueError, match="malformed single-brace"):
        write_resolved_manuscript(tmp_path, {"pipeline_track_count": 16})


def test_write_resolved_manuscript_raises_on_unknown_token(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "00_abstract.md").write_text("Value {{not_a_real_token}}.\n", encoding="utf-8")
    import pytest

    with pytest.raises(ValueError, match="not_a_real_token"):
        write_resolved_manuscript(tmp_path, {"pipeline_track_count": 16})


def test_write_resolved_manuscript_removes_tokens(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "00_abstract.md").write_text(
        "Tracks: {{pipeline_track_count}}; entropy {{si_tmaze_mean_belief_entropy_formatted}}.\n",
        encoding="utf-8",
    )
    variables = generate_variables(root, require_analysis_outputs=False)
    out_dir = write_resolved_manuscript(tmp_path, variables)
    resolved = (out_dir / "00_abstract.md").read_text(encoding="utf-8")
    assert _TOKEN_RE.search(resolved) is None
    assert "Tracks: 30" in resolved


def test_manuscript_no_longer_describes_state_inference_as_default(project_root: Path) -> None:
    manuscript_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (project_root / "manuscript").rglob("*.md")
        if "output" not in path.parts
    )
    banned = (
        "default `state_inference`",
        "default state_inference",
        "scripted state-inference",
        "scripted rule",
        "mode: policy_inference",
        "deliberately too small",
        "2 states / 2 observations / 2 actions",
    )
    for phrase in banned:
        assert phrase not in manuscript_text

def test_format_variables_preserves_tiny_magnitudes() -> None:
    """Machine-epsilon residuals must not be laundered into a literal "0"."""
    from manuscript.hydrate import format_variables, substitute_snake_case_tokens

    out = format_variables({"sweep_rmse_mi": 2.122461271936776e-16, "gap": 0.6031, "zero": 0.0})
    assert out["sweep_rmse_mi"].startswith("2.122461e-16")
    assert out["gap"] == "0.6031"
    assert out["zero"] == "0"
    text, unresolved = substitute_snake_case_tokens("RMSE {{sweep_rmse_mi:.1e}} nats", out)
    assert text == "RMSE 2.1e-16 nats"
    assert unresolved == []


def test_format_variables_adversarial_inputs() -> None:
    """Pin the stringifier on the inputs most likely to regress (advisor ask).

    Exact zero stays "0"; negative zero does not print a minus sign; positive
    and negative epsilons keep magnitude AND sign; clean values keep their
    legacy short rendering; full-precision floats round at 4dp as before.
    """
    from manuscript.hydrate import format_variables

    out = format_variables(
        {
            "exact_zero": 0.0,
            "neg_zero": -0.0,
            "pos_eps": 4.440892098500626e-16,
            "neg_eps": -4.440892098500626e-16,
            "clean": 0.0998,
            "full_precision": 0.24681612473551864,
        }
    )
    assert out["exact_zero"] == "0"
    assert out["neg_zero"] == "0"  # -0.0 == 0.0, takes the zero branch
    assert out["pos_eps"] == "4.440892e-16"
    assert out["neg_eps"] == "-4.440892e-16"
    assert out["clean"] == "0.0998"
    assert out["full_precision"] == "0.2468"



def test_g_format_spec_supported_and_visible() -> None:
    """{{token:.3g}} must hydrate — an unsupported spec previously made the
    token INVISIBLE to both substitution and the fail-closed collector."""
    from manuscript.hydrate import collect_manuscript_tokens, format_variables, substitute_snake_case_tokens

    variables = format_variables({"kl": 6.281983145, "tiny": 0.002.__float__()})
    text, unresolved = substitute_snake_case_tokens("{{kl:.3g}} and {{tiny:.3g}}", variables)
    assert text == "6.28 and 0.002"
    assert unresolved == []
    assert collect_manuscript_tokens("{{kl:.3g}}") == ["kl"]  # visible to the gate


def test_sign_flag_format_spec_supported_and_visible() -> None:
    """{{token:+.3f}} must hydrate with its sign — this spec was also invisible."""
    from manuscript.hydrate import collect_manuscript_tokens, substitute_snake_case_tokens

    text, unresolved = substitute_snake_case_tokens("{{gap:+.3f}}", {"gap": "0.0998"})
    assert text == "+0.100"
    assert unresolved == []
    assert collect_manuscript_tokens("{{gap:+.3f}}") == ["gap"]
