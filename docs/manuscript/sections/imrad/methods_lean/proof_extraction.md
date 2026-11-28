### Proof extraction track

The `proof_extraction` track extracts Lean theorem statements and proof-source
metadata into `output/data/proof_extraction_index.json`. The index currently
contains {{proof_extraction_theorem_count}} extracted theorem rows, with
constructive-token status `{{proof_extraction_all_constructive}}`.

The extracted rows are checked against `output/reports/lean_theorem_inventory.json`
before the manuscript can render. This catches a false-green case where `lake build`
passes but a theorem silently falls out of the generated proof index; the gate requires
the theorem inventory and extracted proof rows to agree exactly.
