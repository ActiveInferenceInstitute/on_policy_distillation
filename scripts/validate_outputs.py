#!/usr/bin/env python3
"""Validate generated outputs against the track contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from gates.validation import validate_manuscript, validate_outputs


def main() -> int:
    outputs = validate_outputs(PROJECT_ROOT)
    manuscript = validate_manuscript(PROJECT_ROOT)
    failed = {**{k: v for k, v in outputs.items() if not v}, **{k: v for k, v in manuscript.items() if not v}}
    report = {
        "schema": "template_active_inference.validation_report.v1",
        "outputs": outputs,
        "manuscript": manuscript,
        "failed_checks": sorted(failed),
        "all_passed": not failed,
    }
    # Persist the report: the release attestation and release-notes evidence
    # attest output/reports/validation_report.json. Before this write existed,
    # those rows were *permanently* deferred against a file nothing produced.
    report_path = PROJECT_ROOT / "output" / "reports" / "validation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"outputs": outputs, "manuscript": manuscript}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
