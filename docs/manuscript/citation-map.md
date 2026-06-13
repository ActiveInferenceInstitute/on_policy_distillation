# Citation Map

The bibliography ([`../../manuscript/references.bib`](../../manuscript/references.bib),
117 entries) organized by **function** — what role each source plays in the argument —
rather than alphabetically. Every key below is present in `references.bib`. The
preprint/archival status of sources is tracked machine-readably in
`output/data/scholarship_source_matrix.json` (see the `scholarship` track and
[`../../manuscript/15_discussion_outlook.md`](../../manuscript/15_discussion_outlook.md)).

A key may legitimately appear in more than one group; it is listed under its primary
function and cross-referenced where load-bearing elsewhere.

## Foundational active inference

The free-energy principle, variational/expected free energy, and discrete-state active
inference that supply the generative-model / posterior / VFE / EFE vocabulary the
correspondence borrows.

| Key | Carries which claim |
| --- | --- |
| `friston2006fep` | Free-energy principle as the variational frame for `F = D_KL(q‖p) − log p(o)`. |
| `friston2010fep` | Action/perception under free energy; anchor for VFE identities and the MI ceiling. |
| `friston2017process` | Active inference as a process theory; basis for "act to generate observations." |
| `parr2022active` | Standard reference textbook; discrete active inference and the EFE ledger. |
| `parr2019generalised` | Generalised free energy; supports the variational-family treatment. |
| `sajid2021demystified` | Demystifies active inference; used for the process-theory reading. |
| `friston2021sophisticated` | Sophisticated inference (beliefs about beliefs) = teacher conditioned on student traces; EFE action selection. |
| `friston2018deep_temporal` | Deep temporal models; SI structure for the T-maze planner. |
| `friston2017curiosity` | Epistemic/curiosity drive = active-sampling pressure. |
| `dacosta2020discrete` | Discrete-state active inference; finite-POMDP framing for the pymdp witness. |
| `vanoostrum2024discrete_active_inference` | Discrete active inference; on-policy rollout interpretation. |
| `pymdp2022` | The pymdp implementation anchor (`TMaze`, `Agent`, `si_policy_search`, `rollout`). |
| `millidge2020efe` | EFE epistemic/pragmatic decomposition the distillation loss recapitulates. |
| `millidge2020active_control` | Control-as-inference; member of the reward-tilted-target family. |
| `champion2024efe_unification` | EFE unification; risk/ambiguity ↔ epistemic/pragmatic identity. |
| `sajid2021bayesian_design` | Bayesian experimental design reading of epistemic value. |
| `devries2025efe_planning_vi` | EFE planning via variational inference; on-policy EFE extension. |
| `buckley2017mathreview` | Mathematical review; scopes free-energy terminology to finite calculations. |
| `millidge2021walkthrough` | Mathematical walkthrough; makes separable-model assumptions explicit. |
| `tschantz2020scaling_active_inference` | Scaling active inference; context for the toy/scale gap. |
| `friston2021interesting_observations` | Interesting-observations framing of epistemic foraging. |
| `smith2022tutorial` | Tutorial on active inference; discrete POMDP exposition. |
| `parr2020markov_blankets_thermo` | Markov blankets; cited only for the constrained screening reading. |
| `friston2013life` | Life/Markov-blanket boundary; used as constrained probabilistic reading only. |
| `kirchhoff2018markov` | Markov blankets as conditional-independence partition (teacher/student asymmetry). |

## RL / control-as-inference bridge

Sources establishing that RL, control, and inference share a KL-regularized,
reward-tilted target `π_ref · exp(R/β)` — Contribution 3's unification.

| Key | Carries which claim |
| --- | --- |
| `levine2018rlinference` | RL-as-inference; the reverse-KL gradient = VFE gradient bridge. |
| `todorov2008duality` | Control-estimation duality; member of the reward-tilted family. |
| `toussaint2009trajectory_inference` | Trajectory inference; planning-as-inference target form. |
| `ziebart2008maxent_irl` | Maximum-entropy IRL; reward-tilted target. |
| `haarnoja2018sac` | Maximum-entropy RL (SAC); KL-regularized objective. |
| `abdolmaleki2018mpo` | MPO; RL-as-inference policy optimization. |
| `odonoghue2020rl_prob_inference` | RL as probabilistic inference; target normalization. |
| `millidge2020iterative_amortised` | Iterative amortised inference; variational control. |
| `tschantz2020rl_active_inference` | RL ↔ active inference; comparison framing. |
| `fellows2018virel` | VIREL; variational intrinsic control in the family. |
| `ziegler2019humanprefs` | RLHF; KL-constrained preference objective. |
| `rafailov2023dpo` | DPO; KL-constrained preference fine-tuning in the family. |

