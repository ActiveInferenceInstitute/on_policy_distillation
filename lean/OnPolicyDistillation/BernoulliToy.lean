/-!
# Bernoulli toy structural witnesses

Deterministic `Int` witnesses for the symmetric Bernoulli-Ising toy that the analytical
track sweeps. These check structural facts of the *declared finite objects* -- e.g. that
the centered 2x2 coupling sums to zero -- not real-valued entropy or the sweep itself.
Bare lean4, no Mathlib.
-/

namespace OnPolicyDistillation

/-- The centered 2x2 Ising coupling entries used by the analytical toy. -/
def isingCouplingEntries : List Int := [1, -1, -1, 1]

def isingCouplingSum : Int := isingCouplingEntries.foldl (· + ·) 0

theorem ising_coupling_sum_zero : isingCouplingSum = 0 := by
  decide

end OnPolicyDistillation
