# Method Inventory

Generated documentation coverage for every Python `def` and `class` under `src/` and `scripts/`. Entries marked `inventory fallback` have no inline docstring yet, but remain documented here by path, line, kind, and qualified name.

Total documented definitions: 891

## `src/analytical/bernoulli_toy.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 18 | `function` | `ising_coupling` | inventory fallback | Inventory fallback for function `ising_coupling` defined at `src/analytical/bernoulli_toy.py:18`. |
| 24 | `function` | `symmetric_mean_field_prior` | inventory fallback | Inventory fallback for function `symmetric_mean_field_prior` defined at `src/analytical/bernoulli_toy.py:24`. |
| 29 | `function` | `ising_mutual_information` | inventory fallback | Inventory fallback for function `ising_mutual_information` defined at `src/analytical/bernoulli_toy.py:29`. |
| 43 | `function` | `ising_joint_posterior` | inventory fallback | Inventory fallback for function `ising_joint_posterior` defined at `src/analytical/bernoulli_toy.py:43`. |
| 50 | `function` | `empirical_mutual_information` | docstring | Mutual information recomputed independently from the joint via total correlation. |
| 63 | `function` | `lambda_sweep_values` | docstring | Backward-compatible sweep grid; delegates to ``lambda_grid`` SSOT. |

## `src/analytical/coupling.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `entangled_prior_unnormalised` | inventory fallback | Inventory fallback for function `entangled_prior_unnormalised` defined at `src/analytical/coupling.py:15`. |
| 27 | `function` | `entangled_posterior` | inventory fallback | Inventory fallback for function `entangled_posterior` defined at `src/analytical/coupling.py:27`. |
| 43 | `function` | `expected_value` | inventory fallback | Inventory fallback for function `expected_value` defined at `src/analytical/coupling.py:43`. |

## `src/analytical/decomposition.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 20 | `class` | `DecompositionTerms` | inventory fallback | Inventory fallback for class `DecompositionTerms` defined at `src/analytical/decomposition.py:20`. |
| 27 | `function` | `DecompositionTerms.total` | inventory fallback | Inventory fallback for function `DecompositionTerms.total` defined at `src/analytical/decomposition.py:27`. |
| 36 | `function` | `sum_marginal_free_energies` | inventory fallback | Inventory fallback for function `sum_marginal_free_energies` defined at `src/analytical/decomposition.py:36`. |
| 46 | `function` | `coupling_cost_term` | inventory fallback | Inventory fallback for function `coupling_cost_term` defined at `src/analytical/decomposition.py:46`. |
| 50 | `function` | `coupling_prior_term` | inventory fallback | Inventory fallback for function `coupling_prior_term` defined at `src/analytical/decomposition.py:50`. |
| 62 | `function` | `entanglement_decomposition_rhs` | inventory fallback | Inventory fallback for function `entanglement_decomposition_rhs` defined at `src/analytical/decomposition.py:62`. |
| 79 | `function` | `_marginals_g_broadcast` | inventory fallback | Inventory fallback for function `_marginals_g_broadcast` defined at `src/analytical/decomposition.py:79`. |
| 89 | `function` | `free_energy_against_entangled_prior` | inventory fallback | Inventory fallback for function `free_energy_against_entangled_prior` defined at `src/analytical/decomposition.py:89`. |
| 107 | `function` | `decomposition_identity_holds` | inventory fallback | Inventory fallback for function `decomposition_identity_holds` defined at `src/analytical/decomposition.py:107`. |

## `src/analytical/free_energy.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 17 | `function` | `_safe_log` | inventory fallback | Inventory fallback for function `_safe_log` defined at `src/analytical/free_energy.py:17`. |
| 22 | `function` | `shannon_entropy` | inventory fallback | Inventory fallback for function `shannon_entropy` defined at `src/analytical/free_energy.py:22`. |
| 28 | `function` | `kl_divergence` | inventory fallback | Inventory fallback for function `kl_divergence` defined at `src/analytical/free_energy.py:28`. |
| 39 | `function` | `total_correlation` | inventory fallback | Inventory fallback for function `total_correlation` defined at `src/analytical/free_energy.py:39`. |
| 45 | `function` | `total_correlation_via_kl` | inventory fallback | Inventory fallback for function `total_correlation_via_kl` defined at `src/analytical/free_energy.py:45`. |
| 49 | `function` | `free_energy` | inventory fallback | Inventory fallback for function `free_energy` defined at `src/analytical/free_energy.py:49`. |
| 60 | `function` | `marginal_free_energy` | inventory fallback | Inventory fallback for function `marginal_free_energy` defined at `src/analytical/free_energy.py:60`. |

## `src/analytical/hyperparameters.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 14 | `class` | `Hyperparameters` | inventory fallback | Inventory fallback for class `Hyperparameters` defined at `src/analytical/hyperparameters.py:14`. |
| 22 | `function` | `load_hyperparameters` | inventory fallback | Inventory fallback for function `load_hyperparameters` defined at `src/analytical/hyperparameters.py:22`. |
| 26 | `function` | `lambda_grid` | inventory fallback | Inventory fallback for function `lambda_grid` defined at `src/analytical/hyperparameters.py:26`. |

## `src/analytical/invariants.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 21 | `function` | `inv_ising_mi_at_zero` | docstring | Check the closed-form Ising mutual information is zero at lambda = 0 within tolerance. |
| 26 | `function` | `inv_ising_mi_saturates` | docstring | Check the Ising mutual information saturates to ln 2 at large lambda (100.0). |
| 32 | `function` | `inv_empirical_matches_closed_form` | docstring | Check empirical and closed-form mutual information agree within tolerance across the lambda grid. |
| 43 | `function` | `inv_decomposition_identity` | docstring | Check the free-energy decomposition identity holds for the Ising joint posterior at lambda = 1.5. |
| 62 | `function` | `inv_joint_is_pmf` | docstring | Check the Ising joint posterior at lambda = 2.0 is a valid probability mass function. |
| 70 | `function` | `inv_mean_field_at_lambda_zero` | docstring | Check the Ising joint posterior factorizes (is mean-field) at lambda = 0. |
| 88 | `function` | `run_invariants` | docstring | Run all CORE_INVARIANTS and return name -> pass mapping. |
| 93 | `function` | `all_invariants_pass` | docstring | Return True when every invariant passes, running them when no results dict is given. |

## `src/analytical/joint_dist.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 13 | `function` | `is_pmf` | inventory fallback | Inventory fallback for function `is_pmf` defined at `src/analytical/joint_dist.py:13`. |
| 18 | `function` | `normalize` | inventory fallback | Inventory fallback for function `normalize` defined at `src/analytical/joint_dist.py:18`. |
| 26 | `function` | `mean_field_to_joint` | inventory fallback | Inventory fallback for function `mean_field_to_joint` defined at `src/analytical/joint_dist.py:26`. |
| 35 | `function` | `joint_marginal` | inventory fallback | Inventory fallback for function `joint_marginal` defined at `src/analytical/joint_dist.py:35`. |
| 43 | `function` | `joint_marginals` | inventory fallback | Inventory fallback for function `joint_marginals` defined at `src/analytical/joint_dist.py:43`. |
| 48 | `function` | `is_mean_field` | inventory fallback | Inventory fallback for function `is_mean_field` defined at `src/analytical/joint_dist.py:48`. |
| 54 | `function` | `m_projection` | inventory fallback | Inventory fallback for function `m_projection` defined at `src/analytical/joint_dist.py:54`. |

## `src/analytical/sweep_io.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 12 | `function` | `read_parameter_sweep` | docstring | Read ``parameter_sweep.csv`` rows as floats. |
| 29 | `function` | `summarize_sweep_rows` | docstring | Summarize sweep residuals and grid size from parsed rows. |
| 47 | `function` | `summarize_sweep_file` | docstring | Summarize sweep statistics from a CSV path. |

## `src/artifact_contracts.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 14 | `class` | `ScriptStep` | docstring | One configured analysis script in deterministic pipeline order. |
| 42 | `function` | `_unique` | docstring | Return values in declaration order with duplicates removed. |

## `src/firstprinciples/adaptive.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 33 | `class` | `TokenDirections` | inventory fallback | Inventory fallback for class `TokenDirections` defined at `src/firstprinciples/adaptive.py:33`. |
| 40 | `function` | `_entropy_threshold` | docstring | Default gate: the median student entropy across the token batch. |
| 46 | `function` | `token_directions` | docstring | Per-token adaptive KL: reverse where student is confident, forward where uncertain. |
| 79 | `function` | `adaptive_loss` | docstring | Summed adaptive per-token divergence. |
| 84 | `function` | `_all_one_direction` | inventory fallback | Inventory fallback for function `_all_one_direction` defined at `src/firstprinciples/adaptive.py:84`. |
| 91 | `function` | `build_payload` | docstring | Build the canonical `firstprinciples.adaptive_demo` artifact payload. |

## `src/firstprinciples/artifacts.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 56 | `function` | `_dir` | inventory fallback | Inventory fallback for function `_dir` defined at `src/firstprinciples/artifacts.py:56`. |
| 62 | `function` | `write_json` | inventory fallback | Inventory fallback for function `write_json` defined at `src/firstprinciples/artifacts.py:62`. |
| 68 | `function` | `divergence_demo` | docstring | Forward/reverse/JSD/skew/alpha geometry on the canonical example. |
| 84 | `function` | `reward_tilting_demo` | docstring | Reward-tilted target and numerical optimality certificate. |
| 99 | `function` | `exposure_bias_demo` | docstring | On-policy vs off-policy survival curves under compounding error. |
| 115 | `function` | `sdpg_demo` | docstring | SDPG objective terms across KL modes on canonical logits. |
| 134 | `function` | `write_statistics_artifact` | docstring | Write ``statistics_demo.json`` from measured classroom belief entropies. |
| 149 | `function` | `write_markdown_tables` | docstring | Write the correspondence and taxonomy markdown tables. |
| 164 | `function` | `write_all` | docstring | Emit every deterministic first-principles artifact; return name->path. |

## `src/firstprinciples/classroom.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 54 | `class` | `ClassroomConfig` | docstring | Privileged-teacher vs on-policy-student rollout parameters. |
| 62 | `function` | `ClassroomConfig.__post_init__` | inventory fallback | Inventory fallback for function `ClassroomConfig.__post_init__` defined at `src/firstprinciples/classroom.py:62`. |
| 72 | `class` | `ClassroomResult` | inventory fallback | Inventory fallback for class `ClassroomResult` defined at `src/firstprinciples/classroom.py:72`. |
| 92 | `function` | `align_distributions` | docstring | Return a shared key order and normalised teacher/student vectors. |
| 108 | `function` | `distillation_metrics` | docstring | Per-decision distillation geometry between teacher and student actions. |
| 124 | `function` | `summarize_steps` | docstring | Mean divergences across the per-step distillation records. |
| 135 | `function` | `_finite_nonnegative` | inventory fallback | Inventory fallback for function `_finite_nonnegative` defined at `src/firstprinciples/classroom.py:135`. |
| 143 | `function` | `_int_value` | inventory fallback | Inventory fallback for function `_int_value` defined at `src/firstprinciples/classroom.py:143`. |
| 150 | `function` | `_normalised` | inventory fallback | Inventory fallback for function `_normalised` defined at `src/firstprinciples/classroom.py:150`. |
| 163 | `function` | `_per_step_rows_valid` | inventory fallback | Inventory fallback for function `_per_step_rows_valid` defined at `src/firstprinciples/classroom.py:163`. |
| 185 | `function` | `_mean_matches` | inventory fallback | Inventory fallback for function `_mean_matches` defined at `src/firstprinciples/classroom.py:185`. |
| 194 | `function` | `validate_classroom_payload` | docstring | Validate the persisted classroom artifact against its measured claims. |
| 264 | `function` | `_belief_entropy_series` | docstring | Per-step belief entropies (nats) from the rollout trace, finite rows only. |
| 274 | `function` | `_agent_config` | inventory fallback | Inventory fallback for function `_agent_config` defined at `src/firstprinciples/classroom.py:274`. |
| 280 | `function` | `run_classroom` | docstring | Run the privileged-teacher / on-policy-student T-maze and measure the gap. |
| 330 | `function` | `build_payload` | docstring | Build the canonical `firstprinciples.classroom` artifact payload from a run result. |
| 339 | `function` | `write_classroom_artifact` | inventory fallback | Inventory fallback for function `write_classroom_artifact` defined at `src/firstprinciples/classroom.py:339`. |

## `src/firstprinciples/divergences.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 39 | `function` | `normalize` | docstring | Project a non-negative vector onto the probability simplex. |
| 50 | `function` | `forward_kl` | docstring | Mode-covering forward KL ``D_KL(teacher \|\| student)``. |
| 60 | `function` | `reverse_kl` | docstring | Mode-seeking reverse KL ``D_KL(student \|\| teacher)``. |
| 71 | `function` | `symmetric_kl` | docstring | Symmetric KL ``D_KL(p \|\| q) + D_KL(q \|\| p)``. |
| 77 | `function` | `jensen_shannon` | docstring | Jensen–Shannon divergence (bounded, symmetric) in nats. |
| 84 | `function` | `skew_kl` | docstring | Skew KL ``D_KL(p \|\| (1-alpha) p + alpha q)`` (DistiLLM family). |
| 98 | `function` | `alpha_divergence` | docstring | Amari alpha-divergence interpolating forward (alpha->0) and reverse. |
| 118 | `function` | `clipped_pointwise_kl` | docstring | Per-token pointwise-clipped reverse KL (OPSD, Zhao et al. 2026). |
| 136 | `function` | `mode_concentration` | docstring | Quantify mode-seeking vs mode-covering behaviour of the two KLs. |

## `src/firstprinciples/diversity.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 52 | `class` | `DiversityCurve` | inventory fallback | Inventory fallback for class `DiversityCurve` defined at `src/firstprinciples/diversity.py:52`. |
| 61 | `function` | `sharpen` | docstring | Temperature-sharpened student ``pi_T^{1/tau}`` renormalised. |
| 70 | `function` | `correct_mass` | docstring | Total student probability on the correct token set ``c``. |
| 76 | `function` | `pass_at_1` | docstring | Greedy Pass@1: whether the most-likely token is correct (tau-invariant). |
| 82 | `function` | `pass_at_k` | docstring | Sampling Pass@k: probability at least one of ``k`` i.i.d. samples is correct. |
| 90 | `function` | `diversity_tradeoff` | docstring | Mean greedy Pass@1 (tau-invariant) and mean sampling Pass@k across a sweep. |
| 117 | `function` | `_ensemble` | inventory fallback | Inventory fallback for function `_ensemble` defined at `src/firstprinciples/diversity.py:117`. |
| 127 | `function` | `build_payload` | docstring | Build the canonical `firstprinciples.diversity_demo` artifact payload. |

## `src/firstprinciples/empirical.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 41 | `class` | `BenchmarkRow` | docstring | One literature-reported training-method benchmark row. |
| 119 | `function` | `_row` | inventory fallback | Inventory fallback for function `_row` defined at `src/firstprinciples/empirical.py:119`. |
| 126 | `function` | `compute_reduction` | docstring | RL GPU-hours / on-policy-distillation GPU-hours (reported). |
| 135 | `function` | `accuracy_gain` | docstring | On-policy-distillation accuracy gain over the off-policy and RL baselines. |
| 147 | `function` | `as_records` | inventory fallback | Inventory fallback for function `as_records` defined at `src/firstprinciples/empirical.py:147`. |
| 151 | `function` | `markdown_table` | inventory fallback | Inventory fallback for function `markdown_table` defined at `src/firstprinciples/empirical.py:151`. |
| 163 | `function` | `build_payload` | docstring | Build the canonical `firstprinciples.empirical_benchmark` artifact payload. |

## `src/firstprinciples/energy.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 68 | `function` | `_safe_log` | inventory fallback | Inventory fallback for function `_safe_log` defined at `src/firstprinciples/energy.py:68`. |
| 73 | `function` | `_values_agree` | docstring | True if all values are pairwise close, or all are the same infinity. |
| 86 | `function` | `_expected_log` | docstring | E_q[ln x], returning -inf if q places mass where x == 0 (no flooring). |
| 101 | `class` | `GenerativeModel` | docstring | A categorical generative model ``p(s) p(o\|s)`` with preferences ``p(o)``. |
| 108 | `function` | `GenerativeModel.__post_init__` | inventory fallback | Inventory fallback for function `GenerativeModel.__post_init__` defined at `src/firstprinciples/energy.py:108`. |
| 120 | `function` | `GenerativeModel.num_states` | inventory fallback | Inventory fallback for function `GenerativeModel.num_states` defined at `src/firstprinciples/energy.py:120`. |
| 124 | `function` | `GenerativeModel.num_obs` | inventory fallback | Inventory fallback for function `GenerativeModel.num_obs` defined at `src/firstprinciples/energy.py:124`. |
| 128 | `function` | `evidence` | docstring | Marginal likelihood ``p(o) = sum_s p(o\|s) p(s)``. |
| 134 | `function` | `posterior` | docstring | Exact Bayesian posterior ``p(s\|o)`` (the teacher target). |
| 144 | `function` | `vfe_energy_entropy` | docstring | F = E_q[-ln p(o,s)] - H[q]. |
| 153 | `function` | `vfe_complexity_accuracy` | docstring | Return (F, complexity, accuracy) with F = complexity - accuracy. |
| 162 | `function` | `vfe_divergence_evidence` | docstring | Return (F, divergence, log_evidence) with F = divergence - log_evidence. |
| 171 | `function` | `vfe_report` | docstring | All three VFE decompositions plus an exact-agreement certificate. |
| 188 | `function` | `predicted_observations` | docstring | Predicted observation distribution ``q(o) = sum_s p(o\|s) q(s)``. |
| 194 | `function` | `efe_risk_ambiguity` | docstring | Return (G, risk, ambiguity) with G = risk + ambiguity. |
| 204 | `function` | `efe_epistemic_pragmatic` | docstring | Return (G, epistemic_value, pragmatic_value) with G = -(epistemic + pragmatic). |
| 227 | `function` | `efe_report` | docstring | Both EFE decompositions plus an exact-agreement certificate. |
| 242 | `function` | `_canonical_model` | inventory fallback | Inventory fallback for function `_canonical_model` defined at `src/firstprinciples/energy.py:242`. |
| 249 | `function` | `build_payload` | docstring | Energy-based demonstration: VFE at the prior vs the exact posterior, and EFE. |