## Distillation foundations

Classical/off-policy knowledge distillation and the learning-using-privileged-information
(LUPI) lineage — the forward-KL / SFT limit and the privilege framing.

| Key | Carries which claim |
| --- | --- |
| `hinton2015distilling` | Classical KD; the mode-covering forward-KL / SFT limit. |
| `bucila2006model_compression` | Model compression; origin of distillation, forward-KL limit. |
| `kim2016sequence_kd` | Sequence-level KD; off-policy teacher-data objective. |
| `rusu2016policy_distillation` | Policy distillation in RL; induced-distribution mismatch. |
| `czarnecki2019distilling_policy` | Distilling policy networks; off-policy baseline. |
| `stanton2021kd_work` | Does KD actually work; diversity/optimization caveats. |
| `vapnik2009lupi` | Learning using privileged information; the privilege construct. |
| `lopezpaz2016unifying` | Unifying distillation and privileged information. |
| `snell2022context_distillation` | Context distillation; privileged-context transfer. |
| `shrivastava2021mi_kd` | Mutual-information KD; motivates the channel view of `I(λ)`. |
| `xu2024speculative_kd` | Speculative KD; reuse of student-generated outputs. |

## On-policy distillation primaries

The OPD line proper: the reverse-KL turn, generalized KD, and the 2026 self-distillation /
privileged-context / adaptive-teacher wave the correspondence is positioned against.

| Key | Carries which claim |
| --- | --- |
| `agarwal2024gkd` | Generalized KD; on-policy student rollouts scored under student visitation. |
| `gu2024minillm` | MiniLLM; the reverse-KL concentration side of the divergence axis. |
| `ko2024distillm` | DistiLLM; skew/adaptive-KL middle regimes. |
| `ko2025distillm2` | DistiLLM-2; further skew/hybrid KD points. |
| `zhao2026opsd` | OPSD; per-token self-distillation objective the classroom maps onto. |
| `liu2026sdpg` | SDPG; privileged-context self-distillation objective `L_clip + βD_KL + αKL_ref`. |
| `lauyikfung2026sdpgcode` | SDPG code reference. |
| `penaloza2026pidistill` | π-distill; reward-tilted distillation in the variational frame. |
| `penaloza2026tutorial` | π-distill tutorial; stepwise/long-context OPD framing. |
| `ye2026context_distillation` | Context distillation OPD; transferable vs shortcut privilege. |
| `jin2026entropy_opd` | Entropy-aware OPD; teacher-entropy / mode-covering switch. |
| `zhu2026hpd` | Hybrid policy distillation; skew-KL design point. |
| `zhu2026manyfacesopd` | "Many faces" of OPD; survey of design choices. |
| `li2026rethinking_opd` | Rethinking OPD; objective/support/optimization dependence (guardrail). |
| `han2026adaptive_teacher_exposure` | Adaptive teacher exposure; entropy-aware supervision. |
| `luo2026demystifying_opd` | Demystifying OPD; what changes the objective in practice. |
| `liu2026visual_advantage_opd` | Visual-advantage OPD; multimodal privileged signal. |
| `lazaridis2026edge_opd` | Edge OPD; privileged/context transfer at the edge. |
| `liu2026oisd` | Internal on-policy self-distillation (OISD); internal-alignment analogue. |
| `hubotter2026sdpo` | SDPO; preference-feedback variant in the family. |
| `oh2026vopd` | Veto/restricted OPD when the teacher is unreliable. |
| `xing2026tropd` | Trust-region OPD. |
| `jang2026veto` | Veto-based OPD. |
| `ye2025blackbox_opd` | Black-box OPD; teacher-access-restricted offline approximation. |
| `wu2026lightningopd` | Lightning OPD; efficiency variant. |
| `zhong2026sod` | Stepwise OPD. |
| `zhang2026opsdl` | Long-horizon OPD. |
| `tian2026vicur` | Curriculum/visual OPD variant. |
| `ramos2026dgrpo` | DGRPO; joint OPD/RL objective context. |
| `awesomeopd2026` | Curated OPD landscape; the divergence-direction taxonomy. |
| `song2026opdsurvey` | OPD survey; field-level positioning. |

## Critiques / limitations

The guardrail literature: divergence-direction caveats, FEP/blanket critiques, EFE
critiques, and exposure-bias severity caveats that keep the toy contrasts from becoming
universal laws.

