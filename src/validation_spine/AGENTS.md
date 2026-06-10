# validation_spine/ - Artifact Provenance Spine

## Purpose

This package validates the generated artifact spine for the Active Inference
exemplar: required artifact presence, deterministic fingerprints, producer
metadata, replay provenance, and release-facing provenance drift checks.

## Local Rules

- Keep validators deterministic and filesystem-local; the public exemplar must
  not rely on network calls, private data, or LLM calls.
- Preserve race-safe file provenance through `_file_fingerprint` in
  [`artifacts.py`](artifacts.py). Do not replace it with ad hoc path or mtime
  checks.
- A new required artifact needs a producer, a fingerprinted provenance row, a
  validation rule, and a negative-control test before manuscript prose may rely
  on it.
- Project-local `output/` is scratch. Copied public deliverables live under the
  sibling template checkout's `output/working/active_inference_on_policy_distillation/`
  path after the root pipeline copy stage; that output path is generated and may
  not exist before a render.

## Verification

```bash
uv run python -m pytest tests/test_validation_spine.py tests/test_track_consolidation.py -q --tb=short
```