## `src/firstprinciples/exposure_bias.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 27 | `class` | `DriftSpec` | docstring | Parameters of the on-track / off-track survival chain. |
| 42 | `function` | `DriftSpec.__post_init__` | inventory fallback | Inventory fallback for function `DriftSpec.__post_init__` defined at `src/firstprinciples/exposure_bias.py:42`. |
| 51 | `function` | `_survival` | docstring | P(ON at step t) for t = 1..horizon under the two-state chain. |
| 62 | `function` | `drift_curves` | docstring | Return off-policy and on-policy survival curves over the horizon. |
| 70 | `function` | `exposure_gap` | docstring | Summarise the terminal advantage of on-policy over off-policy training. |

## `src/firstprinciples/gkd.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 46 | `class` | `GKDProblem` | docstring | A minimal token-state distillation problem. |
| 62 | `function` | `GKDProblem.__post_init__` | inventory fallback | Inventory fallback for function `GKDProblem.__post_init__` defined at `src/firstprinciples/gkd.py:62`. |
| 78 | `function` | `_stationary_visitation` | docstring | Average state visitation over a finite horizon under a policy's walk. |
| 100 | `function` | `normalize_rows` | inventory fallback | Inventory fallback for function `normalize_rows` defined at `src/firstprinciples/gkd.py:100`. |
| 107 | `function` | `visitation` | docstring | State visitation distribution under the student (on-policy) or teacher. |
| 113 | `function` | `gkd_loss` | docstring | Visitation-weighted per-token divergence (reverse KL by default). |
| 134 | `function` | `exposure_bias_gap` | docstring | Contrast off-policy and on-policy GKD objectives. |
| 153 | `function` | `_canonical_problem` | inventory fallback | Inventory fallback for function `_canonical_problem` defined at `src/firstprinciples/gkd.py:153`. |
| 168 | `function` | `build_payload` | docstring | Assemble the GKD on-policy-vs-off-policy demonstration artifact. |

## `src/firstprinciples/mapping.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 31 | `class` | `Correspondence` | docstring | One audited row of the active-inference <-> OPD dictionary. |
| 200 | `function` | `correspondences` | docstring | Return the immutable correspondence table. |
| 205 | `function` | `as_records` | docstring | Return the table as a list of plain dicts (for JSON artifacts). |
| 210 | `function` | `lookup` | docstring | Return the row whose active-inference component matches (case-folded). |
| 219 | `function` | `markdown_table` | docstring | Render the correspondence table as GitHub-flavoured markdown. |
| 229 | `function` | `validate_mapping` | docstring | Return a list of integrity issues (empty list means the map is sound). |
| 244 | `function` | `build_payload` | docstring | Assemble the validated correspondence-map artifact. |

## `src/firstprinciples/parallel.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 38 | `class` | `MLDistillResult` | inventory fallback | Inventory fallback for class `MLDistillResult` defined at `src/firstprinciples/parallel.py:38`. |
| 48 | `function` | `ml_distill_to_teacher` | docstring | Train a student policy to a teacher by jax-autodiff reverse-KL distillation. |
| 64 | `function` | `ml_distill_to_teacher.loss` | inventory fallback | Inventory fallback for function `ml_distill_to_teacher.loss` defined at `src/firstprinciples/parallel.py:64`. |
| 91 | `function` | `_canonical_model` | inventory fallback | Inventory fallback for function `_canonical_model` defined at `src/firstprinciples/parallel.py:91`. |
| 99 | `function` | `build_payload` | docstring | Solve one scenario in both frameworks and certify they agree. |

## `src/firstprinciples/privilege.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 31 | `class` | `PrivilegeSweepConfig` | inventory fallback | Inventory fallback for class `PrivilegeSweepConfig` defined at `src/firstprinciples/privilege.py:31`. |
| 37 | `function` | `PrivilegeSweepConfig.__post_init__` | inventory fallback | Inventory fallback for function `PrivilegeSweepConfig.__post_init__` defined at `src/firstprinciples/privilege.py:37`. |
| 45 | `function` | `rank_correlation` | docstring | Spearman rank correlation (Pearson correlation of ranks), no SciPy. |
| 50 | `function` | `rank_correlation._ranks` | inventory fallback | Inventory fallback for function `rank_correlation._ranks` defined at `src/firstprinciples/privilege.py:50`. |
| 73 | `function` | `run_privilege_sweep` | docstring | Run the classroom across the teacher cue-validity grid; return the trend. |
| 127 | `function` | `build_payload` | docstring | Build the canonical privilege-sweep artifact payload by running the sweep. |

## `src/firstprinciples/reward_tilting.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 37 | `function` | `_normalize` | inventory fallback | Inventory fallback for function `_normalize` defined at `src/firstprinciples/reward_tilting.py:37`. |
| 45 | `function` | `reward_tilted_target` | docstring | Return ``pi*(y) ∝ pi_ref(y) exp(R(y)/beta)`` (numerically stable). |
| 59 | `function` | `expected_reward` | inventory fallback | Inventory fallback for function `expected_reward` defined at `src/firstprinciples/reward_tilting.py:59`. |
| 65 | `function` | `kl_regularized_objective` | docstring | ``J(pi) = E_pi[R] - beta * D_KL(pi \|\| pi_ref)``. |
| 72 | `function` | `free_energy_against_tilted` | docstring | Variational free energy of ``policy`` against the reward-tilted model. |
| 85 | `function` | `verify_optimality` | docstring | Numerically confirm the reward-tilted target maximises ``J``. |

## `src/firstprinciples/sdpg.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 41 | `class` | `SDPGConfig` | docstring | SDPG hyperparameters mirroring the reference implementation defaults. |
| 48 | `function` | `SDPGConfig.__post_init__` | inventory fallback | Inventory fallback for function `SDPGConfig.__post_init__` defined at `src/firstprinciples/sdpg.py:48`. |
| 55 | `function` | `softmax` | docstring | Numerically stable softmax over the last axis (single distribution). |
| 65 | `function` | `self_distillation_term` | docstring | The privileged-context self-distillation KL under the chosen direction. |
| 79 | `function` | `sdpg_loss` | docstring | Evaluate the three SDPG terms for one token position. |
| 111 | `function` | `signal_density` | docstring | Contrast the density of the self-distillation signal vs a scalar reward. |

## `src/firstprinciples/sequential_shift.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 46 | `class` | `SequentialShiftProblem` | docstring | A finite policy-induced state-visitation problem. |
| 56 | `function` | `SequentialShiftProblem.__post_init__` | inventory fallback | Inventory fallback for function `SequentialShiftProblem.__post_init__` defined at `src/firstprinciples/sequential_shift.py:56`. |
| 85 | `function` | `_require_row_stochastic` | inventory fallback | Inventory fallback for function `_require_row_stochastic` defined at `src/firstprinciples/sequential_shift.py:85`. |
| 92 | `function` | `_require_vector_stochastic` | inventory fallback | Inventory fallback for function `_require_vector_stochastic` defined at `src/firstprinciples/sequential_shift.py:92`. |
| 99 | `function` | `induced_transition` | docstring | Return the state transition induced by a state-conditioned policy. |
| 108 | `function` | `visitation` | docstring | Average finite-horizon visitation under the policy-induced transition. |
| 120 | `function` | `_per_state_reverse_kl` | inventory fallback | Inventory fallback for function `_per_state_reverse_kl` defined at `src/firstprinciples/sequential_shift.py:120`. |
| 127 | `function` | `_mix_policy` | inventory fallback | Inventory fallback for function `_mix_policy` defined at `src/firstprinciples/sequential_shift.py:127`. |
| 135 | `function` | `_canonical_problem` | inventory fallback | Inventory fallback for function `_canonical_problem` defined at `src/firstprinciples/sequential_shift.py:135`. |
| 191 | `function` | `build_payload` | docstring | Assemble the sequential distribution-shift witness artifact. |
| 238 | `function` | `build_sensitivity_payload` | docstring | Assemble a finite correction-dose sensitivity sweep for the shift witness. |
| 312 | `function` | `validate_payload` | docstring | Return validation issues for a sequential-shift payload. |
| 368 | `function` | `validate_sensitivity_payload` | docstring | Return validation issues for a sequential-shift correction-dose sweep. |

## `src/firstprinciples/statistics.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 34 | `class` | `Summary` | inventory fallback | Inventory fallback for class `Summary` defined at `src/firstprinciples/statistics.py:34`. |
| 42 | `function` | `_array` | inventory fallback | Inventory fallback for function `_array` defined at `src/firstprinciples/statistics.py:42`. |
| 49 | `function` | `summarize` | inventory fallback | Inventory fallback for function `summarize` defined at `src/firstprinciples/statistics.py:49`. |
| 60 | `function` | `bootstrap_ci` | docstring | Percentile bootstrap CI for the mean (seeded, deterministic). |
| 84 | `function` | `cohens_d` | docstring | Cohen's d effect size (pooled SD) for two independent samples. |
| 97 | `function` | `paired_permutation_test` | docstring | Two-sided paired permutation test on the mean difference a - b. |
| 121 | `function` | `paired_sign_test` | docstring | Exact two-sided sign test on paired differences a - b. |
| 141 | `function` | `build_payload` | docstring | Build the canonical ``statistics_demo`` artifact from measured classroom data. |

## `src/firstprinciples/taxonomy.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 34 | `class` | `Method` | docstring | One on-policy distillation method with its structural attributes. |
| 291 | `function` | `methods` | inventory fallback | Inventory fallback for function `methods` defined at `src/firstprinciples/taxonomy.py:291`. |
| 295 | `function` | `on_policy_methods` | inventory fallback | Inventory fallback for function `on_policy_methods` defined at `src/firstprinciples/taxonomy.py:295`. |
| 299 | `function` | `privileged_info_methods` | inventory fallback | Inventory fallback for function `privileged_info_methods` defined at `src/firstprinciples/taxonomy.py:299`. |
| 303 | `function` | `loss_share_total` | docstring | Total of the loss-family shares (should be ~1.0). |
| 308 | `function` | `as_records` | inventory fallback | Inventory fallback for function `as_records` defined at `src/firstprinciples/taxonomy.py:308`. |
| 312 | `function` | `markdown_table` | inventory fallback | Inventory fallback for function `markdown_table` defined at `src/firstprinciples/taxonomy.py:312`. |
| 323 | `function` | `build_payload` | docstring | Build the canonical `firstprinciples.opd_taxonomy` artifact payload. |

## `src/firstprinciples/variational_em.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 40 | `class` | `EMResult` | inventory fallback | Inventory fallback for class `EMResult` defined at `src/firstprinciples/variational_em.py:40`. |
| 49 | `function` | `_normalize` | inventory fallback | Inventory fallback for function `_normalize` defined at `src/firstprinciples/variational_em.py:49`. |
| 57 | `function` | `run_em` | docstring | Run variational-EM distillation from ``reference`` toward the tilted target. |
| 109 | `function` | `build_payload` | docstring | Build the canonical `firstprinciples.variational_em_demo` artifact payload. |

## `src/gates/aggregate_rederivation.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 60 | `function` | `_eval_spec` | inventory fallback | Inventory fallback for function `_eval_spec` defined at `src/gates/aggregate_rederivation.py:60`. |
| 265 | `function` | `rederive_aggregate` | docstring | Re-derive an aggregate from ``payload['rows']``; vacuous truth is False. |
| 275 | `function` | `aggregate_rederivation_rows` | docstring | One row per covered (artifact, aggregate): stored vs re-derived. |
| 314 | `function` | `aggregates_consistent` | docstring | True iff every covered stored aggregate equals its row-level re-derivation. |
| 319 | `function` | `rule_count` | docstring | Number of (artifact, aggregate) pairs re-derived at validation time. |

## `src/gates/claim_ledger.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 10 | `function` | `_load_structured` | inventory fallback | Inventory fallback for function `_load_structured` defined at `src/gates/claim_ledger.py:10`. |
| 20 | `function` | `_lookup_field` | inventory fallback | Inventory fallback for function `_lookup_field` defined at `src/gates/claim_ledger.py:20`. |
| 32 | `function` | `_numbers_equal` | inventory fallback | Inventory fallback for function `_numbers_equal` defined at `src/gates/claim_ledger.py:32`. |
| 58 | `function` | `_predicate_holds` | inventory fallback | Inventory fallback for function `_predicate_holds` defined at `src/gates/claim_ledger.py:58`. |
| 88 | `function` | `_set_equals` | inventory fallback | Inventory fallback for function `_set_equals` defined at `src/gates/claim_ledger.py:88`. |
| 94 | `function` | `_evidence_spec_holds` | inventory fallback | Inventory fallback for function `_evidence_spec_holds` defined at `src/gates/claim_ledger.py:94`. |
| 176 | `function` | `typed_claim_evidence_issues` | docstring | Return explicit typed-evidence failures for ``claim_ledger.yaml``. |
| 243 | `function` | `validate_typed_claim_evidence` | docstring | Validate optional typed evidence declarations in ``claim_ledger.yaml``. |
| 259 | `function` | `validate_claim_ledger` | inventory fallback | Inventory fallback for function `validate_claim_ledger` defined at `src/gates/claim_ledger.py:259`. |
| 301 | `function` | `verify_claim_bindings` | docstring | Semantic claim bindings -- tie manuscript values/adjectives to their oracles. |

## `src/gates/lean.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 17 | `function` | `lean_project_present` | docstring | True when this project ships a Lake root (``lean/lakefile.lean``). |
| 22 | `function` | `build_lean` | docstring | Build the Lean package when present; skip cleanly when absent. |
| 39 | `function` | `lean_axioms_clean` | docstring | Audit declarations with ``#print axioms``; True iff only whitelisted axioms appear. |

## `src/gates/manuscript_checks.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 49 | `function` | `_duplicate_track_markers` | docstring | Composed sections in which the same sheaf-track marker appears more than once. |
| 66 | `function` | `_bib_keys` | inventory fallback | Inventory fallback for function `_bib_keys` defined at `src/gates/manuscript_checks.py:66`. |
| 73 | `function` | `_citation_source_paths` | inventory fallback | Inventory fallback for function `_citation_source_paths` defined at `src/gates/manuscript_checks.py:73`. |
| 83 | `function` | `unresolved_citation_keys` | docstring | Return manuscript citation keys that have no bibliography entry. |
| 102 | `function` | `citations_resolved` | inventory fallback | Inventory fallback for function `citations_resolved` defined at `src/gates/manuscript_checks.py:102`. |
| 106 | `function` | `validate_manuscript_selected_strict` | docstring | Validate selected manuscript keys without silently dropping unknown keys. |
| 119 | `function` | `validate_manuscript` | inventory fallback | Inventory fallback for function `validate_manuscript` defined at `src/gates/manuscript_checks.py:119`. |
| 126 | `function` | `validate_manuscript._wants` | inventory fallback | Inventory fallback for function `validate_manuscript._wants` defined at `src/gates/manuscript_checks.py:126`. |
| 186 | `function` | `validate_manuscript._section_path` | inventory fallback | Inventory fallback for function `validate_manuscript._section_path` defined at `src/gates/manuscript_checks.py:186`. |

## `src/gates/method_inventory.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 14 | `class` | `MethodEntry` | docstring | A documented function, method, nested helper, or class definition. |
| 25 | `function` | `_first_docstring_line` | docstring | Return a compact first docstring line when a definition has one. |
| 33 | `function` | `_fallback_summary` | docstring | Build an inventory-backed summary for a definition without a docstring. |
| 38 | `function` | `_definition_kind` | docstring | Normalize AST node types into report-friendly definition kinds. |
| 47 | `class` | `_DefinitionVisitor` | docstring | Collect definitions while preserving nested qualified names. |
| 50 | `function` | `_DefinitionVisitor.__init__` | inventory fallback | Inventory fallback for function `_DefinitionVisitor.__init__` defined at `src/gates/method_inventory.py:50`. |
| 55 | `function` | `_DefinitionVisitor.visit_ClassDef` | inventory fallback | Inventory fallback for function `_DefinitionVisitor.visit_ClassDef` defined at `src/gates/method_inventory.py:55`. |
| 61 | `function` | `_DefinitionVisitor.visit_FunctionDef` | inventory fallback | Inventory fallback for function `_DefinitionVisitor.visit_FunctionDef` defined at `src/gates/method_inventory.py:61`. |
| 67 | `function` | `_DefinitionVisitor.visit_AsyncFunctionDef` | inventory fallback | Inventory fallback for function `_DefinitionVisitor.visit_AsyncFunctionDef` defined at `src/gates/method_inventory.py:67`. |
| 73 | `function` | `_DefinitionVisitor._record` | inventory fallback | Inventory fallback for function `_DefinitionVisitor._record` defined at `src/gates/method_inventory.py:73`. |
| 89 | `function` | `_source_files` | docstring | Return Python files in the documentation inventory scope. |
| 100 | `function` | `_path_sort_key` | docstring | Sort inventory paths by declared source-root order, then by path. |
| 110 | `function` | `collect_method_entries` | docstring | Collect every class/function definition under source modules and scripts. |
| 123 | `function` | `_escape_cell` | docstring | Escape Markdown table cells without changing the underlying value. |
| 128 | `function` | `render_method_inventory_markdown` | docstring | Render method inventory entries as a grouped Markdown reference. |
| 172 | `function` | `write_method_inventory` | docstring | Write the method inventory Markdown report and return its path. |

