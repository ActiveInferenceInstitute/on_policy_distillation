"""Writer-side numeric tolerances for simulation artifacts (single definition).

Scope note (deliberate design, do not "fix"): validator-side literals in
``src/gates/`` intentionally do NOT import these constants. Across the
writer/validator trust boundary, duplication is the verification mechanism —
a shared constant would let one edit loosen both sides silently, making the
re-derivation self-confirming. SSOT applies within a trust domain only.
"""

from __future__ import annotations

#: Absolute tolerance for per-step policy-posterior row sums (``q_pi_by_step``).
STEP_POSTERIOR_ATOL = 1e-6

#: Absolute tolerance for policy-posterior distributions (``q_pi`` rows).
POLICY_POSTERIOR_ATOL = 1e-9
