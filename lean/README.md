# Lean track

Lean 4 formalization of the exemplar's Active Inference statements — the
machine-checked formalism track.

- `OnPolicyDistillation.lean` - top-level module.
- `OnPolicyDistillation/` - proof modules:
  - `BernoulliToy.lean` — structural witnesses for the Bernoulli-Ising toy.
  - `SophisticatedInference.lean` — finite-map reachability / normalization witnesses for the T-maze and graph topologies.
  - `InformationIdentity.lean` — the active-selection mutual-information complement identity `I(o;r) + E_o[H(r|o)] = H(r)` and its structural properties (additivity, the `0 ≤ I ≤ H(r)` bound, monotonicity, blind-channel dual), bracketed by a positive (`cue_closes_gap`) and a negative (`pragmatic_leaves_gap`) control.
- `lakefile.lean`, `lean-toolchain` - Lake build configuration and pinned toolchain.

**Honest scope:** bare lean4 with **no Mathlib**. Every theorem is sorry-free over `Int`/`Nat`/finite structures; this is the integer chain-rule *skeleton*, not real-valued `-Σ p log p` entropy (the real-valued log identity stays the two-route numerical witness in the analytical track).

Build with `lake build` when `lean/lakefile.lean` is present (required pipeline track in `tracks.yaml`). Projects without a Lean tree skip the gate cleanly. The `lean_axioms_clean` gate audits **every** theorem (discovered from source) with `#print axioms`, whitelisting only `propext`, `Classical.choice`, `Quot.sound` — so a `sorry` or `native_decide` is caught even when `lake build` exits 0.