## `src/gates/output_checks.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 41 | `function` | `_read_json` | inventory fallback | Inventory fallback for function `_read_json` defined at `src/gates/output_checks.py:41`. |
| 51 | `function` | `_as_float` | inventory fallback | Inventory fallback for function `_as_float` defined at `src/gates/output_checks.py:51`. |
| 58 | `function` | `_as_int` | inventory fallback | Inventory fallback for function `_as_int` defined at `src/gates/output_checks.py:58`. |
| 78 | `function` | `_float_field_equals` | inventory fallback | Inventory fallback for function `_float_field_equals` defined at `src/gates/output_checks.py:78`. |
| 84 | `function` | `_firstprinciples_empirical_benchmark_ok` | inventory fallback | Inventory fallback for function `_firstprinciples_empirical_benchmark_ok` defined at `src/gates/output_checks.py:84`. |
| 127 | `function` | `_firstprinciples_taxonomy_ok` | inventory fallback | Inventory fallback for function `_firstprinciples_taxonomy_ok` defined at `src/gates/output_checks.py:127`. |
| 146 | `function` | `_firstprinciples_sequential_shift_ok` | inventory fallback | Inventory fallback for function `_firstprinciples_sequential_shift_ok` defined at `src/gates/output_checks.py:146`. |
| 152 | `function` | `_firstprinciples_sequential_shift_sensitivity_ok` | inventory fallback | Inventory fallback for function `_firstprinciples_sequential_shift_sensitivity_ok` defined at `src/gates/output_checks.py:152`. |
| 158 | `function` | `_pymdp_logging_expected` | inventory fallback | Inventory fallback for function `_pymdp_logging_expected` defined at `src/gates/output_checks.py:158`. |
| 168 | `function` | `_efe_values_explained` | inventory fallback | Inventory fallback for function `_efe_values_explained` defined at `src/gates/output_checks.py:168`. |
| 177 | `function` | `_si_invariants_all_pass_ok` | inventory fallback | Inventory fallback for function `_si_invariants_all_pass_ok` defined at `src/gates/output_checks.py:177`. |
| 182 | `function` | `_si_efe_rows_explained` | inventory fallback | Inventory fallback for function `_si_efe_rows_explained` defined at `src/gates/output_checks.py:182`. |
| 206 | `function` | `_gate_index_binding` | docstring | Every indexed gate-index row must bind to the live validator surface. |
| 229 | `function` | `_figure_source_map_ok` | inventory fallback | Inventory fallback for function `_figure_source_map_ok` defined at `src/gates/output_checks.py:229`. |
| 239 | `function` | `_figure_hash_manifest_ok` | inventory fallback | Inventory fallback for function `_figure_hash_manifest_ok` defined at `src/gates/output_checks.py:239`. |
| 249 | `function` | `_visualization_quality_audit_ok` | inventory fallback | Inventory fallback for function `_visualization_quality_audit_ok` defined at `src/gates/output_checks.py:249`. |
| 279 | `function` | `_figure_output_integrity_ok` | inventory fallback | Inventory fallback for function `_figure_output_integrity_ok` defined at `src/gates/output_checks.py:279`. |
| 321 | `function` | `_proof_extraction_ok` | inventory fallback | Inventory fallback for function `_proof_extraction_ok` defined at `src/gates/output_checks.py:321`. |
| 341 | `function` | `_ontology_profile_ok` | inventory fallback | Inventory fallback for function `_ontology_profile_ok` defined at `src/gates/output_checks.py:341`. |
| 370 | `function` | `_cross_track_symbol_table_ok` | inventory fallback | Inventory fallback for function `_cross_track_symbol_table_ok` defined at `src/gates/output_checks.py:370`. |
| 410 | `function` | `_firstprinciples_classroom_ok` | inventory fallback | Inventory fallback for function `_firstprinciples_classroom_ok` defined at `src/gates/output_checks.py:410`. |
| 416 | `function` | `_validate_outputs_selected` | inventory fallback | Inventory fallback for function `_validate_outputs_selected` defined at `src/gates/output_checks.py:416`. |
| 592 | `function` | `validate_outputs_selected_strict` | docstring | Validate selected output keys without falling back to the full gate. |
| 611 | `function` | `validate_outputs` | inventory fallback | Inventory fallback for function `validate_outputs` defined at `src/gates/output_checks.py:611`. |
| 622 | `function` | `_validate_outputs_full` | inventory fallback | Inventory fallback for function `_validate_outputs_full` defined at `src/gates/output_checks.py:622`. |

## `src/gnn/concordance.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 34 | `function` | `parity_gaps` | docstring | Report concordance gaps between GNN symbols and their ontology annotations. |
| 61 | `function` | `concordance_holds` | inventory fallback | Inventory fallback for function `concordance_holds` defined at `src/gnn/concordance.py:61`. |

## `src/gnn/model.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 14 | `class` | `GnnVariable` | inventory fallback | Inventory fallback for class `GnnVariable` defined at `src/gnn/model.py:14`. |
| 22 | `function` | `GnnVariable.size` | inventory fallback | Inventory fallback for function `GnnVariable.size` defined at `src/gnn/model.py:22`. |
| 30 | `class` | `GnnConnection` | inventory fallback | Inventory fallback for class `GnnConnection` defined at `src/gnn/model.py:30`. |
| 38 | `class` | `GnnModel` | inventory fallback | Inventory fallback for class `GnnModel` defined at `src/gnn/model.py:38`. |
| 50 | `function` | `GnnModel.variable` | inventory fallback | Inventory fallback for function `GnnModel.variable` defined at `src/gnn/model.py:50`. |
| 55 | `function` | `GnnModel.has` | inventory fallback | Inventory fallback for function `GnnModel.has` defined at `src/gnn/model.py:55`. |

## `src/gnn/parser.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 25 | `class` | `GNNParseError` | docstring | Raised on structural GNN parse failures. |
| 29 | `function` | `_split_sections` | inventory fallback | Inventory fallback for function `_split_sections` defined at `src/gnn/parser.py:29`. |
| 47 | `function` | `_section` | inventory fallback | Inventory fallback for function `_section` defined at `src/gnn/parser.py:47`. |
| 54 | `function` | `_parse_dims_and_type` | inventory fallback | Inventory fallback for function `_parse_dims_and_type` defined at `src/gnn/parser.py:54`. |
| 76 | `function` | `_parse_state_space` | inventory fallback | Inventory fallback for function `_parse_state_space` defined at `src/gnn/parser.py:76`. |
| 91 | `function` | `_parse_connections` | inventory fallback | Inventory fallback for function `_parse_connections` defined at `src/gnn/parser.py:91`. |
| 111 | `function` | `_strip_comment_lines` | inventory fallback | Inventory fallback for function `_strip_comment_lines` defined at `src/gnn/parser.py:111`. |
| 115 | `function` | `_parse_param_blocks` | inventory fallback | Inventory fallback for function `_parse_param_blocks` defined at `src/gnn/parser.py:115`. |
| 148 | `function` | `_parse_kv` | inventory fallback | Inventory fallback for function `_parse_kv` defined at `src/gnn/parser.py:148`. |
| 164 | `function` | `parse_gnn` | inventory fallback | Inventory fallback for function `parse_gnn` defined at `src/gnn/parser.py:164`. |
| 195 | `function` | `parse_gnn_file` | inventory fallback | Inventory fallback for function `parse_gnn_file` defined at `src/gnn/parser.py:195`. |

## `src/manuscript/hydrate.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 17 | `function` | `format_variables` | docstring | Stringify variable values for manuscript substitution. |
| 44 | `function` | `collect_manuscript_tokens` | docstring | Return token names referenced as {{name}}, {{name:.4f}}, or {{name:.1e}} in markdown. |
| 49 | `function` | `collect_single_brace_tokens` | docstring | Return snake_case names in single-brace {name} form (likely typos). |
| 54 | `function` | `collect_malformed_token_names` | docstring | Return token-like names that are not valid double-brace placeholders. |
| 60 | `function` | `collect_tokens_in_directory` | inventory fallback | Inventory fallback for function `collect_tokens_in_directory` defined at `src/manuscript/hydrate.py:60`. |
| 69 | `function` | `validate_manuscript_tokens` | docstring | Return sorted unknown token names referenced under manuscript_dir. |
| 78 | `function` | `substitute_snake_case_tokens` | inventory fallback | Inventory fallback for function `substitute_snake_case_tokens` defined at `src/manuscript/hydrate.py:78`. |
| 84 | `function` | `substitute_snake_case_tokens._replace` | inventory fallback | Inventory fallback for function `substitute_snake_case_tokens._replace` defined at `src/manuscript/hydrate.py:84`. |
| 103 | `function` | `write_resolved_manuscript` | docstring | Write token-substituted markdown copies to output/manuscript/. |

## `src/manuscript/invariant_counts.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 11 | `function` | `load_invariant_counts` | docstring | Return passed/total invariant counts from merged reports when present. |
| 31 | `function` | `invariants_are_merged` | docstring | True when the report contains genuine *simulation* invariants by content. |

## `src/manuscript/pdf_render.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 19 | `function` | `_tex_escape` | docstring | Escape the LaTeX special characters that occur in metadata strings. |
| 36 | `function` | `build_cover_tex` | docstring | Build a standalone title page: title, subtitle, author block, graphical abstract. |
| 95 | `function` | `render_pdf` | docstring | Compose, hydrate, and render the canonical manuscript PDF. |

## `src/manuscript/render_helpers.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 16 | `function` | `extract_preamble` | docstring | Return the LaTeX inside the ```latex fence of preamble.md (or ""). |
| 28 | `function` | `geometry_string` | docstring | Read page geometry from ``manuscript/config.yaml``; fall back to 0.5 in margins. |

## `src/manuscript/sheaf/cli.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 22 | `function` | `build_parser` | docstring | Build the sheaf composition command parser. |
| 77 | `function` | `_emit_issues` | inventory fallback | Inventory fallback for function `_emit_issues` defined at `src/manuscript/sheaf/cli.py:77`. |
| 82 | `function` | `_coverage_paths` | inventory fallback | Inventory fallback for function `_coverage_paths` defined at `src/manuscript/sheaf/cli.py:82`. |
| 89 | `function` | `_emit_coverage` | inventory fallback | Inventory fallback for function `_emit_coverage` defined at `src/manuscript/sheaf/cli.py:89`. |
| 113 | `function` | `run_compose_cli` | docstring | Run the sheaf composition CLI for ``project_root``. |

## `src/manuscript/sheaf/compose.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 24 | `function` | `issues_have_errors` | inventory fallback | Inventory fallback for function `issues_have_errors` defined at `src/manuscript/sheaf/compose.py:24`. |
| 28 | `function` | `validate_manifest` | inventory fallback | Inventory fallback for function `validate_manifest` defined at `src/manuscript/sheaf/compose.py:28`. |
| 104 | `function` | `sheaf_law_issues` | docstring | Surface sheaf-law violations as error-level manifest issues for the strict gate. |
| 113 | `function` | `_imrad_group_titles` | inventory fallback | Inventory fallback for function `_imrad_group_titles` defined at `src/manuscript/sheaf/compose.py:113`. |
| 121 | `function` | `_imrad_divider_markdown` | inventory fallback | Inventory fallback for function `_imrad_divider_markdown` defined at `src/manuscript/sheaf/compose.py:121`. |
| 131 | `function` | `compose_section` | inventory fallback | Inventory fallback for function `compose_section` defined at `src/manuscript/sheaf/compose.py:131`. |
| 164 | `function` | `compose_all_sections` | inventory fallback | Inventory fallback for function `compose_all_sections` defined at `src/manuscript/sheaf/compose.py:164`. |

## `src/manuscript/sheaf/counts.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 12 | `function` | `structural_counts` | docstring | Counts derived from sheaf manifest, registry, and coverage matrix. |

## `src/manuscript/sheaf/coverage.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 24 | `class` | `SheafCoverageContext` | docstring | Loaded manifest, track registry, and the coverage matrix built from them. |
| 32 | `function` | `load_sheaf_coverage_context` | docstring | Load manifest.yaml and the track registry, build the coverage matrix, and return them as a context. |
| 49 | `function` | `classify_cell` | docstring | Classify one cell: unbound -> (absent, white); bound and file exists -> (present, black); else (missing, gray). |
| 64 | `function` | `build_coverage_matrix` | docstring | Build the section-by-track CoverageMatrix by classifying every manifest binding against files on disk. |
| 108 | `function` | `coverage_matrix_to_dict` | docstring | Return the JSON-serializable dict form of a CoverageMatrix (tracks plus per-section cell records). |
| 136 | `function` | `write_coverage_json` | docstring | Write the coverage matrix as indented JSON to path, skipping the write when content is unchanged. |
| 150 | `function` | `load_coverage_json` | docstring | Load a previously written coverage JSON file and return its dict payload. |
| 156 | `function` | `validate_coverage_strict` | docstring | Return one error-level coverage_missing issue per gray (bound-but-absent) cell in the matrix. |
| 170 | `function` | `gray_cell_count` | docstring | Return the number of gray (bound-but-missing) cells in the matrix. |
| 175 | `function` | `gray_cell_count_from_json` | docstring | Return the number of gray cells recorded in a coverage JSON payload. |
| 185 | `function` | `validate_coverage_json_data` | docstring | Validate a coverage JSON payload against the manifest and registry: track/section counts and zero gray cells. |
| 222 | `function` | `emit_coverage_artifacts` | docstring | Build matrix from live manifest/registry and write coverage JSON only. |

## `src/manuscript/sheaf/laws.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 67 | `class` | `SheafLaw` | docstring | The structural laws that make the coverage presheaf a sheaf. |
| 79 | `class` | `LawViolation` | docstring | A single counter-example to one sheaf law. |
| 88 | `class` | `SheafLawReport` | docstring | Structured result of verifying the sheaf laws against a manifest. |
| 95 | `function` | `SheafLawReport.ok` | inventory fallback | Inventory fallback for function `SheafLawReport.ok` defined at `src/manuscript/sheaf/laws.py:95`. |
| 98 | `function` | `SheafLawReport.for_law` | inventory fallback | Inventory fallback for function `SheafLawReport.for_law` defined at `src/manuscript/sheaf/laws.py:98`. |
| 101 | `function` | `SheafLawReport.law_ok` | inventory fallback | Inventory fallback for function `SheafLawReport.law_ok` defined at `src/manuscript/sheaf/laws.py:101`. |
| 105 | `function` | `SheafLawReport.passed_laws` | inventory fallback | Inventory fallback for function `SheafLawReport.passed_laws` defined at `src/manuscript/sheaf/laws.py:105`. |
| 109 | `function` | `SheafLawReport.summary` | inventory fallback | Inventory fallback for function `SheafLawReport.summary` defined at `src/manuscript/sheaf/laws.py:109`. |
| 115 | `function` | `_known_renderers` | inventory fallback | Inventory fallback for function `_known_renderers` defined at `src/manuscript/sheaf/laws.py:115`. |
| 120 | `function` | `_composing_sections` | inventory fallback | Inventory fallback for function `_composing_sections` defined at `src/manuscript/sheaf/laws.py:120`. |
| 124 | `function` | `_check_poset` | docstring | IMRAD blocks form a chain; compose order is monotone in block rank. |
| 168 | `function` | `_check_presheaf` | docstring | Bound tracks are registered; track order restricts the global order. |
| 224 | `function` | `_check_separation` | docstring | s ↦ output_name is injective over composing sections. |
| 253 | `function` | `_check_gluing` | docstring | Compose order is a strict linear extension; each section glues once. |
| 292 | `function` | `_check_typing` | docstring | Each binding is well-typed: renderer exists and suffix is accepted. |
| 331 | `function` | `_check_compositionality` | docstring | Every fragment file is private to one section (composition is a coproduct). |
| 362 | `function` | `verify_sheaf_laws` | docstring | Verify all sheaf laws against the live (or supplied) manifest + registry. |
| 388 | `function` | `sheaf_law_violations` | docstring | Pure law check against in-memory manifest + registry (no filesystem load). |

## `src/manuscript/sheaf/layers_report.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 12 | `function` | `render_track_registry_table` | docstring | Render the track-registry markdown table (order, id, label, renderer, optional) with a {{sheaf_track_count}} token. |
| 32 | `function` | `render_binding_matrix_table` | docstring | Render the IMRAD binding-matrix markdown table of P/—/M symbols per section row and track column. |
| 69 | `function` | `render_coverage_legend` | docstring | Render the legend table mapping P/—/M symbols to coverage colors and meanings. |
| 84 | `function` | `render_evidence_crosswalk_table` | docstring | Render the evidence-crosswalk markdown table (first 8 claims: id, artifact, producer, gates). |
| 103 | `function` | `render_artifact_producer_table` | docstring | Render the artifact-producer markdown table for output/data, output/reports, and the belief-trajectory GIF. |
| 128 | `function` | `render_semantic_restrictions_table` | docstring | Render the semantic-gluing restrictions markdown table from the certificate, showing 'not evaluated' for None values. |
| 132 | `function` | `render_semantic_restrictions_table._cell` | inventory fallback | Inventory fallback for function `render_semantic_restrictions_table._cell` defined at `src/manuscript/sheaf/layers_report.py:132`. |
| 184 | `function` | `render_track_improvement_scope_table` | docstring | Render the track-improvement-scope markdown table from output/data/track_improvement_scope.json, noting truncation. |
| 218 | `function` | `render_section_status_table` | docstring | Render the per-section status markdown table (bound/present/missing counts) for composable sections only. |
| 252 | `function` | `render_track_status_table` | docstring | Render the per-track status markdown table (renderer, bound/present/missing section counts, claims). |
| 275 | `function` | `render_sheaf_render_log_table` | docstring | Render the render/logging event markdown table from the sheaf render log. |
| 297 | `function` | `render_sheaf_layers_markdown` | docstring | Render the full sheaf-layers markdown page by concatenating all registry, matrix, status, and semantic tables. |