| Key | Carries which claim |
| --- | --- |
| `biehl2020critique` | Critique of FEP/blanket inferential readings. |
| `aguilera2022particular_fep` | Particular FEP; technical delicacy of blanket interpretations. |
| `wu2024rethinking_kl_kd` | Rethinking KL in KD; reverse/forward-KL not a universal law. |
| `hernandezlobato2016blackbox_alpha` | Black-box alpha divergence; divergence-direction is not neutral. |
| `ke2019f_divergence_imitation` | f-divergence imitation; objective geometry caveat. |
| `huszar2015hownot` | How (not) to train your generative model; scheduled sampling inconsistency. |
| `he2021selfrecovery` | Self-recovery; exposure-bias severity is task-dependent. |
| `champion2024efe_unification` | (also a foundation) clarifies competing EFE decompositions. |
| `holtzman2019degeneration` | Neural text degeneration; diversity-collapse caveat. |

## Exposure bias / imitation learning

The sequential-prediction / induced-distribution-shift lineage motivating why on-policy
training is needed (Introduction and the T-maze epistemic reading).

| Key | Carries which claim |
| --- | --- |
| `pomerleau1989alvinn` | ALVINN; behavioral cloning and compounding error. |
| `ross2010efficient_imitation` | Efficient imitation reductions. |
| `ross2011dagger` | DAgger; the canonical induced-distribution / interactive-imitation result. |
| `shimodaira2000covariate_shift` | Covariate-shift risk weighting; context for train/test visitation mismatch. |
| `sun2017aggrevated` | AggreVaTeD; differentiable interactive imitation. |
| `bengio2015scheduled` | Scheduled sampling; teacher-forcing mismatch repair. |
| `ranzato2016sequence` | Sequence-level training objectives. |
| `arora2022exposure` | Exposure bias in language generation. |
| `rohatgi2025next_token_barrier` | Next-token barrier; sequential-prediction limits. |
| `pozzi2025exposure_distill` | Exposure bias in distillation specifically. |
| `cai2024privileged_pomdp` | Privileged-information POMDPs; cue-as-privilege analogue. |
| `yang2024sdft_gap` | SDFT (ACL); self-distillation to bridge a fine-tuning distribution gap. |
| `shenfeld2026sdft` | SDFT (continual); demonstration-conditioned self-teacher. |

## Variational-inference and information-theory backbone

| Key | Carries which claim |
| --- | --- |
| `kullback1951information` | KL divergence; the directional information measure. |
| `jordan1999variational` | Variational inference in graphical models; the tractable-family move. |
| `blei2017variational` | Variational inference review; mean-field approximation. |

## Predictive coding

| Key | Carries which claim |
| --- | --- |
| `rao1999predictive` | Predictive coding; top-down target + bottom-up residual reading only. |

## Sheaf / category theory

The applied-composition and contract language for the manuscript-as-artifact discipline
(Contribution 5). Used as a finite local-to-global / composition-contract device, not a
cohomological claim.

| Key | Carries which claim |
| --- | --- |
| `curry2014sheaves` | Cellular sheaves; the local-to-global compose model. |
| `speranzon2018contracts` | Sheaf-theoretic assume/guarantee contracts. |
| `robinson2014topological` | Topological signal processing; sheaf consistency. |
| `robinson2017sensor_sheaf` | Sensor-integration sheaves. |
| `phillips2019sheaving` | Semantic sheaving. |
| `fong2019applied_category` | Applied category theory; compositionality. |
| `rosiak2022sheaf_examples` | Sheaf theory through examples. |
| `cox2026fragmented_risk_sheaf` | Fragmented-risk sheaf application. |

## GNN / ontology specification

| Key | Carries which claim |
| --- | --- |
| `gnn2023` | Generalized Notation Notation (graphical model-spec language); the GNN round-trip. |
| `koudahl2023synthetic` | Synthetic/graphical active-inference specification context. |

## External empirical context (literature-reported, not reproduced)

The production-scale OPD-vs-RL numbers discussed in the limitations. **Not reproduced** —
see [`claims-and-scope.md`](claims-and-scope.md) §(d). The Thinking Machines source is
**non-archival** (a Connectionism blog post), flagged as such in the source matrix.

| Key | Carries which claim |
| --- | --- |
| `qwen2025technical_report` | Qwen3 technical report; the AIME-24 OPD-vs-RL accuracy and GPU-hour table (external context only). |
| `thinkingmachines2025opd` | Thinking Machines OPD post; relays/replicates Qwen and frames efficiency (non-archival external context). |

## Note on completeness

`references.bib` contains 117 entries; this map groups the load-bearing keys cited
across the abstract, introduction, methods, results, discussion, and conclusion. A
handful of entries appear only inside generated supplemental tables
(`output/data/firstprinciples/*_table.md`) or the notation supplement; those carry no
prose claim and are not tabulated here. To audit the live citation surface, render the
manuscript and inspect the resolved bibliography rather than editing this page by hand.
