# Lean proof modules

- `BernoulliToy.lean` — structural witnesses for the Bernoulli-Ising coupling toy.
- `SophisticatedInference.lean` — finite-map reachability / normalization witnesses for the sophisticated-inference (T-maze and graph) track.
- `InformationIdentity.lean` — the active-selection mutual-information complement identity `I(o;r) + E_o[H(r|o)] = H(r)` over `Int`, its endpoints (`cue_closes_gap` / `pragmatic_leaves_gap`), and its structural properties (`expectedCondEntropy_append`, `mi_bounded`, `mi_antitone`(`_strict`), `blind_channel`).

Each module carries a module-level docstring stating its honest scope. New theorems are audited automatically — `gates.lean.lean_axioms_clean` discovers every theorem from source and runs `#print axioms`, so the audit set cannot drift below the inventory.

Imported by `../OnPolicyDistillation.lean`.