## `src/manuscript/sheaf/manifest.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 23 | `function` | `parse_missing` | inventory fallback | Inventory fallback for function `parse_missing` defined at `src/manuscript/sheaf/manifest.py:23`. |
| 32 | `function` | `load_manifest` | inventory fallback | Inventory fallback for function `load_manifest` defined at `src/manuscript/sheaf/manifest.py:32`. |
| 104 | `function` | `_load_manifest_yaml_cached` | inventory fallback | Inventory fallback for function `_load_manifest_yaml_cached` defined at `src/manuscript/sheaf/manifest.py:104`. |
| 109 | `function` | `default_manifest_path` | inventory fallback | Inventory fallback for function `default_manifest_path` defined at `src/manuscript/sheaf/manifest.py:109`. |

## `src/manuscript/sheaf/models.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 14 | `function` | `coverage_cell_symbol` | docstring | Return the coverage-table symbol for a cell color: "P" (black), "M" (gray), or em dash (white). |
| 27 | `class` | `MissingTrackPolicy` | docstring | Policy for handling a section track with no bound source file: skip, warn, or error. |
| 36 | `class` | `TrackSpec` | docstring | Registry entry for one manuscript track: id, ordering, renderer name, label, and optional flag. |
| 47 | `class` | `SheafDefaults` | docstring | Manifest-level defaults, currently the missing-track policy. |
| 54 | `class` | `SheafSection` | docstring | One manifest section: identity, IMRaD placement, track-to-path bindings, and compose controls. |
| 71 | `function` | `SheafSection.should_compose` | inventory fallback | Inventory fallback for function `SheafSection.should_compose` defined at `src/manuscript/sheaf/models.py:71`. |
| 76 | `class` | `SheafManifest` | docstring | Parsed sheaf manifest: defaults, ordered sections, and the track-registry path. |
| 85 | `class` | `ManifestIssue` | docstring | Diagnostic raised during manifest validation or composition: level, code, and message. |
| 94 | `class` | `ComposeOptions` | docstring | Options for a compose run: track/section filters, missing-track override, and strict mode. |
| 104 | `class` | `TrackRegistry` | docstring | Loaded track registry: TrackSpec by id plus renderer filename-suffix mapping. |
| 112 | `class` | `ComposeResult` | docstring | Result of composing sections: written output paths and any issues raised. |
| 120 | `class` | `CoverageCell` | docstring | One section-by-track coverage cell: binding, source path, status, and display color. |
| 131 | `class` | `CoverageSectionRow` | docstring | Coverage-matrix row for one section: its cells plus kind, IMRaD block, depth, and compose flag. |
| 144 | `class` | `CoverageMatrix` | docstring | Full section-by-track coverage matrix with a helper listing gray (missing) cells. |
| 150 | `function` | `CoverageMatrix.gray_cells` | inventory fallback | Inventory fallback for function `CoverageMatrix.gray_cells` defined at `src/manuscript/sheaf/models.py:150`. |

## `src/manuscript/sheaf/registry.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 13 | `function` | `load_track_registry` | inventory fallback | Inventory fallback for function `load_track_registry` defined at `src/manuscript/sheaf/registry.py:13`. |
| 38 | `function` | `_load_registry_yaml_cached` | inventory fallback | Inventory fallback for function `_load_registry_yaml_cached` defined at `src/manuscript/sheaf/registry.py:38`. |
| 43 | `function` | `track_order_for_section` | inventory fallback | Inventory fallback for function `track_order_for_section` defined at `src/manuscript/sheaf/registry.py:43`. |
| 61 | `function` | `list_registered_tracks` | inventory fallback | Inventory fallback for function `list_registered_tracks` defined at `src/manuscript/sheaf/registry.py:61`. |

## `src/manuscript/sheaf/renderers.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 18 | `function` | `_render_ontology` | inventory fallback | Inventory fallback for function `_render_ontology` defined at `src/manuscript/sheaf/renderers.py:18`. |
| 35 | `function` | `_require_track_spec` | inventory fallback | Inventory fallback for function `_require_track_spec` defined at `src/manuscript/sheaf/renderers.py:35`. |
| 42 | `function` | `render_track_body` | inventory fallback | Inventory fallback for function `render_track_body` defined at `src/manuscript/sheaf/renderers.py:42`. |
| 50 | `function` | `_resolve_section_figures` | inventory fallback | Inventory fallback for function `_resolve_section_figures` defined at `src/manuscript/sheaf/renderers.py:50`. |
| 69 | `function` | `_resolve_layers_report` | inventory fallback | Inventory fallback for function `_resolve_layers_report` defined at `src/manuscript/sheaf/renderers.py:69`. |
| 89 | `function` | `resolve_track_body` | docstring | Resolve composed markdown for one bound track. |
| 104 | `function` | `validate_renderer_specs` | inventory fallback | Inventory fallback for function `validate_renderer_specs` defined at `src/manuscript/sheaf/renderers.py:104`. |

## `src/manuscript/sheaf/report.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `class` | `HeatmapConfig` | docstring | Coverage-heatmap rendering settings: indentation, separators, row height, DPI, and percentage display. |
| 26 | `class` | `CoverageColorConfig` | docstring | Hex colors for present, absent, and missing coverage cells. |
| 35 | `class` | `ReportConfig` | docstring | Coverage-page settings: title, section toggles, and the heatmap figure path. |
| 46 | `class` | `CoverageConfig` | docstring | Combined coverage configuration: report, heatmap, and color settings. |
| 55 | `class` | `CoverageReport` | docstring | Coverage matrix plus aggregated bound/present/missing totals and per-section row stats. |
| 67 | `function` | `load_coverage_config` | docstring | Load CoverageConfig from a YAML file, falling back to defaults when absent. |
| 118 | `function` | `default_coverage_config_path` | docstring | Return the default manuscript/sheaf/coverage.yaml path under the project root. |
| 123 | `function` | `build_coverage_report` | docstring | Aggregate per-section bound/present/missing counts from the matrix into a CoverageReport. |
| 155 | `function` | `_imrad_heading` | inventory fallback | Inventory fallback for function `_imrad_heading` defined at `src/manuscript/sheaf/report.py:155`. |
| 159 | `function` | `render_report_markdown` | docstring | Render the sheaf coverage page markdown (totals, legend, IMRAD outline, registered figures). |
| 217 | `function` | `write_coverage_page` | docstring | Build the coverage report from the live manifest and write manuscript/00_00_sheaf_coverage.md. |

## `src/manuscript/sheaf/semantic.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 34 | `function` | `_rel` | inventory fallback | Inventory fallback for function `_rel` defined at `src/manuscript/sheaf/semantic.py:34`. |
| 38 | `function` | `_load_json` | inventory fallback | Inventory fallback for function `_load_json` defined at `src/manuscript/sheaf/semantic.py:38`. |
| 45 | `function` | `_validation_spine_saved_ok` | inventory fallback | Inventory fallback for function `_validation_spine_saved_ok` defined at `src/manuscript/sheaf/semantic.py:45`. |
| 59 | `function` | `_configured_analysis_scripts` | inventory fallback | Inventory fallback for function `_configured_analysis_scripts` defined at `src/manuscript/sheaf/semantic.py:59`. |
| 71 | `function` | `_claims_by_path` | inventory fallback | Inventory fallback for function `_claims_by_path` defined at `src/manuscript/sheaf/semantic.py:71`. |
| 81 | `function` | `_animation_frame_count` | inventory fallback | Inventory fallback for function `_animation_frame_count` defined at `src/manuscript/sheaf/semantic.py:81`. |
| 94 | `function` | `_lean_status` | inventory fallback | Inventory fallback for function `_lean_status` defined at `src/manuscript/sheaf/semantic.py:94`. |
| 109 | `function` | `_policy_comparison_restrictions` | inventory fallback | Inventory fallback for function `_policy_comparison_restrictions` defined at `src/manuscript/sheaf/semantic.py:109`. |
| 124 | `function` | `_policy_posterior_restrictions` | inventory fallback | Inventory fallback for function `_policy_posterior_restrictions` defined at `src/manuscript/sheaf/semantic.py:124`. |
| 134 | `function` | `_runtime_diagnostics_restrictions` | inventory fallback | Inventory fallback for function `_runtime_diagnostics_restrictions` defined at `src/manuscript/sheaf/semantic.py:134`. |
| 144 | `function` | `_restriction_class` | inventory fallback | Inventory fallback for function `_restriction_class` defined at `src/manuscript/sheaf/semantic.py:144`. |
| 180 | `function` | `_obligation_artifacts` | inventory fallback | Inventory fallback for function `_obligation_artifacts` defined at `src/manuscript/sheaf/semantic.py:180`. |
| 194 | `function` | `_proof_obligations` | inventory fallback | Inventory fallback for function `_proof_obligations` defined at `src/manuscript/sheaf/semantic.py:194`. |
| 244 | `function` | `_with_proof_obligations` | inventory fallback | Inventory fallback for function `_with_proof_obligations` defined at `src/manuscript/sheaf/semantic.py:244`. |
| 256 | `function` | `_graph_world_restrictions` | inventory fallback | Inventory fallback for function `_graph_world_restrictions` defined at `src/manuscript/sheaf/semantic.py:256`. |
| 269 | `function` | `_pymdp_hash_restrictions` | inventory fallback | Inventory fallback for function `_pymdp_hash_restrictions` defined at `src/manuscript/sheaf/semantic.py:269`. |
| 278 | `function` | `_gnn_symbols` | inventory fallback | Inventory fallback for function `_gnn_symbols` defined at `src/manuscript/sheaf/semantic.py:278`. |
| 285 | `function` | `_section_ontology_symbols` | inventory fallback | Inventory fallback for function `_section_ontology_symbols` defined at `src/manuscript/sheaf/semantic.py:285`. |
| 290 | `function` | `_expected_symbol_gaps` | inventory fallback | Inventory fallback for function `_expected_symbol_gaps` defined at `src/manuscript/sheaf/semantic.py:290`. |
| 314 | `function` | `semantic_gluing_issues` | docstring | Return semantic cross-track disagreements not covered by structural laws. |
| 457 | `function` | `_section_records` | inventory fallback | Inventory fallback for function `_section_records` defined at `src/manuscript/sheaf/semantic.py:457`. |
| 483 | `function` | `_claim_records` | inventory fallback | Inventory fallback for function `_claim_records` defined at `src/manuscript/sheaf/semantic.py:483`. |
| 505 | `function` | `build_evidence_crosswalk` | docstring | Build a claim-to-artifact crosswalk from the typed claim ledger. |
| 527 | `function` | `build_validation_dependency_graph` | docstring | Build script → artifact → manuscript/gate dependency records. |
| 534 | `function` | `validate_configured_artifact_producers` | docstring | Fail when required generated artifacts lack configured analysis producers. |
| 550 | `function` | `build_semantic_gluing_certificate` | docstring | Build a JSON-serializable semantic certificate from live project state. |
| 791 | `function` | `write_semantic_gluing_certificate` | inventory fallback | Inventory fallback for function `write_semantic_gluing_certificate` defined at `src/manuscript/sheaf/semantic.py:791`. |
| 820 | `function` | `_refresh_hydrated_manuscript` | docstring | Refresh composed and hydrated manuscript artifacts for semantic checks. |
| 837 | `function` | `write_semantic_gluing_outputs` | docstring | Write semantic certificate, evidence crosswalk, and dependency graph outputs. |
| 881 | `function` | `_stable_artifact_graph` | inventory fallback | Inventory fallback for function `_stable_artifact_graph` defined at `src/manuscript/sheaf/semantic.py:881`. |
| 893 | `function` | `_stable_certificate_fields` | inventory fallback | Inventory fallback for function `_stable_certificate_fields` defined at `src/manuscript/sheaf/semantic.py:893`. |
| 904 | `function` | `validate_semantic_gluing` | docstring | Validate the live semantic certificate and its generated artifact. |

## `src/manuscript/sheaf/status.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 18 | `function` | `_load_yaml` | inventory fallback | Inventory fallback for function `_load_yaml` defined at `src/manuscript/sheaf/status.py:18`. |
| 25 | `function` | `_claim_indexes` | inventory fallback | Inventory fallback for function `_claim_indexes` defined at `src/manuscript/sheaf/status.py:25`. |
| 52 | `function` | `_artifact_indexes` | inventory fallback | Inventory fallback for function `_artifact_indexes` defined at `src/manuscript/sheaf/status.py:52`. |
| 73 | `function` | `build_sheaf_section_status_matrix` | docstring | Build one explicit status row for every section x registered-track cell. |
| 199 | `function` | `build_sheaf_render_log` | docstring | Build a deterministic render/log summary for the sheaf manuscript layer. |
| 285 | `function` | `validate_sheaf_status_outputs` | inventory fallback | Inventory fallback for function `validate_sheaf_status_outputs` defined at `src/manuscript/sheaf/status.py:285`. |
| 311 | `function` | `write_sheaf_status_outputs` | inventory fallback | Inventory fallback for function `write_sheaf_status_outputs` defined at `src/manuscript/sheaf/status.py:311`. |

## `src/manuscript/variables.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 18 | `function` | `_rederived_aggregate_rule_count` | docstring | Count of (artifact, aggregate) pairs re-derived from rows at validation time. |
| 25 | `function` | `_ising_mi_saturation_from_sweep` | docstring | Maximum closed-form MI on the measured λ grid (nats). |
| 32 | `function` | `_free_energy_sweep_summary` | docstring | Summary for the exact-target and mean-field free-energy comparison. |
| 87 | `function` | `_free_energy_argmin_lambda` | docstring | λ minimizing the mean-field free-energy gap on the configured sweep. |
| 92 | `function` | `_policy_goal_counts_by_planner` | docstring | Goal-reaching counts split by planner from comparison-only rows. |
| 102 | `function` | `_load_json` | inventory fallback | Inventory fallback for function `_load_json` defined at `src/manuscript/variables.py:102`. |
| 112 | `function` | `_pipeline_track_count` | docstring | Required pipeline tracks from ``tracks.yaml`` (distinct from ``sheaf_track_count``). |
| 122 | `function` | `_gnn_spec_version` | inventory fallback | Inventory fallback for function `_gnn_spec_version` defined at `src/manuscript/variables.py:122`. |
| 138 | `function` | `generate_variables` | inventory fallback | Inventory fallback for function `generate_variables` defined at `src/manuscript/variables.py:138`. |

## `src/ontology/bindings.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 57 | `function` | `load_section_ontology` | inventory fallback | Inventory fallback for function `load_section_ontology` defined at `src/ontology/bindings.py:57`. |
| 73 | `function` | `validate_gnn_ontology` | inventory fallback | Inventory fallback for function `validate_gnn_ontology` defined at `src/ontology/bindings.py:73`. |
| 87 | `function` | `_validate_section_ontology_exact` | inventory fallback | Inventory fallback for function `_validate_section_ontology_exact` defined at `src/ontology/bindings.py:87`. |
| 104 | `function` | `validate_all_gnn_ontology` | docstring | Validate every project GNN model against its model-specific ontology map. |

## `src/orchestration/analysis.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 18 | `function` | `write_parameter_sweep` | inventory fallback | Inventory fallback for function `write_parameter_sweep` defined at `src/orchestration/analysis.py:18`. |
| 39 | `function` | `write_invariants_report` | inventory fallback | Inventory fallback for function `write_invariants_report` defined at `src/orchestration/analysis.py:39`. |
| 53 | `function` | `summarize_sweep` | inventory fallback | Inventory fallback for function `summarize_sweep` defined at `src/orchestration/analysis.py:53`. |
| 58 | `function` | `write_analysis_statistics` | inventory fallback | Inventory fallback for function `write_analysis_statistics` defined at `src/orchestration/analysis.py:58`. |
| 91 | `function` | `run_analysis` | inventory fallback | Inventory fallback for function `run_analysis` defined at `src/orchestration/analysis.py:91`. |

## `src/orchestration/artifact_pipeline.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `refresh_analysis_artifacts` | docstring | Refresh deterministic analysis, simulation, first-principles, and figure artifacts. |
| 59 | `function` | `refresh_promoted_track_artifacts` | docstring | Refresh validation-spine, roadmap, integration-audit, and canonical sheaf artifacts. |
| 82 | `function` | `_write_variables` | inventory fallback | Inventory fallback for function `_write_variables` defined at `src/orchestration/artifact_pipeline.py:82`. |
| 95 | `function` | `hydrate_manuscript_fixed_point` | docstring | Compose, hydrate, and regenerate semantic artifacts until validators converge. |
| 154 | `function` | `refresh_gate_artifacts` | docstring | Refresh the full artifact surface required by output and manuscript gates. |

## `src/orchestration/coverage_pipeline.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 11 | `function` | `_coverage_input_paths` | inventory fallback | Inventory fallback for function `_coverage_input_paths` defined at `src/orchestration/coverage_pipeline.py:11`. |
| 23 | `function` | `_is_stale` | inventory fallback | Inventory fallback for function `_is_stale` defined at `src/orchestration/coverage_pipeline.py:23`. |
| 30 | `function` | `run_coverage_figures_and_page` | docstring | Render heatmap PNG and coverage page from existing coverage JSON. |
| 48 | `function` | `ensure_coverage_artifacts` | docstring | Ensure coverage JSON exists; optionally render heatmap and coverage page. |
| 90 | `function` | `run_coverage_pipeline` | docstring | Write coverage JSON, heatmap PNG, and coverage manuscript page. |

