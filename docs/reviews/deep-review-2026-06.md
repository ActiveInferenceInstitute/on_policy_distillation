# Deep-review disposition ledger (2026-06)

This page maps every item of the external deep review ("Deep Review of
On-Policy Distillation Is Active Inference", received 2026-06-10) to its
disposition in the repository. Dispositions are evidence-bound: each row names
the file that carries the change. Three disposition values are used:

- **LANDED** — implemented; evidence file(s) named.
- **DEFERRED** — accepted in principle; blocked on something external; tracked.
- **REJECTED** — not adopted, with the stated reason.

The bulk of the claim-audit items were implemented in the Run-5 commit
(`66fe40b`, "external-review response — claim calibration, countervailing
citations, proposition box, figure rigor, bib hygiene"); the remainder landed
in the run that authored this ledger.

## 1. Headline-thesis calibration

| Review item | Disposition | Evidence |
|---|---|---|
| "On-policy distillation is active inference" reads as a field-wide theorem; say "can be cast as / within this finite construction" | **LANDED** | `manuscript/00_abstract.md` opens "admits a scoped active-inference reading that is exact in the finite models studied here"; `manuscript/17_conclusion.md`: "stronger than a slogan and narrower than a universal theorem … a claim about declared toy models, generated artifacts, and machine-checked manuscript bindings" |
| Teacher policy "plays the role of" generative model needs the augmented joint model defined before the mapping is asserted | **LANDED** | Abstract uses "plays the role of"; the correspondence is pinned as a proposition **with stated assumptions** in `manuscript/05_methods_analytical.md`, referenced from `manuscript/03_intro_contributions.md` ("a claim we pin down as a proposition with stated assumptions … separating what is proved in closed form, what is demonstrated numerically, and what remains an interpretive reading") |
| Reverse-KL loss "is" VFE needs the evidence-constant qualification | **LANDED** | Abstract states $F = D_{\mathrm{KL}}(q\,\|\,p) - \log p(o)$ explicitly; conclusion: "variational free energy **up to the evidence constant**" |
| OPD "repairs" exposure bias — soften; severity is task-dependent, self-recovery documented | **LANDED** | Abstract: "closely related to — though not identical with — … whose severity is itself contested"; `manuscript/15_discussion_outlook.md` Limitations: "its empirical severity is task-dependent and autoregressive models can exhibit meaningful self-recovery" citing `he2021selfrecovery`, `huszar2015hownot` |
| Reverse-KL mode-seeking / forward-KL mass-covering trope — keep only as finite-support intuition | **LANDED** | Abstract: "a finite-support divergence-direction intuition rather than a universal law about LLM training" citing `wu2024rethinking_kl_kd`; discussion divergence-map paragraph carries the support/entropy/optimization caveat |
| "Student rollouts are active sampling" — separate OPD data collection from EFE-based action selection | **LANDED** | Abstract keeps VFE and EFE apart by construction ("the distillation loss instantiates *variational* free energy on realized rollouts, while action selection and planning are … *expected* free energy"); `manuscript/06_methods_pymdp.md` frames the T-maze agent as the executable analogue |
| "OPD is the student minimising EFE" — overstated | **LANDED** | The EFE reading is confined to the pymdp agent's planner; discussion: "The cue-disambiguation result is an epistemic-foraging toy, not evidence that LLM students will discover useful hidden structure at scale" |
| Teacher–student MI as "the epistemic value of teacher feedback" — reframe as proxy | **LANDED** (hedged-reading variant) | `manuscript/05_methods_analytical.md`: "an interpretable ceiling for this toy binary coupling — … **read as** the epistemic value of teacher feedback on student-generated states — … **we do not claim a general communication-theoretic bound beyond this construction**" |
| Qwen/Thinking Machines numbers need primary-source anchoring; TM must not be load-bearing | **LANDED** | Discussion "Empirical evidence (literature-reported)": "We did **not** measure any of the following ourselves; the table values … are from Table {{qwen_table_number}} of the Qwen3 technical report as relayed and discussed by Thinking Machines … reproduced here only as external context." The primary-source pin is now source-bound in `src/firstprinciples/empirical.py`, `src/manuscript/variables.py`, `src/gates/output_checks.py`, and `tests/test_firstprinciples_empirical.py`: Qwen3 Technical Report, Table 21, heading "Comparison of reinforcement learning and on-policy distillation on Qwen3-8B." |
| Survey/repo citations carrying technical claims — replace with primaries | **LANDED** | All 2026 OPD primaries are cited directly (see §3); surveys appear only with explicit "and the survey literature" framing; `output/data/scholarship_source_matrix.json` keeps the preprint/archival distinction machine-readable |
| Markov-blanket / predictive-coding language needs Biehl/Aguilera qualification | **LANDED** | Discussion Limitations: "blanket-based inferential readings are technically delicate and not uncontested, we use them only as a constrained probabilistic interpretation of the toy models" citing `biehl2020critique`, `aguilera2022particular_fep` |
| Artifact pipeline "proves machine-checked correspondence" — scope it | **LANDED** | Conclusion: "They do not prove a general theorem about all active-inference agents or all distillation algorithms. They prove something operationally valuable for this manuscript: …" |

## 2. Structural recommendations

| Review item | Disposition | Evidence |
|---|---|---|
| Explicit assumptions paragraph (finite support, declared joint target, realized observations, tractable student family, VFE/EFE separation) | **LANDED** | Proposition with stated assumptions in `manuscript/05_methods_analytical.md`; the VFE/EFE separation is stated in the abstract and re-stated at each use site |
| Bridge paragraph in the introduction ("constructive rather than universal") | **LANDED** | `manuscript/03_intro_contributions.md` contribution 1 carries the constructive framing and the closed-form / numerical / interpretive split |
| Discussion in three parts: what is established / what is not / which OPD questions are illuminated | **LANDED** | `manuscript/15_discussion_outlook.md` sections: "What this demonstrates", "Limitations", "Empirical evidence (literature-reported)", "Audit, evidence, and open problems" — the open-problems paragraph is organized around teacher reliability, privilege-vs-shortcutting, uncertainty-aware losses, and stability, as the review requested |
| Per-paragraph scoping line in Results | **LANDED** | Results figures/captions carry determinism + scope statements (e.g. `figures.yaml` → `diversity_tradeoff`: "an exact calculation over the toy problem ensemble, not an empirical measurement") |
| Three-audience concluding paragraph (ML / active-inference / reproducibility readers) | **LANDED (this run)** | `manuscript/17_conclusion.md`, penultimate paragraph: "Each intended audience receives a distinct, separable contribution …" |
| Reposition or compress the sheaf/provenance apparatus | **PARTIALLY ADOPTED** | The provenance material already lives in the supplements (`18_…`, `19_…`, `20_…`), and the main text references it in one paragraph per section. Full relocation to a companion artifact paper is a venue decision recorded in `TODO.md`, not unilaterally taken here |

## 3. Priority citation additions

All priority and recommended sources from the review are present in
`manuscript/references.bib` (117 entries) and cited at the locations the
review names. Verification: `grep -c '^@' manuscript/references.bib` and the
keys below.

| Review source | Bib key | Cited at |
|---|---|---|
| Sajid et al., *Active inference: demystified and compared* | `sajid2021demystified` | abstract-adjacent intro, methods, discussion |
| Levine, *RL and Control as Probabilistic Inference* | `levine2018rlinference` | abstract; reward-tilted target in `05_methods_analytical.md` |
| Lopez-Paz et al., *Unifying distillation and privileged information* | `lopezpaz2016unifying` | abstract; contributions; privileged-conditioning discussion |
| Snell et al., *Learning by Distilling Context* | `snell2022context_distillation` | abstract; limitations; open problems |
| Champion et al., *Reframing the Expected Free Energy* | `champion2024efe_unification` | EFE handling |
| Wu et al., *Rethinking KL Divergence in KD for LLMs* | `wu2024rethinking_kl_kd` | abstract; divergence-geometry guardrails |
| Friston et al., *Sophisticated Inference* | `friston2021sophisticated` | abstract; pymdp methods (key renamed in Run-5) |
| Biehl et al. critique; Aguilera et al. FEP physics | `biehl2020critique`, `aguilera2022particular_fep` | blanket caveats in Limitations |
| Agarwal et al. GKD; Gu et al. MiniLLM; Ko et al. DistiLLM | `agarwal2024gkd`, `gu2024minillm`, `ko2024distillm` (+`ko2025distillm2`) | primary OPD anchors throughout |
| Huszár 2015; He et al. 2021 | `huszar2015hownot`, `he2021selfrecovery` | exposure-bias qualification |
| OPSD; π-Distill; SDPG; OPCD; entropy-aware OPD; HPD; Rethinking OPD; adaptive teacher exposure; Demystifying OPD; VA-OPD; EDGE-OPD | `zhao2026opsd`, `penaloza2026pidistill`, `liu2026sdpg`, `ye2026context_distillation`, `jin2026entropy_opd`, `zhu2026hpd`, `li2026rethinking_opd`, `han2026adaptive_teacher_exposure`, `luo2026demystifying_opd`, `liu2026visual_advantage_opd`, `lazaridis2026edge_opd` | abstract, discussion, open problems — all as primaries |
| pymdp JOSS; van Oostrum et al. | `pymdp2022`, `vanoostrum2024discrete_active_inference` | software + discrete-time formalism citations |

## 4. Visualization audit

| Review item | Disposition | Evidence / reason |
|---|---|---|
| Caption guardrails ("toy finite-support illustration only", determinism statements) | **LANDED** | `figures.yaml` captions state determinism explicitly (e.g. `parallel_convergence`: "fully deterministic (no sampling), so no uncertainty intervals apply"; `diversity_tradeoff`: "exact calculation … not an empirical measurement") |
| Fig 17 (privilege dose-response): state clipped floor, avoid unexplained inferential language | **LANDED** | `figures.yaml` → `privilege_dose_response`: explicit "$10^{-3}$-nat noise floor", "step-versus-slope is resolution-limited by the grid", identical-agent baseline labeled "a wiring check, not an effect control" |
| Fig 18 (policy posterior grid): define normalization / measured rows; reduce label clutter | **LANDED** | `figures.yaml` → `policy_posterior_grid`: "cell values are probabilities; labels shown for mass at or above 0.30"; "{{posterior_grid_available_count}} of {{posterior_grid_row_count}} measured grid rows" |
| Fig 19 (taxonomy): quadrant criteria visible, table in supplement, primaries only | **LANDED** | `figures.yaml` → `opd_taxonomy_landscape` lane counts derived from `output/data/firstprinciples/opd_taxonomy.json`; caption: "a positioning of the field's design choices, not a performance comparison" |
| Fig 1 (correspondence map): simplify to 8–10 rows in main text | **REJECTED** | The full-dictionary rendering is deliberate — the caption frames it as "the paper's thesis as a single picture", and every row is machine-validated (`firstprinciples.mapping.CORRESPONDENCES`). Truncating the rendered map would desynchronize the figure from the audited artifact it is generated from; the appendix carries per-row notes |
| Fig 2 / Figs 20–25/27 (provenance dashboards): move to supplement | **PARTIALLY ADOPTED** | Provenance figures are concentrated in the supplement sections; remaining main-text placement is a venue-formatting decision tracked in `TODO.md` |
| Fig 7 (T-maze matrices) → table or supplement | **DEFERRED** | Converting the generated matrix figure to a typeset table changes the figure-source-map contract; tracked in `TODO.md` as a venue-preparation item |
| External OPD-vs-RL table: pin exact Qwen table/figure | **LANDED** | The table is pinned to Qwen3 Technical Report Table 21 and the exact source heading in `output/data/firstprinciples/empirical_benchmark.json`, `output/data/scholarship_source_matrix.json`, and the strict output gate constants in `src/gates/output_checks.py`; Thinking Machines remains a relay/context key, not the direct source. |

## 5. Final-checklist cross-check

Every item of the review's "Final revision checklist" maps to a row above
except two, handled as follows:

- **"If inferential statistics are applied to deterministic toy runs, define
  the resampling unit; otherwise remove inferential language"** — LANDED: the
  deterministic artifacts state "no sampling / no RNG" in captions and
  results prose; no confidence intervals are attached to deterministic
  sweeps (`manuscript/20_supplement_validation_statistics.md` documents the
  validation statistics that DO exist and their basis).
- **"Position the paper explicitly for its venue (scientific thesis vs
  reproducibility-systems paper)"** — the three-audience conclusion paragraph
  now states the separable contributions; the venue decision itself is the
  authors' and is out of scope for this ledger.

## Maintenance

When a future review arrives, copy this file's structure into
`docs/reviews/<review-id>.md`, fill dispositions only with file-backed
evidence, and never mark an item LANDED without naming the file that carries
it. Items requiring external re-verification (e.g. primary-source table
numbers) are DEFERRED with the blocking condition stated, not silently
adopted.
