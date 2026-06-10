# First-Principles Package

Executable support for the paper's OPD/Active-Inference correspondence.

- `mapping.py`, `taxonomy.py` - audited correspondence and OPD literature rows.
- `empirical.py` - curated literature-reported OPD benchmark rows (every value carries its bibkey; no measured claims).
- `divergences.py`, `reward_tilting.py`, `energy.py` - divergence geometry,
  reward-tilted targets, and VFE/EFE decompositions.
- `exposure_bias.py`, `gkd.py`, `variational_em.py`, `diversity.py`,
  `adaptive.py`, `parallel.py`, `sdpg.py` - deterministic minimal models of
  on-policy distillation mechanisms.
- `classroom.py`, `privilege.py`, `statistics.py` - two-agent pymdp classroom
  evidence and derived uncertainty summaries.
- `artifacts.py` - writes the canonical JSON/Markdown artifacts consumed by
  manuscript variables, figures, and validation gates.