## `src/orchestration/pipeline_manifest.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 10 | `function` | `analysis_scripts` | inventory fallback | Inventory fallback for function `analysis_scripts` defined at `src/orchestration/pipeline_manifest.py:10`. |

## `src/roadmap_tracks/formal_interop.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `_load_json` | inventory fallback | Inventory fallback for function `_load_json` defined at `src/roadmap_tracks/formal_interop.py:15`. |
| 22 | `function` | `_write_json` | inventory fallback | Inventory fallback for function `_write_json` defined at `src/roadmap_tracks/formal_interop.py:22`. |
| 28 | `function` | `_gnn_paths` | inventory fallback | Inventory fallback for function `_gnn_paths` defined at `src/roadmap_tracks/formal_interop.py:28`. |
| 32 | `function` | `_model_to_payload` | docstring | Structured, JSON-serializable view of a parsed GNN model (sorted, deterministic). |
| 54 | `function` | `_model_payload` | inventory fallback | Inventory fallback for function `_model_payload` defined at `src/roadmap_tracks/formal_interop.py:54`. |
| 58 | `function` | `_payload_to_gnn_text` | docstring | Serialize a model payload back to GNN markdown. |
| 98 | `function` | `roundtrip_payload_lossless` | docstring | True iff serializing the STRUCTURAL payload to GNN text and re-parsing reproduces it. |
| 116 | `function` | `build_model_checking_witnesses` | docstring | Model-checking witnesses derived from real finite enumeration + Lean binding. |
| 130 | `function` | `build_model_checking_witnesses._theorem_names` | inventory fallback | Inventory fallback for function `build_model_checking_witnesses._theorem_names` defined at `src/roadmap_tracks/formal_interop.py:130`. |
| 203 | `function` | `build_gnn_roundtrip_report` | docstring | Build the gnn_roundtrip_report.v1 payload: a parse-write-reparse losslessness row per gnn/*.gnn.md model. |
| 226 | `function` | `build_gnn_lint_report` | docstring | Build the gnn_lint_report.v1 payload: per-variable dtype/shape/ontology checks against the expected term maps. |
| 288 | `function` | `build_ontology_alias_index` | docstring | Build the ontology_alias_index.v1 payload from per-section ontology.yaml files, flagging conflicting alias terms. |
| 311 | `function` | `build_ontology_profile_matrix` | docstring | Build ontology_profile_matrix.v1 with true per-variable uniqueness checks. |
| 407 | `function` | `_lean_files` | inventory fallback | Inventory fallback for function `_lean_files` defined at `src/roadmap_tracks/formal_interop.py:407`. |
| 411 | `function` | `_lean_text` | inventory fallback | Inventory fallback for function `_lean_text` defined at `src/roadmap_tracks/formal_interop.py:411`. |
| 415 | `function` | `build_lean_theorem_inventory` | docstring | Build the lean_theorem_inventory.v1 payload: theorem names from lean/OnPolicyDistillation/*.lean plus a sorry/axiom/native_decide token scan. |
| 431 | `function` | `build_lean_graph_world_inventory` | docstring | Build the lean_graph_world_inventory.v1 payload: per-topology and policy-enumeration Lean witness presence checks. |
| 473 | `function` | `build_interop_roundtrip_report` | docstring | Build the interop_roundtrip_report.v1 payload combining GNN round-trip losslessness with ontology mapping completeness. |
| 498 | `function` | `_leading_tactic` | docstring | First tactic identifier in a proof body (after ``:= by``), skipping blanks/comments. |
| 510 | `function` | `_normalize_lean_statement` | docstring | Normalize theorem binders and conclusions captured before ``:= by``. |
| 516 | `function` | `_theorem_names` | inventory fallback | Inventory fallback for function `_theorem_names` defined at `src/roadmap_tracks/formal_interop.py:516`. |
| 520 | `function` | `proof_inventory_mismatch` | docstring | Theorem names present in Lean but absent from proof extraction, or vice versa. |
| 534 | `function` | `build_proof_extraction_index` | docstring | Build the proof_extraction_index.v1 payload: per-theorem statement and leading tactic extracted from the Lean sources, cross-checked against the theorem inventory. |
| 582 | `function` | `write_formal_interop_artifacts` | docstring | Write the nine formal-interop JSON artifacts under output/data/ and output/reports/. |
| 625 | `function` | `validate_formal_interop_artifacts` | docstring | Validate the written formal-interop artifacts (schemas, losslessness, proved theorems, staleness, inventory parity). |

## `src/roadmap_tracks/integration_audit.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 93 | `function` | `write_manuscript_staleness_report` | docstring | Write the hydrated-manuscript staleness report. |
| 102 | `function` | `write_integration_audit_artifacts` | inventory fallback | Inventory fallback for function `write_integration_audit_artifacts` defined at `src/roadmap_tracks/integration_audit.py:102`. |
| 177 | `function` | `validate_integration_audit_artifacts` | inventory fallback | Inventory fallback for function `validate_integration_audit_artifacts` defined at `src/roadmap_tracks/integration_audit.py:177`. |

## `src/roadmap_tracks/integration_audit_artifacts.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 35 | `function` | `build_artifact_diffoscope` | docstring | Build the artifact_diffoscope.v1 payload comparing saved provenance sha256 digests against live file hashes, skipping cycle-excluded producers. |
| 66 | `function` | `build_artifact_license_audit` | docstring | Build the artifact_license_audit.v1 payload labeling each provenance artifact with the project license and a license_safe flag. |
| 96 | `function` | `build_release_notes_evidence` | docstring | Build the release_notes_evidence.v1 payload: three source-backed release notes (validation report, bundle sources, semantic certificate), deferring rows whose source artifact does not exist yet. |
| 142 | `function` | `build_figure_source_map` | docstring | Build the figure_source_map.v1 payload: per-registry-figure sources, source fields, validation gates, caption/alt tokens, and image dimensions. |
| 149 | `function` | `build_figure_source_map._image_dimensions` | inventory fallback | Inventory fallback for function `build_figure_source_map._image_dimensions` defined at `src/roadmap_tracks/integration_audit_artifacts.py:149`. |
| 493 | `function` | `_actual_figure_image_paths` | inventory fallback | Inventory fallback for function `_actual_figure_image_paths` defined at `src/roadmap_tracks/integration_audit_artifacts.py:493`. |
| 504 | `function` | `_expected_figure_image_paths` | inventory fallback | Inventory fallback for function `_expected_figure_image_paths` defined at `src/roadmap_tracks/integration_audit_artifacts.py:504`. |
| 511 | `function` | `build_figure_hash_manifest` | docstring | Build the figure_hash_manifest.v1 payload for declared figure/animation images. |
| 600 | `function` | `_caption_overclaim_free` | inventory fallback | Inventory fallback for function `_caption_overclaim_free` defined at `src/roadmap_tracks/integration_audit_artifacts.py:600`. |
| 608 | `function` | `build_visualization_quality_audit` | docstring | Build a verifier-facing audit over figure readability, provenance, and caption scope. |
| 685 | `function` | `_figure_source_rows_complete` | inventory fallback | Inventory fallback for function `_figure_source_rows_complete` defined at `src/roadmap_tracks/integration_audit_artifacts.py:685`. |
| 775 | `function` | `_figure_hash_rows_complete` | inventory fallback | Inventory fallback for function `_figure_hash_rows_complete` defined at `src/roadmap_tracks/integration_audit_artifacts.py:775`. |
| 806 | `function` | `build_scope_boundary_audit` | docstring | Build the scope_boundary_audit.v1 payload scanning numbered manuscript sections for empirical-biological claims outside the allowed future-work files. |
| 840 | `function` | `build_manuscript_evidence_tables` | docstring | Build the manuscript_evidence_tables.v1 payload: an id/row_count/source index over twenty evidence artifacts. |
| 973 | `function` | `build_adversarial_audit` | docstring | Return a copy of the canonical adversarial audit from roadmap_tracks.sheaf_tracks. |
| 980 | `function` | `build_integration_semantic_snapshot` | docstring | Build the integration_semantic_snapshot.v1 payload: ~30 boolean restrictions over the saved artifacts plus structural/semantic/artifact/manuscript section rollups. |

## `src/roadmap_tracks/integration_audit_builders.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 33 | `function` | `_load_json` | inventory fallback | Inventory fallback for function `_load_json` defined at `src/roadmap_tracks/integration_audit_builders.py:33`. |
| 40 | `function` | `_write_json` | inventory fallback | Inventory fallback for function `_write_json` defined at `src/roadmap_tracks/integration_audit_builders.py:40`. |
| 46 | `function` | `_sha256` | inventory fallback | Inventory fallback for function `_sha256` defined at `src/roadmap_tracks/integration_audit_builders.py:46`. |
| 54 | `function` | `_analysis_scripts` | inventory fallback | Inventory fallback for function `_analysis_scripts` defined at `src/roadmap_tracks/integration_audit_builders.py:54`. |
| 59 | `function` | `build_integration_dependency_graph` | inventory fallback | Inventory fallback for function `build_integration_dependency_graph` defined at `src/roadmap_tracks/integration_audit_builders.py:59`. |
| 94 | `function` | `build_producer_completeness` | inventory fallback | Inventory fallback for function `build_producer_completeness` defined at `src/roadmap_tracks/integration_audit_builders.py:94`. |
| 115 | `function` | `build_stale_artifact_report` | inventory fallback | Inventory fallback for function `build_stale_artifact_report` defined at `src/roadmap_tracks/integration_audit_builders.py:115`. |
| 141 | `function` | `build_cross_track_symbol_table` | inventory fallback | Inventory fallback for function `build_cross_track_symbol_table` defined at `src/roadmap_tracks/integration_audit_builders.py:141`. |
| 307 | `function` | `build_manuscript_token_provenance` | inventory fallback | Inventory fallback for function `build_manuscript_token_provenance` defined at `src/roadmap_tracks/integration_audit_builders.py:307`. |
| 351 | `function` | `_literal_guarded` | docstring | Return whether a formatted variable value is specific enough to audit. |
| 364 | `function` | `_literal_pattern` | inventory fallback | Inventory fallback for function `_literal_pattern` defined at `src/roadmap_tracks/integration_audit_builders.py:364`. |
| 369 | `function` | `build_hardcoded_variable_audit` | docstring | Find generated variable values hard-coded in manuscript source. |
| 438 | `function` | `_expected_token_value` | inventory fallback | Inventory fallback for function `_expected_token_value` defined at `src/roadmap_tracks/integration_audit_builders.py:438`. |
| 451 | `function` | `build_manuscript_staleness_report` | docstring | Compare hydrated manuscript tokens against the current generated variables. |
| 523 | `function` | `build_claim_evidence_audit` | inventory fallback | Inventory fallback for function `build_claim_evidence_audit` defined at `src/roadmap_tracks/integration_audit_builders.py:523`. |
| 742 | `function` | `_rows_fully_specified` | inventory fallback | Inventory fallback for function `_rows_fully_specified` defined at `src/roadmap_tracks/integration_audit_builders.py:742`. |
| 748 | `function` | `build_validation_gate_index` | docstring | Index the validator surface with per-gate required inputs. |

## `src/roadmap_tracks/scholarship/matrix.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 21 | `function` | `_load_yaml` | inventory fallback | Inventory fallback for function `_load_yaml` defined at `src/roadmap_tracks/scholarship/matrix.py:21`. |
| 28 | `function` | `_write_json` | inventory fallback | Inventory fallback for function `_write_json` defined at `src/roadmap_tracks/scholarship/matrix.py:28`. |
| 34 | `function` | `_bib_entries` | inventory fallback | Inventory fallback for function `_bib_entries` defined at `src/roadmap_tracks/scholarship/matrix.py:34`. |
| 43 | `function` | `_bib_field` | inventory fallback | Inventory fallback for function `_bib_field` defined at `src/roadmap_tracks/scholarship/matrix.py:43`. |
| 50 | `function` | `_arxiv_id` | inventory fallback | Inventory fallback for function `_arxiv_id` defined at `src/roadmap_tracks/scholarship/matrix.py:50`. |
| 60 | `function` | `_manuscript_citation_text` | inventory fallback | Inventory fallback for function `_manuscript_citation_text` defined at `src/roadmap_tracks/scholarship/matrix.py:60`. |
| 69 | `function` | `_citation_present` | inventory fallback | Inventory fallback for function `_citation_present` defined at `src/roadmap_tracks/scholarship/matrix.py:69`. |
| 74 | `function` | `_registry_tracks` | inventory fallback | Inventory fallback for function `_registry_tracks` defined at `src/roadmap_tracks/scholarship/matrix.py:74`. |
| 79 | `function` | `_manifest_sections` | inventory fallback | Inventory fallback for function `_manifest_sections` defined at `src/roadmap_tracks/scholarship/matrix.py:79`. |
| 84 | `function` | `_has_locator` | inventory fallback | Inventory fallback for function `_has_locator` defined at `src/roadmap_tracks/scholarship/matrix.py:84`. |
| 89 | `function` | `build_scholarship_source_matrix` | docstring | Build the literature-to-method traceability matrix. |
| 147 | `function` | `write_scholarship_source_matrix` | docstring | Write the source-backed scholarship matrix. |
| 155 | `function` | `validate_scholarship_source_matrix_payload` | docstring | Validate an already-loaded scholarship-source matrix payload. |
| 183 | `function` | `validate_scholarship_source_matrix` | docstring | Validate the saved scholarship-source matrix against its row evidence. |

## `src/roadmap_tracks/sheaf_track_validation.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 12 | `function` | `_all_rows` | inventory fallback | Inventory fallback for function `_all_rows` defined at `src/roadmap_tracks/sheaf_track_validation.py:12`. |
| 17 | `function` | `_all_rows_absent` | inventory fallback | Inventory fallback for function `_all_rows_absent` defined at `src/roadmap_tracks/sheaf_track_validation.py:17`. |
| 22 | `function` | `_semantic_obligation_issues` | inventory fallback | Inventory fallback for function `_semantic_obligation_issues` defined at `src/roadmap_tracks/sheaf_track_validation.py:22`. |
| 75 | `function` | `load_sheaf_track_payloads` | docstring | Load the canonical artifact payload set once for cheap in-memory checks. |
| 86 | `function` | `_payload` | inventory fallback | Inventory fallback for function `_payload` defined at `src/roadmap_tracks/sheaf_track_validation.py:86`. |
| 94 | `function` | `validate_sheaf_track_payloads` | docstring | Validate already-loaded canonical sheaf-track payloads. |
| 112 | `function` | `validate_sheaf_track_artifacts` | docstring | Validate canonical sheaf-track artifacts and their semantic certificate. |
| 121 | `function` | `_validate_sheaf_track_artifacts` | inventory fallback | Inventory fallback for function `_validate_sheaf_track_artifacts` defined at `src/roadmap_tracks/sheaf_track_validation.py:121`. |

## `src/roadmap_tracks/sheaf_tracks.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 149 | `function` | `write_sheaf_track_artifacts` | inventory fallback | Inventory fallback for function `write_sheaf_track_artifacts` defined at `src/roadmap_tracks/sheaf_tracks.py:149`. |
| 162 | `function` | `write_sheaf_track_artifacts._semantic_certificate` | inventory fallback | Inventory fallback for function `write_sheaf_track_artifacts._semantic_certificate` defined at `src/roadmap_tracks/sheaf_tracks.py:162`. |
| 341 | `function` | `validate_sheaf_track_artifacts` | docstring | Compatibility facade for canonical sheaf-track validation. |
| 348 | `function` | `load_sheaf_track_payloads` | docstring | Compatibility facade for loading canonical sheaf-track payloads once. |
| 355 | `function` | `validate_sheaf_track_payloads` | docstring | Compatibility facade for validating preloaded canonical sheaf-track payloads. |

## `src/roadmap_tracks/sheaf_tracks_builders.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 33 | `function` | `_field_sha256` | docstring | Deterministic content hash of a single artifact field value. |
| 40 | `function` | `_field_level_provenance_rows` | docstring | Per-field lineage rows (AI-PROVENANCE-FIELDS-1). |
| 88 | `function` | `build_artifact_provenance` | inventory fallback | Inventory fallback for function `build_artifact_provenance` defined at `src/roadmap_tracks/sheaf_tracks_builders.py:88`. |
| 132 | `function` | `_artifact_bundles` | inventory fallback | Inventory fallback for function `_artifact_bundles` defined at `src/roadmap_tracks/sheaf_tracks_builders.py:132`. |
| 216 | `function` | `build_replay_matrix` | inventory fallback | Inventory fallback for function `build_replay_matrix` defined at `src/roadmap_tracks/sheaf_tracks_builders.py:216`. |
| 271 | `function` | `build_sensitivity_sweep` | inventory fallback | Inventory fallback for function `build_sensitivity_sweep` defined at `src/roadmap_tracks/sheaf_tracks_builders.py:271`. |
| 357 | `function` | `build_uncertainty_summary` | inventory fallback | Inventory fallback for function `build_uncertainty_summary` defined at `src/roadmap_tracks/sheaf_tracks_builders.py:357`. |
| 426 | `function` | `build_counterexample_matrix` | inventory fallback | Inventory fallback for function `build_counterexample_matrix` defined at `src/roadmap_tracks/sheaf_tracks_builders.py:426`. |
| 493 | `function` | `build_model_checking_witnesses` | inventory fallback | Inventory fallback for function `build_model_checking_witnesses` defined at `src/roadmap_tracks/sheaf_tracks_builders.py:493`. |
| 557 | `function` | `build_interop_roundtrip_report` | docstring | Canonical interop report built on the GENUINE parse->write->parse round-trip. |
| 629 | `function` | `build_adversarial_audit` | inventory fallback | Inventory fallback for function `build_adversarial_audit` defined at `src/roadmap_tracks/sheaf_tracks_builders.py:629`. |
| 660 | `function` | `build_blocked_scope_manifest` | inventory fallback | Inventory fallback for function `build_blocked_scope_manifest` defined at `src/roadmap_tracks/sheaf_tracks_builders.py:660`. |

## `src/roadmap_tracks/sheaf_tracks_reports.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 49 | `function` | `_field_value` | inventory fallback | Inventory fallback for function `_field_value` defined at `src/roadmap_tracks/sheaf_tracks_reports.py:49`. |
| 59 | `function` | `build_evidence_field_index` | inventory fallback | Inventory fallback for function `build_evidence_field_index` defined at `src/roadmap_tracks/sheaf_tracks_reports.py:59`. |
| 112 | `function` | `build_release_bundle_manifest` | inventory fallback | Inventory fallback for function `build_release_bundle_manifest` defined at `src/roadmap_tracks/sheaf_tracks_reports.py:112`. |
| 186 | `function` | `build_theorem_traceability_matrix` | inventory fallback | Inventory fallback for function `build_theorem_traceability_matrix` defined at `src/roadmap_tracks/sheaf_tracks_reports.py:186`. |
| 230 | `function` | `_track_artifact` | inventory fallback | Inventory fallback for function `_track_artifact` defined at `src/roadmap_tracks/sheaf_tracks_reports.py:230`. |
| 259 | `function` | `build_track_improvement_scope` | inventory fallback | Inventory fallback for function `build_track_improvement_scope` defined at `src/roadmap_tracks/sheaf_tracks_reports.py:259`. |
| 349 | `function` | `build_validation_dependency_graph` | inventory fallback | Inventory fallback for function `build_validation_dependency_graph` defined at `src/roadmap_tracks/sheaf_tracks_reports.py:349`. |
| 462 | `function` | `_canonical_restrictions` | inventory fallback | Inventory fallback for function `_canonical_restrictions` defined at `src/roadmap_tracks/sheaf_tracks_reports.py:462`. |

## `src/roadmap_tracks/sheaf_tracks_support.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 26 | `function` | `_load_json` | inventory fallback | Inventory fallback for function `_load_json` defined at `src/roadmap_tracks/sheaf_tracks_support.py:26`. |
| 37 | `function` | `_parse_yaml_cached` | docstring | Parse a YAML file, memoized on (path, mtime, size). |
| 51 | `function` | `_load_yaml` | inventory fallback | Inventory fallback for function `_load_yaml` defined at `src/roadmap_tracks/sheaf_tracks_support.py:51`. |
| 58 | `function` | `_load_structured` | inventory fallback | Inventory fallback for function `_load_structured` defined at `src/roadmap_tracks/sheaf_tracks_support.py:58`. |
| 64 | `function` | `_write_json` | inventory fallback | Inventory fallback for function `_write_json` defined at `src/roadmap_tracks/sheaf_tracks_support.py:64`. |
| 70 | `function` | `_sha256` | inventory fallback | Inventory fallback for function `_sha256` defined at `src/roadmap_tracks/sheaf_tracks_support.py:70`. |
| 80 | `function` | `_analysis_scripts` | inventory fallback | Inventory fallback for function `_analysis_scripts` defined at `src/roadmap_tracks/sheaf_tracks_support.py:80`. |
| 85 | `function` | `_registry_tracks` | inventory fallback | Inventory fallback for function `_registry_tracks` defined at `src/roadmap_tracks/sheaf_tracks_support.py:85`. |
| 91 | `function` | `_manifest_sections` | inventory fallback | Inventory fallback for function `_manifest_sections` defined at `src/roadmap_tracks/sheaf_tracks_support.py:91`. |
| 97 | `function` | `_bound_tracks` | inventory fallback | Inventory fallback for function `_bound_tracks` defined at `src/roadmap_tracks/sheaf_tracks_support.py:97`. |
| 109 | `function` | `_claim_records` | inventory fallback | Inventory fallback for function `_claim_records` defined at `src/roadmap_tracks/sheaf_tracks_support.py:109`. |
| 115 | `function` | `_claim_ids_by_path` | inventory fallback | Inventory fallback for function `_claim_ids_by_path` defined at `src/roadmap_tracks/sheaf_tracks_support.py:115`. |
| 125 | `function` | `_claim_ids_by_track` | inventory fallback | Inventory fallback for function `_claim_ids_by_track` defined at `src/roadmap_tracks/sheaf_tracks_support.py:125`. |
| 134 | `function` | `_artifact_maps` | inventory fallback | Inventory fallback for function `_artifact_maps` defined at `src/roadmap_tracks/sheaf_tracks_support.py:134`. |
| 140 | `function` | `_source_commit` | inventory fallback | Inventory fallback for function `_source_commit` defined at `src/roadmap_tracks/sheaf_tracks_support.py:140`. |
| 153 | `function` | `_deterministic_seed` | inventory fallback | Inventory fallback for function `_deterministic_seed` defined at `src/roadmap_tracks/sheaf_tracks_support.py:153`. |
| 158 | `function` | `_config_digest` | inventory fallback | Inventory fallback for function `_config_digest` defined at `src/roadmap_tracks/sheaf_tracks_support.py:158`. |
| 180 | `function` | `_entropy` | inventory fallback | Inventory fallback for function `_entropy` defined at `src/roadmap_tracks/sheaf_tracks_support.py:180`. |
| 186 | `function` | `_root_output_dir` | inventory fallback | Inventory fallback for function `_root_output_dir` defined at `src/roadmap_tracks/sheaf_tracks_support.py:186`. |
| 194 | `function` | `_copied_parity` | inventory fallback | Inventory fallback for function `_copied_parity` defined at `src/roadmap_tracks/sheaf_tracks_support.py:194`. |
| 238 | `function` | `_remove_legacy_artifacts` | inventory fallback | Inventory fallback for function `_remove_legacy_artifacts` defined at `src/roadmap_tracks/sheaf_tracks_support.py:238`. |
| 245 | `function` | `_refresh_hydrated_manuscript` | docstring | Refresh hydrated manuscript copies so semantic staleness gates converge. |
| 261 | `function` | `_canonical_artifact_rows` | inventory fallback | Inventory fallback for function `_canonical_artifact_rows` defined at `src/roadmap_tracks/sheaf_tracks_support.py:261`. |

## `src/roadmap_tracks/supplemental.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 39 | `function` | `_load_json` | inventory fallback | Inventory fallback for function `_load_json` defined at `src/roadmap_tracks/supplemental.py:39`. |
| 49 | `function` | `_validation_failures_within_fixed_point` | docstring | Return whether a red report contains only release fixed-point checks. |
| 55 | `function` | `_write_json` | inventory fallback | Inventory fallback for function `_write_json` defined at `src/roadmap_tracks/supplemental.py:55`. |
| 61 | `function` | `_sha256` | inventory fallback | Inventory fallback for function `_sha256` defined at `src/roadmap_tracks/supplemental.py:61`. |
| 71 | `function` | `_statement_symbols` | docstring | Extract stable statement identifiers from a Lean theorem statement. |
| 91 | `function` | `build_proof_dependency_graph` | docstring | Build theorem-to-source, theorem-to-symbol, and theorem-to-witness edges. |
| 143 | `function` | `_graph_world_transition_rows` | inventory fallback | Inventory fallback for function `_graph_world_transition_rows` defined at `src/roadmap_tracks/supplemental.py:143`. |
| 177 | `function` | `_tmaze_transition_rows` | inventory fallback | Inventory fallback for function `_tmaze_transition_rows` defined at `src/roadmap_tracks/supplemental.py:177`. |
| 202 | `function` | `build_state_transition_table` | docstring | Build explicit finite transition rows for graph-world topologies and T-maze actions. |
| 225 | `function` | `build_ablation_sensitivity_report` | docstring | Join causal-ablation effects to sensitivity and uncertainty source rows. |
| 271 | `function` | `build_release_attestation` | docstring | Attest release bundle, validation, license, and blocked-scope status. |
| 352 | `function` | `write_supplemental_artifacts` | docstring | Write all supplemental canonical sheaf artifacts. |
| 375 | `function` | `validate_supplemental_artifacts` | docstring | Validate supplemental artifacts from row-derived conditions. |
| 437 | `function` | `release_attestation_consistent_and_current` | docstring | Attestation is internally consistent and refers to the on-disk report. |

## `src/roadmap_tracks/toy_sweep.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 27 | `function` | `_load_json` | inventory fallback | Inventory fallback for function `_load_json` defined at `src/roadmap_tracks/toy_sweep.py:27`. |
| 34 | `function` | `_write_json` | inventory fallback | Inventory fallback for function `_write_json` defined at `src/roadmap_tracks/toy_sweep.py:34`. |
| 46 | `function` | `_sigma` | inventory fallback | Inventory fallback for function `_sigma` defined at `src/roadmap_tracks/toy_sweep.py:46`. |
| 50 | `function` | `_binary_entropy` | inventory fallback | Inventory fallback for function `_binary_entropy` defined at `src/roadmap_tracks/toy_sweep.py:50`. |
| 56 | `function` | `_closed_same_state_probability` | inventory fallback | Inventory fallback for function `_closed_same_state_probability` defined at `src/roadmap_tracks/toy_sweep.py:56`. |
| 60 | `function` | `_closed_posterior_correlation` | inventory fallback | Inventory fallback for function `_closed_posterior_correlation` defined at `src/roadmap_tracks/toy_sweep.py:60`. |
| 64 | `function` | `_closed_joint_entropy` | inventory fallback | Inventory fallback for function `_closed_joint_entropy` defined at `src/roadmap_tracks/toy_sweep.py:64`. |
| 69 | `function` | `_closed_marginal_entropy` | inventory fallback | Inventory fallback for function `_closed_marginal_entropy` defined at `src/roadmap_tracks/toy_sweep.py:69`. |
| 74 | `function` | `_closed_conditional_policy_entropy` | inventory fallback | Inventory fallback for function `_closed_conditional_policy_entropy` defined at `src/roadmap_tracks/toy_sweep.py:74`. |
| 85 | `function` | `_empirical_same_state_probability` | inventory fallback | Inventory fallback for function `_empirical_same_state_probability` defined at `src/roadmap_tracks/toy_sweep.py:85`. |
| 90 | `function` | `_empirical_posterior_correlation` | inventory fallback | Inventory fallback for function `_empirical_posterior_correlation` defined at `src/roadmap_tracks/toy_sweep.py:90`. |
| 95 | `function` | `_empirical_joint_entropy` | inventory fallback | Inventory fallback for function `_empirical_joint_entropy` defined at `src/roadmap_tracks/toy_sweep.py:95`. |
| 100 | `function` | `_empirical_marginal_entropy` | inventory fallback | Inventory fallback for function `_empirical_marginal_entropy` defined at `src/roadmap_tracks/toy_sweep.py:100`. |
| 106 | `function` | `_empirical_conditional_policy_entropy` | inventory fallback | Inventory fallback for function `_empirical_conditional_policy_entropy` defined at `src/roadmap_tracks/toy_sweep.py:106`. |
| 122 | `function` | `build_analytical_observable_sweep` | docstring | Two genuinely independent routes per observable; the residual is their gap. |
| 154 | `function` | `build_analytical_assumption_index` | docstring | Index the finite-model assumptions behind the analytical equations. |
| 272 | `function` | `build_sensitivity_sweep` | docstring | Build the sensitivity_sweep.v1 payload: the full lambda x horizon x seed x topology grid with closed-form MI per cell. |
| 303 | `function` | `build_uncertainty_summary` | docstring | Build the uncertainty_summary.v1 payload: per-step belief entropy and normalized posteriors derived from si_tmaze_trace.json. |
| 333 | `function` | `build_toy_benchmark_matrix` | docstring | Build the toy_benchmark_matrix.v1 payload: one gate row per model (bernoulli_ising, si_tmaze, graph_world) from existing artifacts. |
| 372 | `function` | `build_policy_grid` | docstring | Build the si_policy_grid.v1 payload from si_policy_comparison.json, flagging whether the planner x horizon x seed grid is complete. |
| 410 | `function` | `build_efe_terms` | docstring | Build the si_efe_values.v1 payload: per-run expected-free-energy values from si_policy_comparison.json, with a fallback reason when pymdp exposed none. |
| 451 | `function` | `_topology_trace` | inventory fallback | Inventory fallback for function `_topology_trace` defined at `src/roadmap_tracks/toy_sweep.py:451`. |
| 466 | `function` | `build_graph_world_topology_sweep` | docstring | Build the si_graph_world_topology_sweep.v1 payload: per-topology node/step counts and goal-reached flags from deterministic traces. |
| 490 | `function` | `build_graph_world_topology_traces` | docstring | Build the si_graph_world_topology_traces.v1 payload: full per-topology traces cross-checked against the topology sweep summary. |
| 514 | `function` | `_graph_world_trace_invariants` | docstring | Compute the three finite invariants from an actual topology trace (not hardcoded). |
| 543 | `function` | `build_graph_world_invariants` | docstring | Build the graph_world_invariants.v1 payload: reachability/determinism/absorbing checks computed per topology trace. |
| 559 | `function` | `build_state_space_catalog` | docstring | Build the state_space_catalog.v1 payload: state/action/policy counts for the toy models plus each graph-world topology. |
| 605 | `function` | `build_causal_ablation_matrix` | docstring | Build the causal_ablation_matrix.v1 payload: deterministic topology x lambda x perturbation grid of toy goal-margin deltas. |
| 635 | `function` | `write_toy_sweep_artifacts` | docstring | Write all twelve toy-sweep JSON artifacts under output/data/ (and output/reports/ for graph invariants). |
| 684 | `function` | `validate_toy_sweep_artifacts` | docstring | Validate the written toy-sweep artifacts (schemas, grid completeness, re-derived summary booleans, residual bound). |

## `src/simulation/graph_world.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 10 | `function` | `_graph_world_trace` | inventory fallback | Inventory fallback for function `_graph_world_trace` defined at `src/simulation/graph_world.py:10`. |
| 28 | `function` | `write_graph_world_artifacts` | docstring | Write deterministic graph-world summary and trace artifacts. |
| 53 | `function` | `write_graph_world_summary_path` | docstring | Backward-compatible wrapper returning the summary artifact path. |

## `src/simulation/invariants.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 17 | `function` | `_load_summary` | inventory fallback | Inventory fallback for function `_load_summary` defined at `src/simulation/invariants.py:17`. |
| 25 | `function` | `_load_trace` | inventory fallback | Inventory fallback for function `_load_trace` defined at `src/simulation/invariants.py:25`. |
| 33 | `function` | `_load_matrices` | inventory fallback | Inventory fallback for function `_load_matrices` defined at `src/simulation/invariants.py:33`. |
| 41 | `function` | `inv_belief_entropy_finite` | docstring | Check mean_belief_entropy in si_tmaze_summary.json is finite and non-negative. |
| 48 | `function` | `inv_actions_length_matches_steps` | docstring | Check the summary's action list length equals rollout_timestep_count equals steps + 1. |
| 57 | `function` | `inv_observations_in_obs_space` | docstring | Check observations cover exactly the location/outcome/cue modalities and each index is within its modality bound (5/3/3). |
| 67 | `function` | `inv_policy_len_matches_config` | docstring | Check the summary's policy_len matches the policy_len recorded in its config block. |
| 75 | `function` | `inv_goal_reached` | docstring | Check the summary reports goal_reached, falling back to any reward outcome observation (index 1). |
| 84 | `function` | `inv_trace_step_count_matches_summary` | docstring | Check the si_tmaze_trace.json step count equals the summary's rollout_timestep_count. |
| 91 | `function` | `inv_si_tree_available` | docstring | Check the planner is sophisticated_inference and the summary reports tree_available. |
| 97 | `function` | `inv_q_pi_rows_normalized` | docstring | Check every trace step flags q_pi_normalized and its q_pi sums to 1 within STEP_POSTERIOR_ATOL. |
| 106 | `function` | `inv_model_matrices_full_tmaze` | docstring | Check si_tmaze_model_matrices.json has the v1 schema, full T-maze A/B shapes, and all normalization checks passing. |
| 130 | `function` | `run_simulation_invariants` | docstring | Run all SIMULATION_INVARIANTS against the project root and return name -> pass mapping. |
| 136 | `function` | `build_merged_invariants_payload` | docstring | Single SSOT for merged analytical + simulation invariant reports. |
| 166 | `function` | `write_simulation_invariants` | docstring | Run the simulation invariants and write results plus all_pass to output/reports/si_invariants.json. |
| 180 | `function` | `merge_simulation_into_invariants_report` | docstring | Rebuild output/reports/invariants.json with simulation results merged via build_merged_invariants_payload. |

## `src/simulation/logging_utils.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 35 | `function` | `_now_iso` | inventory fallback | Inventory fallback for function `_now_iso` defined at `src/simulation/logging_utils.py:35`. |
| 39 | `function` | `_json_default` | inventory fallback | Inventory fallback for function `_json_default` defined at `src/simulation/logging_utils.py:39`. |
| 45 | `function` | `validate_record` | inventory fallback | Inventory fallback for function `validate_record` defined at `src/simulation/logging_utils.py:45`. |
| 56 | `class` | `RunLogger` | inventory fallback | Inventory fallback for class `RunLogger` defined at `src/simulation/logging_utils.py:56`. |
| 60 | `function` | `RunLogger.__post_init__` | inventory fallback | Inventory fallback for function `RunLogger.__post_init__` defined at `src/simulation/logging_utils.py:60`. |
| 66 | `function` | `RunLogger.from_project_root` | inventory fallback | Inventory fallback for function `RunLogger.from_project_root` defined at `src/simulation/logging_utils.py:66`. |
| 77 | `function` | `RunLogger.fresh` | inventory fallback | Inventory fallback for function `RunLogger.fresh` defined at `src/simulation/logging_utils.py:77`. |
| 82 | `function` | `RunLogger.emit` | inventory fallback | Inventory fallback for function `RunLogger.emit` defined at `src/simulation/logging_utils.py:82`. |
| 91 | `function` | `RunLogger.emit_run_header` | inventory fallback | Inventory fallback for function `RunLogger.emit_run_header` defined at `src/simulation/logging_utils.py:91`. |
| 114 | `function` | `RunLogger.timed` | inventory fallback | Inventory fallback for function `RunLogger.timed` defined at `src/simulation/logging_utils.py:114`. |
| 123 | `function` | `RunLogger.records` | inventory fallback | Inventory fallback for function `RunLogger.records` defined at `src/simulation/logging_utils.py:123`. |
| 132 | `function` | `RunLogger.step_records` | inventory fallback | Inventory fallback for function `RunLogger.step_records` defined at `src/simulation/logging_utils.py:132`. |

## `src/simulation/pymdp_config.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 21 | `class` | `EnvironmentConfig` | docstring | T-maze environment settings: reward condition, cue validity, and outcome probabilities. |
| 33 | `class` | `AgentConfig` | docstring | pymdp agent settings: policy lengths, gamma, inference algorithm, action selection, and learning flags. |
| 47 | `class` | `SISearchConfig` | docstring | Sophisticated-inference tree-search settings: horizon, node/branching caps, and pruning thresholds. |
| 64 | `class` | `LoggingConfig` | docstring | Run-logging settings: enabled flag and JSONL output path. |
| 72 | `class` | `ValidationComparisonConfig` | docstring | Planner-comparison settings for validation runs: enabled flag, planners, and seeds. |
| 81 | `class` | `PymdpConfig` | docstring | Top-level config for the canonical full-TMaze sophisticated-inference rollout. |
| 96 | `function` | `PymdpConfig.policy_len` | inventory fallback | Inventory fallback for function `PymdpConfig.policy_len` defined at `src/simulation/pymdp_config.py:96`. |
| 100 | `function` | `PymdpConfig.horizon` | inventory fallback | Inventory fallback for function `PymdpConfig.horizon` defined at `src/simulation/pymdp_config.py:100`. |
| 104 | `function` | `PymdpConfig.steps` | inventory fallback | Inventory fallback for function `PymdpConfig.steps` defined at `src/simulation/pymdp_config.py:104`. |
| 108 | `function` | `PymdpConfig.mode` | docstring | Compatibility alias for older manuscript statistics consumers. |
| 113 | `function` | `_coerce_planner` | inventory fallback | Inventory fallback for function `_coerce_planner` defined at `src/simulation/pymdp_config.py:113`. |
| 120 | `function` | `_coerce_comparison_planner` | inventory fallback | Inventory fallback for function `_coerce_comparison_planner` defined at `src/simulation/pymdp_config.py:120`. |
| 127 | `function` | `_coerce_reward_condition` | inventory fallback | Inventory fallback for function `_coerce_reward_condition` defined at `src/simulation/pymdp_config.py:127`. |
| 136 | `function` | `_parse_raw` | inventory fallback | Inventory fallback for function `_parse_raw` defined at `src/simulation/pymdp_config.py:136`. |
| 205 | `function` | `default_pymdp_config` | docstring | Return a PymdpConfig with all default values. |
| 210 | `function` | `pymdp_config_path` | docstring | Return the canonical pymdp.yaml path under the project root. |
| 215 | `function` | `load_pymdp_config` | docstring | Load PymdpConfig from pymdp.yaml (or config_path), returning defaults when the file is absent. |
| 231 | `function` | `apply_pymdp_overrides` | docstring | Return a copy of the config with any provided steps/horizon/seed/logging/comparison overrides applied. |
| 263 | `function` | `config_snapshot` | docstring | Return a JSON-serializable dict of every config field, used for logging and hashing. |
| 315 | `function` | `config_hash` | docstring | Return the first 16 hex chars of the SHA-256 over the sorted JSON config snapshot. |

## `src/simulation/pymdp_runtime.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 24 | `function` | `_categorized_rows` | docstring | Derive explicit per-construction categorized diagnostic rows. |
| 89 | `function` | `_runtime_rows_explained` | docstring | True iff every row has a known category and every reasoned-category row has a reason. |
| 102 | `function` | `_package_version` | inventory fallback | Inventory fallback for function `_package_version` defined at `src/simulation/pymdp_runtime.py:102`. |
| 109 | `function` | `_backend_flags` | inventory fallback | Inventory fallback for function `_backend_flags` defined at `src/simulation/pymdp_runtime.py:109`. |
| 122 | `function` | `_warning_record` | inventory fallback | Inventory fallback for function `_warning_record` defined at `src/simulation/pymdp_runtime.py:122`. |
| 131 | `function` | `construct_agent_with_diagnostics` | docstring | Construct ``pymdp.Agent`` while capturing the one audited JAX warning. |
| 185 | `function` | `build_runtime_diagnostics` | inventory fallback | Inventory fallback for function `build_runtime_diagnostics` defined at `src/simulation/pymdp_runtime.py:185`. |
| 209 | `function` | `write_runtime_diagnostics` | inventory fallback | Inventory fallback for function `write_runtime_diagnostics` defined at `src/simulation/pymdp_runtime.py:209`. |
| 220 | `function` | `validate_runtime_diagnostics` | inventory fallback | Inventory fallback for function `validate_runtime_diagnostics` defined at `src/simulation/pymdp_runtime.py:220`. |

## `src/simulation/si_artifacts.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 25 | `function` | `_shape_list` | inventory fallback | Inventory fallback for function `_shape_list` defined at `src/simulation/si_artifacts.py:25`. |
| 29 | `function` | `_factor_sum_ranges` | inventory fallback | Inventory fallback for function `_factor_sum_ranges` defined at `src/simulation/si_artifacts.py:29`. |
| 46 | `function` | `model_matrices_payload` | inventory fallback | Inventory fallback for function `model_matrices_payload` defined at `src/simulation/si_artifacts.py:46`. |
| 70 | `function` | `write_model_matrices` | inventory fallback | Inventory fallback for function `write_model_matrices` defined at `src/simulation/si_artifacts.py:70`. |
| 79 | `function` | `write_si_artifacts` | inventory fallback | Inventory fallback for function `write_si_artifacts` defined at `src/simulation/si_artifacts.py:79`. |
| 191 | `function` | `run_and_persist` | inventory fallback | Inventory fallback for function `run_and_persist` defined at `src/simulation/si_artifacts.py:191`. |
| 208 | `function` | `_comparison_row` | inventory fallback | Inventory fallback for function `_comparison_row` defined at `src/simulation/si_artifacts.py:208`. |
| 251 | `function` | `write_policy_comparison` | docstring | Write SI-vs-vanilla comparison rows without changing the canonical summary. |
| 309 | `function` | `write_policy_posterior_grid` | docstring | Write step-level PyMDP policy posterior normalization evidence. |

## `src/simulation/si_belief.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 8 | `function` | `marginal_state_belief` | inventory fallback | Inventory fallback for function `marginal_state_belief` defined at `src/simulation/si_belief.py:8`. |
| 19 | `function` | `belief_entropy` | inventory fallback | Inventory fallback for function `belief_entropy` defined at `src/simulation/si_belief.py:19`. |
| 24 | `function` | `qs_marginal_state1` | inventory fallback | Inventory fallback for function `qs_marginal_state1` defined at `src/simulation/si_belief.py:24`. |

## `src/simulation/si_loop.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 27 | `function` | `pymdp_available` | inventory fallback | Inventory fallback for function `pymdp_available` defined at `src/simulation/si_loop.py:27`. |
| 37 | `class` | `SIRunResult` | inventory fallback | Inventory fallback for class `SIRunResult` defined at `src/simulation/si_loop.py:37`. |
| 64 | `function` | `SIRunResult.mode` | inventory fallback | Inventory fallback for function `SIRunResult.mode` defined at `src/simulation/si_loop.py:64`. |
| 68 | `function` | `_prob_entropy` | inventory fallback | Inventory fallback for function `_prob_entropy` defined at `src/simulation/si_loop.py:68`. |
| 79 | `function` | `_sequence_from_rollout` | inventory fallback | Inventory fallback for function `_sequence_from_rollout` defined at `src/simulation/si_loop.py:79`. |
| 84 | `function` | `_observations_by_modality` | inventory fallback | Inventory fallback for function `_observations_by_modality` defined at `src/simulation/si_loop.py:84`. |
| 93 | `function` | `_named_observations` | inventory fallback | Inventory fallback for function `_named_observations` defined at `src/simulation/si_loop.py:93`. |
| 105 | `function` | `_belief_entropy_by_step` | inventory fallback | Inventory fallback for function `_belief_entropy_by_step` defined at `src/simulation/si_loop.py:105`. |
| 119 | `function` | `_q_pi_rows` | inventory fallback | Inventory fallback for function `_q_pi_rows` defined at `src/simulation/si_loop.py:119`. |
| 132 | `function` | `_first_action_probabilities` | inventory fallback | Inventory fallback for function `_first_action_probabilities` defined at `src/simulation/si_loop.py:132`. |
| 148 | `function` | `_tree_stats` | inventory fallback | Inventory fallback for function `_tree_stats` defined at `src/simulation/si_loop.py:148`. |
| 164 | `function` | `_build_si_policy_search` | inventory fallback | Inventory fallback for function `_build_si_policy_search` defined at `src/simulation/si_loop.py:164`. |
| 183 | `function` | `_run_pymdp_rollout` | inventory fallback | Inventory fallback for function `_run_pymdp_rollout` defined at `src/simulation/si_loop.py:183`. |
| 317 | `function` | `run_si_tmaze` | docstring | Run the canonical full-TMaze sophisticated-inference profile. |
| 331 | `function` | `run_validation_comparison_tmaze` | docstring | Run SI or vanilla pymdp planning for comparison artifacts only. |

## `src/simulation/si_policy.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 22 | `function` | `select_policy_action` | docstring | Return action, method label, selected EFE, selected policy index, and policy evidence. |

## `src/simulation/statistics.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 11 | `function` | `_entropy_stats` | inventory fallback | Inventory fallback for function `_entropy_stats` defined at `src/simulation/statistics.py:11`. |
| 22 | `function` | `_series_stats` | inventory fallback | Inventory fallback for function `_series_stats` defined at `src/simulation/statistics.py:22`. |
| 33 | `function` | `_first_positive_step` | inventory fallback | Inventory fallback for function `_first_positive_step` defined at `src/simulation/statistics.py:33`. |
| 40 | `function` | `summarize_si_trace` | inventory fallback | Inventory fallback for function `summarize_si_trace` defined at `src/simulation/statistics.py:40`. |
| 78 | `function` | `load_si_artifacts` | inventory fallback | Inventory fallback for function `load_si_artifacts` defined at `src/simulation/statistics.py:78`. |

## `src/simulation/tmaze_model.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 43 | `class` | `TMazeSpec` | inventory fallback | Inventory fallback for class `TMazeSpec` defined at `src/simulation/tmaze_model.py:43`. |
| 55 | `function` | `spec_from_config` | inventory fallback | Inventory fallback for function `spec_from_config` defined at `src/simulation/tmaze_model.py:55`. |
| 64 | `function` | `build_tmaze_environment` | docstring | Construct pymdp's full ``TMaze`` environment from the project config. |
| 80 | `function` | `_as_list_dependencies` | inventory fallback | Inventory fallback for function `_as_list_dependencies` defined at `src/simulation/tmaze_model.py:80`. |
| 84 | `function` | `_normalization_checks` | inventory fallback | Inventory fallback for function `_normalization_checks` defined at `src/simulation/tmaze_model.py:84`. |
| 104 | `function` | `build_preference_vectors` | docstring | Build C vectors following pymdp's full-TMaze SI validation notebook. |
| 117 | `function` | `build_initial_state_priors` | docstring | Build D priors: center-start location and uniform reward-location belief. |
| 128 | `function` | `build_tmaze_generative_model` | docstring | Return pymdp full ``TMaze`` A/B/C/D plus labels and normalization evidence. |

## `src/validation_spine/artifacts.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 93 | `function` | `_sha256` | inventory fallback | Inventory fallback for function `_sha256` defined at `src/validation_spine/artifacts.py:93`. |
| 104 | `function` | `_file_fingerprint` | inventory fallback | Inventory fallback for function `_file_fingerprint` defined at `src/validation_spine/artifacts.py:104`. |
| 117 | `function` | `_load_json` | inventory fallback | Inventory fallback for function `_load_json` defined at `src/validation_spine/artifacts.py:117`. |
| 124 | `function` | `_configured_analysis_scripts` | inventory fallback | Inventory fallback for function `_configured_analysis_scripts` defined at `src/validation_spine/artifacts.py:124`. |
| 134 | `function` | `_config_digest` | inventory fallback | Inventory fallback for function `_config_digest` defined at `src/validation_spine/artifacts.py:134`. |
| 146 | `function` | `_deterministic_seed` | inventory fallback | Inventory fallback for function `_deterministic_seed` defined at `src/validation_spine/artifacts.py:146`. |
| 158 | `function` | `_source_commit_for_root` | inventory fallback | Inventory fallback for function `_source_commit_for_root` defined at `src/validation_spine/artifacts.py:158`. |
| 172 | `function` | `_source_commit` | inventory fallback | Inventory fallback for function `_source_commit` defined at `src/validation_spine/artifacts.py:172`. |
| 176 | `function` | `_artifact_record` | inventory fallback | Inventory fallback for function `_artifact_record` defined at `src/validation_spine/artifacts.py:176`. |
| 195 | `function` | `_config_record` | inventory fallback | Inventory fallback for function `_config_record` defined at `src/validation_spine/artifacts.py:195`. |
| 205 | `function` | `build_artifact_provenance` | docstring | Build deterministic artifact lineage and hash records. |
| 232 | `function` | `_same_json` | inventory fallback | Inventory fallback for function `_same_json` defined at `src/validation_spine/artifacts.py:232`. |
| 238 | `function` | `_copy_replay_inputs` | inventory fallback | Inventory fallback for function `_copy_replay_inputs` defined at `src/validation_spine/artifacts.py:238`. |
| 247 | `function` | `build_reproducibility_replay` | docstring | Replay deterministic toy producers in a temporary tree and compare outputs. |
| 324 | `function` | `build_counterexample_matrix` | docstring | Document expected-failure fixtures that keep the gates falsifiable. |
| 417 | `function` | `write_validation_spine_artifacts` | docstring | Write provenance, replay, and counterexample artifacts. |
| 444 | `function` | `validate_artifact_provenance` | inventory fallback | Inventory fallback for function `validate_artifact_provenance` defined at `src/validation_spine/artifacts.py:444`. |
| 520 | `function` | `validate_reproducibility_replay` | inventory fallback | Inventory fallback for function `validate_reproducibility_replay` defined at `src/validation_spine/artifacts.py:520`. |
| 564 | `function` | `validate_counterexample_matrix` | inventory fallback | Inventory fallback for function `validate_counterexample_matrix` defined at `src/validation_spine/artifacts.py:564`. |
| 588 | `function` | `validate_validation_spine` | docstring | Return all validation-spine artifact issues. |

## `src/visualizations/animation.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 13 | `function` | `_frame_hash` | docstring | Deterministic sha256 over a frame's raw RGB pixel bytes (no new deps). |
| 18 | `function` | `_load_trace_steps` | inventory fallback | Inventory fallback for function `_load_trace_steps` defined at `src/visualizations/animation.py:18`. |
| 33 | `function` | `write_belief_trajectory_gif` | docstring | Write a deterministic multi-frame GIF from trace entropy/action state. |
| 71 | `function` | `build_animation_frame_deltas` | docstring | Compute a deterministic manifest proving adjacent GIF frames change. |
| 140 | `function` | `write_animation_frame_deltas` | docstring | Write the frame-delta manifest for the deterministic animation track. |
| 149 | `function` | `validate_animation_frame_deltas` | docstring | Return frame-delta manifest issues. |

## `src/visualizations/figure_helpers.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 20 | `function` | `save_styled_figure` | inventory fallback | Inventory fallback for function `save_styled_figure` defined at `src/visualizations/figure_helpers.py:20`. |
| 37 | `function` | `style_grid` | inventory fallback | Inventory fallback for function `style_grid` defined at `src/visualizations/figure_helpers.py:37`. |
| 43 | `function` | `styled_figure` | docstring | Load style, resolve output path, and apply matplotlib rc context. |
| 51 | `function` | `subset_note` | docstring | Stamp a 'showing N of M' annotation on any figure rendering a filtered view. |

## `src/visualizations/figure_io.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 17 | `function` | `save_figure_png` | docstring | Save a figure to PNG and optionally normalize to RGB for PDF pipelines. |

## `src/visualizations/figure_registry.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 20 | `class` | `FigureSpec` | inventory fallback | Inventory fallback for class `FigureSpec` defined at `src/visualizations/figure_registry.py:20`. |
| 29 | `class` | `SectionFigureRef` | inventory fallback | Inventory fallback for class `SectionFigureRef` defined at `src/visualizations/figure_registry.py:29`. |
| 36 | `function` | `_figures_yaml_path` | inventory fallback | Inventory fallback for function `_figures_yaml_path` defined at `src/visualizations/figure_registry.py:36`. |
| 40 | `function` | `_load_figures_yaml` | inventory fallback | Inventory fallback for function `_load_figures_yaml` defined at `src/visualizations/figure_registry.py:40`. |
| 49 | `function` | `_load_figures_yaml_cached` | inventory fallback | Inventory fallback for function `_load_figures_yaml_cached` defined at `src/visualizations/figure_registry.py:49`. |
| 54 | `function` | `load_figure_registry` | inventory fallback | Inventory fallback for function `load_figure_registry` defined at `src/visualizations/figure_registry.py:54`. |
| 75 | `function` | `load_section_figures` | inventory fallback | Inventory fallback for function `load_section_figures` defined at `src/visualizations/figure_registry.py:75`. |
| 99 | `function` | `figure_output_path` | inventory fallback | Inventory fallback for function `figure_output_path` defined at `src/visualizations/figure_registry.py:99`. |
| 104 | `function` | `render_figure_markdown` | inventory fallback | Inventory fallback for function `render_figure_markdown` defined at `src/visualizations/figure_registry.py:104`. |
| 142 | `function` | `render_section_figures` | inventory fallback | Inventory fallback for function `render_section_figures` defined at `src/visualizations/figure_registry.py:142`. |
| 165 | `function` | `build_figure_registry_payload` | docstring | Build validator-facing registry JSON keyed by ``fig:{id}`` labels. |
| 183 | `function` | `write_figure_registry_json` | docstring | Write ``output/figures/figure_registry.json`` from ``figures.yaml``. |

## `src/visualizations/figure_style.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 53 | `class` | `FigureStyleConfig` | inventory fallback | Inventory fallback for class `FigureStyleConfig` defined at `src/visualizations/figure_style.py:53`. |
| 60 | `function` | `FigureStyleConfig.color` | inventory fallback | Inventory fallback for function `FigureStyleConfig.color` defined at `src/visualizations/figure_style.py:60`. |
| 64 | `function` | `FigureStyleConfig.base_font_size` | inventory fallback | Inventory fallback for function `FigureStyleConfig.base_font_size` defined at `src/visualizations/figure_style.py:64`. |
| 67 | `function` | `FigureStyleConfig.font_size` | docstring | Return a named figure font size in points. |
| 78 | `function` | `FigureStyleConfig.rc_params` | inventory fallback | Inventory fallback for function `FigureStyleConfig.rc_params` defined at `src/visualizations/figure_style.py:78`. |
| 96 | `function` | `active_style` | inventory fallback | Inventory fallback for function `active_style` defined at `src/visualizations/figure_style.py:96`. |
| 100 | `function` | `load_figure_style` | inventory fallback | Inventory fallback for function `load_figure_style` defined at `src/visualizations/figure_style.py:100`. |
| 109 | `function` | `_load_figure_style_cached` | inventory fallback | Inventory fallback for function `_load_figure_style_cached` defined at `src/visualizations/figure_style.py:109`. |
| 124 | `function` | `apply_style` | inventory fallback | Inventory fallback for function `apply_style` defined at `src/visualizations/figure_style.py:124`. |

## `src/visualizations/figures.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 132 | `function` | `run_figure` | docstring | Dispatch a registry figure id to its generator. |
| 145 | `function` | `generate_all_figures` | inventory fallback | Inventory fallback for function `generate_all_figures` defined at `src/visualizations/figures.py:145`. |

## `src/visualizations/figures_abstract.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 21 | `function` | `_json_or_empty` | inventory fallback | Inventory fallback for function `_json_or_empty` defined at `src/visualizations/figures_abstract.py:21`. |
| 28 | `function` | `figure_graphical_abstract` | docstring | Render the cover-page graphical abstract from generated evidence artifacts. |
| 42 | `function` | `figure_graphical_abstract._f` | inventory fallback | Inventory fallback for function `figure_graphical_abstract._f` defined at `src/visualizations/figures_abstract.py:42`. |
| 48 | `function` | `figure_graphical_abstract._i` | inventory fallback | Inventory fallback for function `figure_graphical_abstract._i` defined at `src/visualizations/figures_abstract.py:48`. |
| 56 | `function` | `figure_graphical_abstract._v` | inventory fallback | Inventory fallback for function `figure_graphical_abstract._v` defined at `src/visualizations/figures_abstract.py:56`. |
| 93 | `function` | `figure_graphical_abstract.evidence_card` | inventory fallback | Inventory fallback for function `figure_graphical_abstract.evidence_card` defined at `src/visualizations/figures_abstract.py:93`. |

## `src/visualizations/figures_analytical.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 23 | `function` | `_read_sweep` | inventory fallback | Inventory fallback for function `_read_sweep` defined at `src/visualizations/figures_analytical.py:23`. |
| 31 | `function` | `figure_ising_mi_curve` | inventory fallback | Inventory fallback for function `figure_ising_mi_curve` defined at `src/visualizations/figures_analytical.py:31`. |
| 70 | `function` | `figure_energy_decomposition` | docstring | Render the VFE and EFE decompositions from the energy demo artifact. |
| 160 | `function` | `figure_free_energy_curve` | inventory fallback | Inventory fallback for function `figure_free_energy_curve` defined at `src/visualizations/figures_analytical.py:160`. |

## `src/visualizations/figures_diagrams.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 27 | `function` | `_load_invariant_blocks` | inventory fallback | Inventory fallback for function `_load_invariant_blocks` defined at `src/visualizations/figures_diagrams.py:27`. |
| 40 | `function` | `figure_invariant_dashboard` | inventory fallback | Inventory fallback for function `figure_invariant_dashboard` defined at `src/visualizations/figures_diagrams.py:40`. |
| 97 | `function` | `figure_tmaze_schematic` | inventory fallback | Inventory fallback for function `figure_tmaze_schematic` defined at `src/visualizations/figures_diagrams.py:97`. |
| 178 | `function` | `_load_pipeline_track_labels` | inventory fallback | Inventory fallback for function `_load_pipeline_track_labels` defined at `src/visualizations/figures_diagrams.py:178`. |
| 185 | `function` | `_load_sheaf_track_labels` | inventory fallback | Inventory fallback for function `_load_sheaf_track_labels` defined at `src/visualizations/figures_diagrams.py:185`. |
| 193 | `function` | `figure_multi_track_architecture` | inventory fallback | Inventory fallback for function `figure_multi_track_architecture` defined at `src/visualizations/figures_diagrams.py:193`. |
| 199 | `function` | `figure_multi_track_architecture._fmt` | inventory fallback | Inventory fallback for function `figure_multi_track_architecture._fmt` defined at `src/visualizations/figures_diagrams.py:199`. |
| 289 | `function` | `figure_multi_track_architecture.draw_box` | inventory fallback | Inventory fallback for function `figure_multi_track_architecture.draw_box` defined at `src/visualizations/figures_diagrams.py:289`. |
| 384 | `function` | `figure_lean_boundary_status` | inventory fallback | Inventory fallback for function `figure_lean_boundary_status` defined at `src/visualizations/figures_diagrams.py:384`. |
| 390 | `function` | `figure_lean_boundary_status._wrap_snake` | inventory fallback | Inventory fallback for function `figure_lean_boundary_status._wrap_snake` defined at `src/visualizations/figures_diagrams.py:390`. |
| 447 | `function` | `figure_gnn_ontology_concordance` | inventory fallback | Inventory fallback for function `figure_gnn_ontology_concordance` defined at `src/visualizations/figures_diagrams.py:447`. |

## `src/visualizations/figures_firstprinciples.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 21 | `function` | `figure_distillation_divergence_geometry` | docstring | Render first-principles divergence geometry for teacher/student policies. |
| 99 | `function` | `figure_exposure_bias_recovery` | docstring | Render off-policy compounding versus on-policy correction curves. |
| 198 | `function` | `figure_classroom_distillation_signal` | docstring | Render teacher/student policy gaps in the two-agent classroom artifact. |
| 306 | `function` | `figure_sequential_shift_recovery` | docstring | Render the deterministic finite sequential train/test shift witness. |
| 401 | `function` | `figure_sequential_shift_sensitivity` | docstring | Render the finite correction-dose sensitivity sweep for sequential shift. |
| 510 | `function` | `figure_parallel_convergence` | docstring | Two frameworks, one answer: ML distillation converging to the AIF posterior. |
| 573 | `function` | `figure_diversity_tradeoff` | docstring | Pass@1 (greedy, temperature-invariant) vs Pass@k (collapses under sharpening). |
| 622 | `function` | `figure_privilege_dose_response` | docstring | Teacher-privilege dose-response: entropy gap is a threshold, reverse KL is the sensitive detector. |

## `src/visualizations/figures_interpretability.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 25 | `function` | `_load_json` | inventory fallback | Inventory fallback for function `_load_json` defined at `src/visualizations/figures_interpretability.py:25`. |
| 29 | `function` | `figure_correspondence_map` | docstring | Render the audited OPD <-> active inference dictionary as the paper's visual spine. |
| 42 | `function` | `figure_correspondence_map._wrap` | inventory fallback | Inventory fallback for function `figure_correspondence_map._wrap` defined at `src/visualizations/figures_interpretability.py:42`. |
| 98 | `function` | `figure_policy_posterior_grid` | docstring | Render the measured per-step policy posteriors for both planners. |
| 184 | `function` | `_taxonomy_label_offset` | docstring | Return a deterministic leader-line offset for dense same-year method clusters. |
| 196 | `function` | `figure_opd_taxonomy_landscape` | docstring | Render the audited method taxonomy as a year-by-design-quadrant landscape. |

## `src/visualizations/figures_sheaf.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 33 | `function` | `figure_sheaf_layers_overview` | inventory fallback | Inventory fallback for function `figure_sheaf_layers_overview` defined at `src/visualizations/figures_sheaf.py:33`. |
| 69 | `function` | `figure_sheaf_coverage_heatmap` | docstring | Render B/W/G sheaf coverage matrix with IMRAD row grouping. |

## `src/visualizations/figures_sheaf_draw.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 20 | `function` | `_imrad_group_label` | inventory fallback | Inventory fallback for function `_imrad_group_label` defined at `src/visualizations/figures_sheaf_draw.py:20`. |
| 24 | `function` | `_draw_imrad_group_labels` | docstring | Annotate IMRAD block names on the left margin of the heatmap. |
| 61 | `function` | `draw_coverage_heatmap` | inventory fallback | Inventory fallback for function `draw_coverage_heatmap` defined at `src/visualizations/figures_sheaf_draw.py:61`. |
| 142 | `function` | `draw_track_layers_panel` | inventory fallback | Inventory fallback for function `draw_track_layers_panel` defined at `src/visualizations/figures_sheaf_draw.py:142`. |
| 205 | `function` | `layers_overview_figure_height` | docstring | Figure height (inches) for the two-panel sheaf layers overview. |

## `src/visualizations/figures_sheaf_payload.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 13 | `class` | `HeatmapPayload` | inventory fallback | Inventory fallback for class `HeatmapPayload` defined at `src/visualizations/figures_sheaf_payload.py:13`. |
| 22 | `function` | `coverage_heatmap_payload` | inventory fallback | Inventory fallback for function `coverage_heatmap_payload` defined at `src/visualizations/figures_sheaf_payload.py:22`. |

## `src/visualizations/figures_si.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 22 | `function` | `_style_discrete_y` | inventory fallback | Inventory fallback for function `_style_discrete_y` defined at `src/visualizations/figures_si.py:22`. |
| 27 | `function` | `_clean_action_label` | inventory fallback | Inventory fallback for function `_clean_action_label` defined at `src/visualizations/figures_si.py:27`. |
| 31 | `function` | `_tmaze_action_vocabulary` | inventory fallback | Inventory fallback for function `_tmaze_action_vocabulary` defined at `src/visualizations/figures_si.py:31`. |
| 54 | `function` | `figure_si_belief_entropy_curve` | inventory fallback | Inventory fallback for function `figure_si_belief_entropy_curve` defined at `src/visualizations/figures_si.py:54`. |
| 88 | `function` | `figure_si_obs_action_trace` | inventory fallback | Inventory fallback for function `figure_si_obs_action_trace` defined at `src/visualizations/figures_si.py:88`. |
| 160 | `function` | `figure_si_tmaze_actions` | inventory fallback | Inventory fallback for function `figure_si_tmaze_actions` defined at `src/visualizations/figures_si.py:160`. |
| 224 | `function` | `figure_si_tmaze_model_matrices` | inventory fallback | Inventory fallback for function `figure_si_tmaze_model_matrices` defined at `src/visualizations/figures_si.py:224`. |
| 320 | `function` | `figure_si_summary` | docstring | Deprecated alias for ``figure_si_tmaze_actions``. |

## `src/visualizations/figures_validation.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 22 | `function` | `_wrap_label` | inventory fallback | Inventory fallback for function `_wrap_label` defined at `src/visualizations/figures_validation.py:22`. |
| 26 | `function` | `_compact_list_label` | inventory fallback | Inventory fallback for function `_compact_list_label` defined at `src/visualizations/figures_validation.py:26`. |
| 34 | `function` | `figure_semantic_gluing_graph` | inventory fallback | Inventory fallback for function `figure_semantic_gluing_graph` defined at `src/visualizations/figures_validation.py:34`. |
| 149 | `function` | `figure_theorem_traceability_graph` | docstring | Render theorem → proof dependency → witness links from generated JSON rows. |
| 243 | `function` | `figure_causal_ablation_heatmap` | docstring | Render source-backed causal-ablation effects as topology × perturbation heatmap. |
| 286 | `function` | `figure_scholarship_source_map` | docstring | Render bibliography-to-method-source bindings from the scholarship matrix. |
| 298 | `function` | `figure_scholarship_source_map.artifact_bucket` | inventory fallback | Inventory fallback for function `figure_scholarship_source_map.artifact_bucket` defined at `src/visualizations/figures_validation.py:298`. |

## `src/visualizations/lean_boundary.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 11 | `class` | `LeanBoundaryRow` | inventory fallback | Inventory fallback for class `LeanBoundaryRow` defined at `src/visualizations/lean_boundary.py:11`. |
| 26 | `function` | `_module_name` | inventory fallback | Inventory fallback for function `_module_name` defined at `src/visualizations/lean_boundary.py:26`. |
| 34 | `function` | `_declaration_block` | docstring | Return the declaration body from ``start`` until the next top-level def/theorem. |
| 43 | `function` | `_scan_lean_file` | inventory fallback | Inventory fallback for function `_scan_lean_file` defined at `src/visualizations/lean_boundary.py:43`. |
| 56 | `function` | `load_lean_boundary_rows` | inventory fallback | Inventory fallback for function `load_lean_boundary_rows` defined at `src/visualizations/lean_boundary.py:56`. |

## `scripts/compose_manuscript.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/compose_manuscript.py:15`. |

## `scripts/compute_statistics.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/compute_statistics.py:15`. |

## `scripts/generate_figures.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/generate_figures.py:15`. |

## `scripts/generate_firstprinciples.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 24 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/generate_firstprinciples.py:24`. |

## `scripts/generate_formal_interop_tracks.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 16 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/generate_formal_interop_tracks.py:16`. |

## `scripts/generate_integration_audit.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/generate_integration_audit.py:15`. |

## `scripts/generate_method_inventory.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/generate_method_inventory.py:15`. |

## `scripts/generate_sheaf_tracks.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/generate_sheaf_tracks.py:15`. |

## `scripts/generate_toy_sweep_tracks.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/generate_toy_sweep_tracks.py:15`. |

## `scripts/generate_validation_spine.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/generate_validation_spine.py:15`. |

## `scripts/inject_variables.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 11 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/inject_variables.py:11`. |

## `scripts/render_animation.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 14 | `function` | `build_parser` | inventory fallback | Inventory fallback for function `build_parser` defined at `scripts/render_animation.py:14`. |
| 26 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/render_animation.py:26`. |

## `scripts/render_pdf.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 17 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/render_pdf.py:17`. |

## `scripts/run_analytical_sweep.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 15 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/run_analytical_sweep.py:15`. |

## `scripts/run_full_chain.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 61 | `function` | `canonical_scripts` | docstring | The declared analysis order from manuscript/config.yaml (source of truth). |
| 70 | `function` | `_run` | inventory fallback | Inventory fallback for function `_run` defined at `scripts/run_full_chain.py:70`. |
| 80 | `function` | `_project_pytest_running` | docstring | Detect another same-repo pytest run before mutating generated artifacts. |
| 109 | `function` | `_pipeline_lock` | docstring | Serialize full-chain writers so artifact fixed points are not interleaved. |
| 126 | `function` | `_release_attestation_current` | docstring | Return true only when the attestation pins the current validation report. |
| 145 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/run_full_chain.py:145`. |

## `scripts/run_tests_chunked.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 31 | `function` | `collect_chunks` | docstring | Group test files into chunks; with a seed, shuffle deterministically. |
| 49 | `function` | `_parse_counts` | inventory fallback | Inventory fallback for function `_parse_counts` defined at `scripts/run_tests_chunked.py:49`. |
| 61 | `function` | `_tail_lines` | docstring | Return a bounded diagnostic tail without inventing output on success. |
| 68 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/run_tests_chunked.py:68`. |

## `scripts/simulate_si_graph_world.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 13 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/simulate_si_graph_world.py:13`. |

## `scripts/simulate_si_tmaze.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 18 | `function` | `build_parser` | inventory fallback | Inventory fallback for function `build_parser` defined at `scripts/simulate_si_tmaze.py:18`. |
| 57 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/simulate_si_tmaze.py:57`. |

## `scripts/validate_outputs.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 16 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/validate_outputs.py:16`. |

## `scripts/z_generate_manuscript_variables.py`

| line | kind | name | documentation source | summary |
| ---: | --- | --- | --- | --- |
| 16 | `function` | `main` | inventory fallback | Inventory fallback for function `main` defined at `scripts/z_generate_manuscript_variables.py:16`. |
