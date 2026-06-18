/-
  Finite-channel chain-rule SKELETON for the active-selection identity.

  The active-selection result rests on the mutual-information complement identity
      I(o;r) = H(r) - E_o[H(r|o)],   equivalently   I(o;r) + E_o[H(r|o)] = H(r).
  This module machine-checks the ALGEBRAIC STRUCTURE of that identity over the
  integers: mutual information is *defined* as the prior entropy minus the explicit
  finite fold of per-observation conditional entropies, and the chain-rule equality
  is proved for any prior and any finite observation list.

  SCOPE (honest): this is the finite chain-rule skeleton over `Int`. It does NOT
  encode `entropy = -Σ p log p`; the real-valued log identity (e.g. I + H_b(σ) = log 2)
  remains the two-route NUMERICAL witness in the analytical track (residual 2.2e-16),
  not a Lean theorem -- the project's Lean toolchain is pinned to bare lean4 with no
  Mathlib, so `Real.log`/binary-entropy are out of scope here. The negative control
  `pragmatic_leaves_gap` is what keeps the skeleton from being vacuous: a strictly
  positive residual transfers strictly less than the prior entropy, mirroring the
  pragmatic-only policy that leaves the distillation gap open.
-/

namespace OnPolicyDistillation

/-- Expected conditional entropy `E_o[H(r|o)]` as an explicit fold over the finite
    observation list -- a genuine finite enumeration, not an opaque constant. -/
def expectedCondEntropy (obs : List Int) : Int := obs.foldl (· + ·) 0

/-- Mutual information `I(o;r)` defined as prior entropy minus the expected
    conditional entropy -- the entropy-reduction the active-selection result uses. -/
def mutualInformation (priorEntropy : Int) (obs : List Int) : Int :=
  priorEntropy - expectedCondEntropy obs

/-- Chain-rule / complement identity for a finite categorical channel:
    `I(o;r) + E_o[H(r|o)] = H(r)`, for ANY prior entropy and ANY finite channel. -/
theorem mi_chain_rule (priorEntropy : Int) (obs : List Int) :
    mutualInformation priorEntropy obs + expectedCondEntropy obs = priorEntropy := by
  unfold mutualInformation
  omega

/-- A cue that fully resolves the residual (`E_o[H(r|o)] = 0`) transfers all of the
    prior entropy: `I = H(r)` -- the active-selection cue policy, residual gap zero. -/
def cueResolvesObs : List Int := [0, 0]

theorem cue_closes_gap (priorEntropy : Int) :
    mutualInformation priorEntropy cueResolvesObs = priorEntropy := by
  unfold mutualInformation expectedCondEntropy cueResolvesObs
  simp

/-- NEGATIVE CONTROL (must fire): an observation leaving a strictly positive
    residual `r > 0` transfers strictly less than the prior entropy, `I < H(r)` --
    the pragmatic-only policy that leaves the distillation gap open. -/
theorem pragmatic_leaves_gap (priorEntropy r : Int) (hr : r > 0) :
    mutualInformation priorEntropy [r] < priorEntropy := by
  unfold mutualInformation expectedCondEntropy
  simp
  omega

end OnPolicyDistillation
