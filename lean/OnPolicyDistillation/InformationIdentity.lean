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
    observation list -- a genuine finite enumeration, not an opaque constant. As a
    signed `Int` sum it is not constrained to be non-negative; `expectedCondEntropy_nonneg`
    below recovers non-negativity under the natural per-observation hypothesis. -/
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

/-! ### Structural properties of the skeleton

The two theorems above pin the active-selection endpoints (full transfer / strictly
less). The properties below establish the *shape* of the skeleton: the conditional
entropy fold composes additively over channel concatenation, it is non-negative when
each per-observation residual is, the mutual information is bounded between zero and
the prior entropy, it is antitone in the residual, and a residual equal to the prior
entropy transfers nothing. These are the integer-skeleton images of standard
information-theoretic facts -- they remain over `Int`, not real-valued entropy. -/

/-- `foldl` with an accumulator equals `acc` plus the fold from `0` -- the
    accumulator lemma that lets the explicit conditional-entropy fold compose. -/
theorem foldl_add_acc (obs : List Int) (acc : Int) :
    obs.foldl (· + ·) acc = acc + obs.foldl (· + ·) 0 := by
  induction obs generalizing acc with
  | nil => simp
  | cons x xs ih =>
    simp only [List.foldl_cons]
    rw [ih (acc + x), ih (0 + x)]
    omega

/-- ADDITIVITY: the expected conditional entropy of concatenated channels is the
    sum of the parts -- `E_o[H(r|o)]` composes over channel concatenation. -/
theorem expectedCondEntropy_append (a b : List Int) :
    expectedCondEntropy (a ++ b) = expectedCondEntropy a + expectedCondEntropy b := by
  unfold expectedCondEntropy
  rw [List.foldl_append]
  rw [foldl_add_acc b (a.foldl (· + ·) 0)]

/-- Non-negativity of the expected conditional entropy when every per-observation
    residual is non-negative -- conditional entropies are non-negative quantities. -/
theorem expectedCondEntropy_nonneg (obs : List Int)
    (h : ∀ x ∈ obs, 0 ≤ x) : 0 ≤ expectedCondEntropy obs := by
  unfold expectedCondEntropy
  induction obs with
  | nil => simp
  | cons x xs ih =>
    simp only [List.foldl_cons]
    rw [foldl_add_acc xs (0 + x)]
    have hx : 0 ≤ x := h x (List.mem_cons_self x xs)
    have hxs : 0 ≤ xs.foldl (· + ·) 0 := by
      apply ih
      intro y hy
      exact h y (List.mem_cons_of_mem x hy)
    omega

/-- BOUND: `0 ≤ I(o;r) ≤ H(r)`. Under non-negative per-observation residuals and a
    residual no larger than the prior entropy, the mutual information sits between
    zero and the prior entropy -- the formal skeleton of "epistemic value is bounded
    by the prior entropy", which the active-selection result exhibits (epistemic
    value ranges over `0 .. H(r)`). -/
theorem mi_bounded (priorEntropy : Int) (obs : List Int)
    (hnn : ∀ x ∈ obs, 0 ≤ x)
    (hle : expectedCondEntropy obs ≤ priorEntropy) :
    0 ≤ mutualInformation priorEntropy obs ∧
    mutualInformation priorEntropy obs ≤ priorEntropy := by
  unfold mutualInformation
  have hnn' : 0 ≤ expectedCondEntropy obs := expectedCondEntropy_nonneg obs hnn
  omega

/-- MONOTONICITY (antitone): a channel with a larger residual transfers no more
    information -- `I` is antitone in the expected conditional entropy. -/
theorem mi_antitone (priorEntropy : Int) (obs1 obs2 : List Int)
    (h : expectedCondEntropy obs1 ≤ expectedCondEntropy obs2) :
    mutualInformation priorEntropy obs2 ≤ mutualInformation priorEntropy obs1 := by
  unfold mutualInformation
  omega

/-- STRICT MONOTONICITY: a strictly larger residual transfers strictly less
    information -- the strict dual of `mi_antitone`. -/
theorem mi_antitone_strict (priorEntropy : Int) (obs1 obs2 : List Int)
    (h : expectedCondEntropy obs1 < expectedCondEntropy obs2) :
    mutualInformation priorEntropy obs2 < mutualInformation priorEntropy obs1 := by
  unfold mutualInformation
  omega

/-- BLIND CHANNEL: a residual equal to the prior entropy transfers nothing,
    `I = 0` -- the dual of `cue_closes_gap` (a fully-uninformative observation
    leaves the entire distillation gap open, like the blinded cue). -/
theorem blind_channel (priorEntropy : Int) (obs : List Int)
    (h : expectedCondEntropy obs = priorEntropy) :
    mutualInformation priorEntropy obs = 0 := by
  unfold mutualInformation
  omega

/-- Concrete blind witness, dual to `cueResolvesObs`: a single observation whose
    residual is the full prior entropy transfers zero information. -/
def blindObs (priorEntropy : Int) : List Int := [priorEntropy]

theorem blind_witness (priorEntropy : Int) :
    mutualInformation priorEntropy (blindObs priorEntropy) = 0 := by
  unfold mutualInformation expectedCondEntropy blindObs
  simp

end OnPolicyDistillation
