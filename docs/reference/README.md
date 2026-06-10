# Reference Contracts

This directory holds the public reference contracts for the
"On-Policy Distillation is Active Inference" project.

| File | Role |
| --- | --- |
| [`configuration-and-extension.md`](configuration-and-extension.md) | Knob→consumer map for every config file, the six-surface add-a-figure recipe, the add-a-track recipe, what-to-run-after-editing-X, and troubleshooting. |
| [`method-inventory.md`](method-inventory.md) | Generated inventory for every Python `class` and `def` in the project, including scripts and internal helpers. |
| [`notation-supplement.md`](notation-supplement.md) | Integrated notation and formalism dictionary shared by the manuscript and the executable `firstprinciples` reference implementations. |
| [`rendering-reproducibility.md`](rendering-reproducibility.md) | Contract for sheaf rendering, replay, provenance, figure metadata, PDF/web parity, and copied-output reproducibility. |

Regenerate the method inventory with:

```bash
uv run python scripts/generate_method_inventory.py
```

Validate generated outputs with:

```bash
uv run python scripts/validate_outputs.py
```
