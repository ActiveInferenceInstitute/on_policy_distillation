# Supplementary material: reproducibility methodology {#sec:methods_sheaf}

<!-- sheaf-track:prose -->

## Compose contract

This standalone supplement documents the reproducibility methodology behind the rendered paper. The preceding full-coverage supplement ([@sec:appendix_full_sheaf]) checks that the maximal appendix row can bind all registered fragment families; this section instead explains the operational contract that makes those fragments reproducible: where data are generated, how variables are hydrated, which validators run, and how failed gates block the PDF.

Each manifest row in `manuscript/sheaf/manifest.yaml` binds fragment tracks from `manuscript/sheaf/tracks.yaml`. A track supplies a renderer, compose order, label, and optional flag; the composer flattens the binding set into one Markdown section for PDF and web output. The machinery is generic, but the manuscript it assembles here argues a specific thesis: that on-policy distillation admits a finite-model active-inference reading when the variational objects are declared, so the composer must keep the analytical toy model, the pymdp rollout, the sequential-shift witness and sensitivity sweep, and the self-distillation literature mutually consistent about that scoped correspondence.

The operational claim is auditable binding: analytical, simulation, pymdp, visualization, Lean, GNN, ontology, scholarship, and optional media fragments attach to each IMRAD row under [@eq:coverage_cell] (**P** present, **—** unbound, **M** missing). This is an applied local-to-global consistency and composition-contract use of sheaf language in the spirit of cellular sheaves, sheaf-theoretic contracts, sheaf-signal-processing work, sensor-integration sheaves, semantic sheaving, applied compositionality, and reproducible computational research references [@curry2014sheaves; @speranzon2018contracts; @robinson2014topological; @robinson2017sensor_sheaf; @phillips2019sheaving; @fong2019applied_category; @rosiak2022sheaf_examples; @cox2026fragmented_risk_sheaf; @sandve2013reproducible; @wilkinson2016fair], but instantiated here as a finite manuscript artifact gate rather than as a public archive or release claim. Concretely, what this gate verifies is machine-executable provenance and version capture in the sense of standard reproducible-research practice [@sandve2013reproducible]; that discipline is necessary but not sufficient, since findable, accessible, interoperable, and reusable artifacts [@wilkinson2016fair] are not the same thing as end-to-end rerunnability or independent reproduction of the toy results by a third party, neither of which is claimed here. The same gate forces the teacher-student framing to remain coherent end to end: the Bernoulli-Ising free-energy analysis [@friston2006fep; @friston2009rl_active_inference; @friston2010fep], the sophisticated-inference T-maze rollout [@parr2022active; @dacosta2020discrete], the sequential-shift witness and sensitivity sweep, and the on-policy distillation context [@agarwal2024gkd; @thinkingmachines2025opd] each occupy their own track yet must agree on the variational posterior they describe.

## Coverage and figures

[@fig:sheaf_layers_overview] summarizes {{sheaf_track_count}} fragment types and their IMRAD bindings. Generated tables below list every track definition and section×track binding at compose time. The bindings span the full argument: the minimal-model demonstrations (analytical and pymdp tracks) and the scholarship track that situates them against the off-policy baseline [@hinton2015distilling], the reverse-KL turn [@gu2024minillm], and the 2026 self-distillation wave [@zhao2026opsd; @shenfeld2026sdft; @liu2026sdpg].

The visualization layer is audited as data, not as decoration. `output/data/figure_source_map.json` binds every registered figure to source artifacts, source fields, validation gates, and explicit caption-claim contracts; `output/reports/figure_hash_manifest.json` records the declared rendered image bytes; and `output/reports/visualization_quality_audit.json` rechecks readability, nonblank pixels, source binding, caption-claim source fields, caption scope guardrails, cover wording, cover quantitative-free status, declared palette contrast, font-role floors, and absence of unregistered image artifacts. The negative controls mutate rows under green summaries and add stray image files, so a figure with an unreadable image, missing source, missing caption-claim field, unscoped empirical/production caption, inaccessible declared style token, stale cover equality claim, metric-dashboard cover language, or stale unregistered PNG cannot remain validated by a stale boolean.

The statistical layer follows the same rule. `output/data/firstprinciples/statistics_demo.json` is accepted only when its matched teacher/student entropy series, paired deltas, summaries, effect size, and seeded permutation metadata rederive from `output/data/firstprinciples/classroom.json` at validation time. This makes the classroom inferential paragraph a source-bound toy summary rather than a free-floating significance claim.

## Compose commands

```bash
uv run python scripts/compose_manuscript.py
uv run python scripts/compose_manuscript.py --validate-only --strict
```

Each run emits `output/data/sheaf_coverage_matrix.json` and regenerates coverage artifacts. Partial compose (`--section`) is draft-only; the matrix always reflects the full manifest. Coverage totals appear on [@sec:sheaf_coverage]; discussion scope is in [@sec:discussion_outlook].

## Law verification

`--validate-only --strict` runs the structural gate before any fragment is glued. Beyond per-cell coverage, it invokes the sheaf-law oracle (`verify_sheaf_laws`, `src/manuscript/sheaf/laws.py`), which checks {{sheaf_law_count}} axioms — poset, presheaf functoriality, separation, gluing, typing, and compositionality — and reports {{sheaf_laws_verified}}/{{sheaf_law_count}} satisfied for the current manifest. A violation is raised as an error-level issue and aborts the build, so a malformed manifest (a section colliding on an output file, an off-chain block, a mistyped fragment, a fragment shared between sections) can never compose. The formal statements are in the formalism block below; the negative-control suite (`tests/test_sheaf_laws.py`) proves each check is falsifiable.

Stored summary flags are themselves never trusted at the final gate. Each generated artifact carries `all_*` aggregate booleans written by its producer; `validate_outputs` re-derives {{rederived_aggregate_rule_count}} of these aggregates from their own row data at read time (`src/gates/aggregate_rederivation.py`) and fails when a stored flag disagrees with its rows — including the vacuous case of a `true` flag over an empty row set. A mutated row under an untouched green summary therefore fails validation no matter what wrote it; the negative-control suite exercises exactly that lying case.

The semantic layer is separate from those structural laws. `output/data/sheaf_gluing_certificate.json` records cross-track symbols, typed claim evidence, artifact sources, and manuscript-variable restrictions; validation fails when the analytical, pymdp, GNN, ontology, Lean, visualization, or manuscript tracks disagree about a shared symbol or measured claim. This is where the correspondence is held honest at the symbol level: the coupling parameter and mutual information of the analytical toy, the cue-validity privileged-information channel of the T-maze, the two-agent classroom figures (privileged teacher belief entropy {{classroom_teacher_belief_entropy_formatted}} nats versus the on-policy student's {{classroom_student_belief_entropy_formatted}} nats, mean reverse-KL distillation signal {{classroom_mean_reverse_kl_formatted}} nats), and the sequential-shift witness (train loss {{sequential_train_loss:.3f}} nats, induced test loss {{sequential_test_loss_before:.3f}} nats, corrected test loss {{sequential_test_loss_after:.3f}} nats, sensitivity loss reduction {{sequential_sensitivity_test_loss_reduction:.3f}} nats) must all restrict consistently onto the shared variational-free-energy and reverse-KL symbols. The certificate keeps these numbers bound as a minimal-model demonstration of the teacher-student correspondence, not as claims about production LLMs. [@fig:semantic_gluing_graph] renders this gluing graph: the configured producers, the generated evidence artifacts, and the validation consumers that read each shared symbol.

<!-- sheaf-track:formalism -->

### Base poset and presheaf

The manuscript is modelled as a coverage sheaf over a finite base poset. Let the
**base** $P$ be the IMRAD blocks ordered as a chain,

$$
\mathsf{Introduction} \prec \mathsf{Methods} \prec \mathsf{Results} \prec \mathsf{Discussion} \prec \mathsf{Appendix},
$$ {#eq:imrad_chain}

with, in each block, a *group* node above its *section* nodes (written $G \sqsupseteq s$). $P$ is therefore a finite poset (equivalently a finite Alexandrov space). Let $\mathcal{T}$ be the registered fragment-track set from `manuscript/sheaf/tracks.yaml`; each track $t \in \mathcal{T}$ carries a renderer $R(t)$, label $L(t)$, optional flag $O(t)$, and a strict compose-order index $\pi(t)$.

The **presheaf** $\mathcal{F}$ is a contravariant functor on $P$ — $\mathcal{F}\colon P \to \mathbf{Set}$ with restriction maps along $\sqsupseteq$ — assigning to each composing section $s$ its bound fragment set $\mathcal{F}(s) = \{\,(t, F_s(t)) : t \text{ bound in } s\,\}$, where $F_s : \mathcal{T} \rightharpoonup \mathbf{Path}$ is the section's partial binding map. Restriction along $G \sqsupseteq s$ is projection onto a section's own bindings; group nodes carry the empty assignment and do not compose.

The coverage cell is

$$
B(s,t) \in \{\mathrm{P}, \text{--}, \mathrm{M}\}
$$ {#eq:coverage_cell}

derived from $F_s(t)$ and filesystem existence at compose time: **P** when a bound fragment exists, **—** when the track is unbound for that row, and **M** when a bound path is missing. The current regenerated matrix reports {{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing cells. Registry size: $|\mathcal{T}| = {{sheaf_track_count}}$ types across {{imrad_manifest_rows}} IMRAD manifest rows ({{imrad_group_count}} group rows, {{composed_section_count}} composing sections).

### Verified sheaf laws

What makes this presheaf a *sheaf* — rather than a bare incidence table — is that the composer's structural axioms are machine-checked. The oracle `verify_sheaf_laws` (`src/manuscript/sheaf/laws.py`) verifies {{sheaf_law_count}} laws, and the regenerated build reports {{sheaf_laws_verified}}/{{sheaf_law_count}} satisfied:

1. **Poset.** The IMRAD blocks form the chain of [@eq:imrad_chain]; compose order is monotone in block rank and every composing section's block carries a group row.
2. **Presheaf (functoriality).** Every bound track lies in $\mathcal{T}$; $\pi$ is a strict total order; and each section's resolved track order is the monotone restriction of $\pi$ (an explicit `track_order` override must be a permutation of the section's bound tracks).
3. **Separation (locality).** The map $s \mapsto \mathrm{output\_name}(s)$ is injective over composing sections: distinct locals glue to distinct global positions, so the global section is unique.
4. **Gluing.** Compose order is a linear extension of $P$ — each block's rows are contiguous and strictly increasing in order — so the local fragments glue to a unique global manuscript in which every composing section appears exactly once.
5. **Typing.** Each binding $(t, F_s(t))$ is well-typed: $R(t)$ is a registered renderer and the fragment suffix lies in $R(t)$'s accepted suffix set. Generated renderers (`section_figures`, `layers_report`) synthesize their body and are explicitly type-exempt.
6. **Compositionality.** Every fragment file is private to one section (no path is bound twice), so global composition is the coproduct of the per-section bodies and is independent of inclusion order.

Each law is paired with a negative control in `tests/test_sheaf_laws.py` — a single mutation that breaks the law and is proven to be caught — so the gate binds the laws' *content*, not merely their shape. Under `--strict`, any violation is surfaced as an error-level manifest issue and aborts composition.

### Scope (what is and is not claimed)

These laws verify the sheaf *axioms* on a finite base poset. They do **not** compute sheaf *cohomology* ($H^0$/$H^1$, Čech complexes, derived functors); "sheaf" here names the verified separation-and-gluing structure of a multi-track coverage assignment, not a cohomological invariant. The applied contracts reading is limited to the same finite local-to-global assembly discipline [@speranzon2018contracts], not a claim that the manuscript instantiates a full systems-of-systems semantics. Formal track definitions and section×track bindings appear in the generated tables below.

Semantic gluing then checks agreement of the glued content: coverage counts, manuscript variables, typed claim predicates, pymdp mode/hash, Bernoulli GNN ontology, and SI T-maze GNN ontology. This certificate is a content-level audit over the same base, not an additional topological law.

<!-- sheaf-track:visualization -->

![Sheaf layers overview. Left: the registry stack of {{sheaf_track_count}} composable fragment types in compose order with their renderer ids, the ordered base over which the manuscript sheaf is assembled. Right: the IMRAD section-binding heatmap across {{imrad_manifest_rows}} manifest rows ({{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing). Together the panels show how heterogeneous local evidence -- analytical, pymdp, and Lean fragments -- is layered and bound section by section, the constructive mechanism by which the multi-track active-inference and on-policy-distillation argument is glued into a single coherent document.](../output/figures/sheaf_layers_overview.png){#fig:sheaf_layers_overview width=98% fig-alt="Two-panel overview of sheaf fragment layers. Left panel shows {{sheaf_track_count}} composable track types in registry compose order with labels and renderer ids. Right panel shows the IMRAD section binding heatmap with black present, white absent, and gray missing cells across {{imrad_manifest_rows}} manifest rows and {{sheaf_track_count}} tracks."}

![Semantic gluing graph tracing the dependency chain from configured analysis scripts (producers) through the generated evidence artifacts to the manuscript consumers and validation gates that close the multi-track sheaf certificate. Each edge records a declared provenance link, so the graph is the auditable trail showing that registered figure and variable dependencies are traced to declared producers and re-checked downstream. It is the operational embodiment of the sheaf gluing condition for this artifact contract: producers, artifacts, and consumers must agree along the registered edges before the assembled active-inference / on-policy-distillation argument is accepted. Long consumer lists are visually compacted with `+N` counts while remaining bound to `output/data/validation_dependency_graph.json`.](../output/figures/semantic_gluing_graph.png){#fig:semantic_gluing_graph width=95% fig-alt="Dependency diagram linking configured analysis scripts to generated evidence artifacts, manuscript consumers, and validation gates for the semantic sheaf gluing certificate."}

![Condensed scholarship source map for {{scholarship_source_count}} bibliography source rows across {{scholarship_method_role_count}} method roles and {{scholarship_source_family_count}} source families (connected status: {{scholarship_sources_connected}}). The rendered figure is intentionally print-condensed: it shows the largest source families plus an aggregated long-tail row, where those families bind into generated artifact buckets, and the distribution of source kinds; the full row-level contract remains in `output/data/scholarship_source_matrix.json`. The map ties each external reference -- on-policy distillation and active-inference literature alike -- to a concrete place where the exemplar uses or tests it, evidencing load-bearing scholarship rather than decorative citation.](../output/figures/scholarship_source_map.png){#fig:scholarship_source_map width=95% fig-alt="Condensed source map generated from the scholarship source matrix. The left panel shows the highest-count source families plus an aggregated long-tail row, the middle panel shows where those families bind into generated artifact buckets, and the right panel summarizes source kinds."}

<!-- sheaf-track:provenance -->

The `provenance` fragment makes artifact lineage a live canonical sheaf track. The configured producer `generate_sheaf_tracks.py` writes `output/data/artifact_provenance.json`, which hashes {{validation_spine_artifact_count}} required toy artifacts and records producer scripts, source commit, deterministic seed fields, config digests, and {{provenance_bundle_count}} artifact bundles. Publication claims that depend on generated files must be traceable to this lineage table or to a narrower artifact-specific certificate.

The provenance claim is intentionally limited: every listed artifact exists, has a SHA-256 digest or an explicit cycle exclusion, is produced by a configured analysis script, and carries seed/config provenance (`{{provenance_seeded_count}}` seeded rows; all seeded flag `{{provenance_all_seeded}}`; bundle-complete flag `{{provenance_bundle_complete}}`). A changed file, missing producer, or stale saved digest is a validation failure, not a prose warning.

<!-- sheaf-track:counterexample -->

The `counterexample` fragment records expected-failure fixtures as first-class evidence. `output/reports/counterexample_matrix.json` lists {{counterexample_count}} negative controls that intentionally mutate ontology mappings, semantic certificates, graph-world trace agreement, typed claim evidence, replay rows, release parity, and provenance hashes.

The matrix is not an empirical result. It is a falsifiability ledger: each row names the gate that must fail and the test that proves the failure path remains live.

<!-- sheaf-track:adversarial_audit -->

The `adversarial_audit` fragment makes expected failures part of the sheaf rather than an informal test note. `output/reports/adversarial_audit.json` records {{adversarial_audit_count}} known-bad rows and {{adversarial_known_bad_passed}} known-bad rows passing; publication proceeds only when every row is documented as an expected failure and mapped to a gate.

The audit rows target the same failure modes as the semantic certificate: incomplete sweep cells, unnormalized uncertainty rows, interop field loss, stale certificate state, and empirical-scope leakage. The scope boundary remains toy-only: `{{scope_boundary_status}}`.

<!-- sheaf-track:evidence_fields -->

The `evidence_fields` fragment indexes the exact artifact fields that support typed claims and hydrated manuscript tokens. `output/data/evidence_field_index.json` records {{evidence_field_count}} field rows, and the track passes only when every referenced JSONPath or dotted field is present (`{{evidence_fields_mapped}}`).

<!-- sheaf-track:release_bundle -->

The `release_bundle` fragment records whether the canonical deliverables exist before copying and whether copied root outputs match or are explicitly deferred until the copy stage. `output/reports/release_bundle_manifest.json` tracks {{release_bundle_artifact_count}} required deliverables with source-present flag `{{release_bundle_sources_present}}`.

<!-- sheaf-track:gate_ergonomics -->

The `gate_ergonomics` fragment turns validation commands into evidence rows. `output/data/validation_gate_index.json` records {{validation_gate_index_count}} gate rows, each naming required inputs and the negative-control surface that should fail closed.

**Integration-audit sub-artifacts.** Beyond the named sheaf tracks, `generate_integration_audit.py` emits a set of cross-cutting audit artifacts that are each enforced with a fail-closed negative control, so this section states what every one of them guarantees rather than leaving them as unexplained inventory rows. *Producer completeness* (`output/reports/producer_completeness.json`) requires every registered sheaf-track artifact to name a configured producer script; its `all_complete` flag is re-derived from the rows, so a registered artifact with a missing or unconfigured producer fails even if the stored flag was left true. *Token provenance* (`output/data/manuscript_token_provenance.json`) maps each hydrated double-brace token placeholder back to the artifact and field that produced it; the gate independently re-scans the manuscript and requires the rendered-token set, the provenance-key set, the per-row token set, and the live re-scan to coincide, so a deleted provenance row (a rendered token with no producer) or a phantom row (a provenance key that is never rendered) fails. *Claim-evidence audit* (`output/reports/claim_evidence_audit.json`) re-derives `all_claims_typed` per row, so any manuscript claim lacking a typed evidence binding or track set fails. *Scope-boundary audit* (`output/reports/scope_boundary_audit.json`) keeps every current claim inside the deterministic toy boundary and fails on any empirical or production scope leak. *Cross-track symbol table* (`output/data/cross_track_symbol_table.json`) is the table of shared symbols and the tracks that must agree on each; it backs the gluing certificate, which fails if two tracks bind different values to one symbol. *Evidence crosswalk* (`output/data/sheaf_evidence_crosswalk.json`) ties each typed claim to the evidence artifact and gate that back it; its schema gate fails closed on a malformed or inconsistent crosswalk, and its presence is enforced upstream by the producer-completeness check. *Validation dependency graph* (`output/data/validation_dependency_graph.json`) is the producer-to-artifact-to-consumer edge set that the semantic-gluing figure renders; manuscript validation fails on an unresolved dependency edge. *Reproducibility replay* (`output/data/reproducibility_replay.json`) records the end-to-end validation-spine replay distinct from the per-producer replay matrix, and its schema gate fails closed on a malformed replay record.

<!-- sheaf-track:artifact_diffoscope -->

### Artifact diffoscope track

The `artifact_diffoscope` track compares saved provenance hashes against live
artifact hashes at the artifact root JSONPath. Its proof artifact is
`output/reports/artifact_diffoscope.json`: it currently records
{{artifact_diffoscope_row_count}} comparison rows, with equality status
`{{artifact_diffoscope_all_equal}}`.

<!-- sheaf-track:artifact_license -->

### Artifact license track

The `artifact_license` track classifies generated and project-source artifacts
under the public project license boundary. Its audit artifact is
`output/reports/artifact_license_audit.json`: it currently records
{{artifact_license_row_count}} rows, with license-safe status
`{{artifact_license_all_safe}}`.

<!-- sheaf-track:scholarship -->

The `scholarship` fragment turns citations into an audited method surface rather
than decorative bibliography. `output/data/scholarship_source_matrix.json`
records {{scholarship_source_count}} source rows across
{{scholarship_method_role_count}} method roles and
{{scholarship_source_family_count}} source families; [@fig:scholarship_source_map]
renders the resulting source-to-artifact map. The row set connects foundational
KL, variational-inference, model-compression, sequence-KD, and policy-distillation
primitives [@kullback1951information; @jordan1999variational; @blei2017variational;
@bucila2006model_compression; @kim2016sequence_kd; @rusu2016policy_distillation;
@czarnecki2019distilling_policy], foundational free-energy, predictive-coding,
Markov-blanket, and active-inference references [@friston2006fep; @friston2009rl_active_inference; @friston2010fep;
@friston2013life; @kirchhoff2018markov; @rao1999predictive; @buckley2017mathreview;
@friston2017process; @friston2017curiosity; @friston2018deep_temporal;
@millidge2021walkthrough; @dacosta2020discrete; @friston2021sophisticated;
@parr2019generalised; @millidge2020efe; @champion2024efe_unification;
@sajid2021demystified; @sajid2021bayesian_design; @devries2025efe_planning_vi;
@parr2022active; @smith2022tutorial; @tschantz2020scaling_active_inference;
@friston2021interesting_observations; @aguilera2022particular_fep;
@parr2020markov_blankets_thermo], the sequential
distribution-shift, behavioral-cloning, and distillation lineage
[@pomerleau1989alvinn; @ross2010efficient_imitation; @ross2011dagger;
@shimodaira2000covariate_shift; @sun2017aggrevated; @bengio2015scheduled; @arora2022exposure;
@rohatgi2025next_token_barrier; @pozzi2025exposure_distill;
@hinton2015distilling; @stanton2021kd_work; @gu2024minillm; @agarwal2024gkd;
@yang2024sdft_gap; @ko2024distillm; @ko2025distillm2; @wu2024rethinking_kl_kd;
@gxchen2025kl_mode_collapse; @zelikman2022star],
reinforcement-learning/control-as-inference, MaxEnt-IRL, and
preference-tilt bridges [@todorov2008duality; @toussaint2009trajectory_inference;
@ziebart2008maxent_irl; @levine2018rlinference; @abdolmaleki2018mpo;
@millidge2020active_control; @odonoghue2020rl_prob_inference;
@millidge2020iterative_amortised; @tschantz2020rl_active_inference;
@haarnoja2018sac; @ouyang2022instructgpt; @ziegler2019humanprefs; @rafailov2023dpo],
privileged-information sources
[@vapnik2009lupi; @lopezpaz2016unifying; @sharoni2023privileged_erm; @cai2024privileged_pomdp;
@penaloza2026pidistill; @penaloza2026tutorial],
recent self-distillation and entropy/hybrid OPD references [@zhao2026opsd; @shenfeld2026sdft;
@hubotter2026sdpo; @liu2026sdpg; @lauyikfung2026sdpgcode; @jin2026entropy_opd;
@zhu2026hpd; @liu2026pwopsd; @oh2026vopd; @xing2026tropd; @jang2026veto; @ye2025blackbox_opd],
empirical reasoning-distillation and speculative-KD context [@qwen2025technical_report;
@thinkingmachines2025opd; @deepseek2025r1; @xu2024speculative_kd],
OPD landscape indexes [@awesomeopd2026;
@song2026opdsurvey; @zhu2026manyfacesopd; @ramos2026dgrpo; @liu2026oisd],
implementation, reproducibility, and notation anchors [@pymdp2022; @gnn2023; @koudahl2023synthetic;
@sandve2013reproducible; @wilkinson2016fair],
applied sheaf sources [@curry2014sheaves; @speranzon2018contracts;
@robinson2014topological; @robinson2017sensor_sheaf; @phillips2019sheaving;
@fong2019applied_category; @rosiak2022sheaf_examples; @cox2026fragmented_risk_sheaf],
and statistical-method reporting [@cohen1988power]
to the exact artifact or method role they support.

The validation claim is deliberately narrow: every row must have a bibliography
entry with a DOI or URL, a manuscript citation, a registered sheaf track, a bound
manifest section, an existing evidence artifact, and a claim-boundary statement.
The hydrated flag `{{scholarship_sources_connected}}` is therefore a
source-traceability claim, not a claim that the toy results inherit empirical
support from the cited literature.

<!-- sheaf-track:manuscript_staleness -->

The `manuscript_staleness` fragment closes the hydration loop. `output/reports/manuscript_staleness_report.json` checks {{manuscript_staleness_row_count}} manuscript token bindings against the current generated variables after resolved markdown is written; the pass flag is `{{manuscript_staleness_all_fresh}}`.

`output/reports/manuscript_hardcoded_variable_audit.json` then scans the source fragments for guarded generated values that appear as prose literals instead of double-brace manuscript-variable placeholders. It guards {{hardcoded_variable_guarded_count}} formatted token values and records {{hardcoded_variable_issue_count}} hard-coded-value issues; the pass flag is `{{hardcoded_variables_all_auto_injected}}`.

This is a publication-systems claim, not a domain result. A stale hydrated value, unresolved token, hard-coded generated value, or missing resolved section becomes a validation failure before PDF or web outputs are accepted.

<!-- sheaf-track:layers -->

<!-- sheaf-layers:registry -->
## Sheaf fragment track registry

Compose order and renderer bindings from `manuscript/sheaf/tracks.yaml`.

| Order | Track id | Label | Renderer | Optional |
| ---: | --- | --- | --- | --- |
| 10 | `prose` | Narrative prose | `markdown` | No |
| 20 | `formalism` | Mathematical formalism | `markdown` | No |
| 30 | `simulation` | Analytical simulation notes | `markdown` | No |
| 32 | `assumption_index` | Analytical assumption index | `markdown` | No |
| 35 | `layers` | Sheaf layers tables | `layers_report` | Yes |
| 40 | `pymdp` | pymdp harness artifacts | `markdown` | No |
| 41 | `interop` | GNN/ontology/JSON interop checks | `markdown` | No |
| 42 | `provenance` | Artifact provenance and bundle lineage spine | `markdown` | No |
| 45 | `replay_matrix` | Deterministic replay matrix | `markdown` | No |
| 48 | `counterexample` | Expected-failure counterexamples | `markdown` | No |
| 50 | `adversarial_audit` | Adversarial audit matrix | `markdown` | No |
| 52 | `evidence_fields` | Evidence field index | `markdown` | No |
| 53 | `release_bundle` | Release bundle parity manifest | `markdown` | No |
| 54 | `gate_ergonomics` | Validation gate ergonomics | `markdown` | No |
| 55 | `artifact_diffoscope` | Artifact diffoscope | `markdown` | No |
| 56 | `artifact_license` | Artifact license audit | `markdown` | No |
| 57 | `scholarship` | Source-backed scholarship matrix | `markdown` | No |
| 60 | `sensitivity` | Toy sensitivity sweep | `markdown` | No |
| 62 | `uncertainty` | Toy uncertainty summaries | `markdown` | No |
| 65 | `benchmark` | Compact toy benchmark matrix | `markdown` | No |
| 66 | `manuscript_staleness` | Hydrated manuscript staleness report | `markdown` | No |
| 67 | `visualization` | Figure references | `section_figures` | No |
| 70 | `lean` | Lean boundary fragment | `markdown` | No |
| 75 | `model_checking` | Finite-state model checking witnesses | `markdown` | No |
| 76 | `theorem_traceability` | Lean theorem traceability matrix | `markdown` | No |
| 77 | `proof_extraction` | Lean proof extraction index | `markdown` | No |
| 78 | `state_space_catalog` | Finite state-space catalog | `markdown` | No |
| 79 | `causal_ablation` | Deterministic causal ablation matrix | `markdown` | No |
| 80 | `gnn` | GNN notation fragment | `markdown` | No |
| 90 | `ontology` | Active Inference Ontology bindings | `ontology_yaml` | No |
| 100 | `animation` | Animation fragment | `markdown` | Yes |
| 102 | `animation_delta` | Animation frame-delta manifest | `markdown` | No |
| 110 | `release_notes` | Release notes evidence | `markdown` | No |

**Track count:** {{sheaf_track_count}} registered fragment types.

<!-- sheaf-layers:binding-matrix -->
## IMRAD binding matrix

Section rows versus fragment track columns. **P** = present (bound and file exists); **—** = absent (not bound); **M** = missing (bound, file absent).

| Section | prose | formalism | simulation | assumption_index | layers | pymdp | interop | provenance | replay_matrix | counterexample | adversarial_audit | evidence_fields | release_bundle | gate_ergonomics | artifact_diffoscope | artifact_license | scholarship | sensitivity | uncertainty | benchmark | manuscript_staleness | visualization | lean | model_checking | theorem_traceability | proof_extraction | state_space_catalog | causal_ablation | gnn | ontology | animation | animation_delta | release_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Introduction (group) | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
|   Motivation and scope | P | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | P | — | — | — | — | — | — | — | — | — | — | — |
|   Contributions | P | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | P | — | — | — | — | — | — | — | P | — | — | — |
| Methods (group) | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
|   Teacher and student coupling: the analytical model | P | P | P | P | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | P | — | — | — | — | — | — | P | P | — | — | — |
|   On-policy student: pymdp sophisticated inference | P | P | — | — | — | P | P | — | — | — | — | — | — | — | — | — | — | — | — | — | — | P | — | — | — | — | — | — | P | P | — | — | — |
|   Machine-checked correspondence (Lean) | P | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | P | P | P | P | P | — | — | — | — | — | — | — |
| Results (group) | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
|   Teacher and student mutual information | P | P | P | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | P | — | — | — | — | — | — | — | — | — | — | — |
|   Free-energy decomposition | P | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | P | — | — | — | — | — | — | — | — | — | — | — |
|   On-policy student rollout (T-maze) | P | — | — | — | — | P | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | P | — | — | — | — | — | — | — | — | — | — | — |
| Discussion (group) | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
|   Limitations and outlook | P | — | P | — | — | — | — | — | — | — | — | — | — | — | — | — | P | — | — | — | — | P | — | — | — | — | — | — | — | P | — | — | P |
| Appendix (group) | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
|   Supplementary material: full coverage and concordance | P | P | P | P | — | P | P | P | P | P | P | P | P | P | P | P | P | P | P | P | — | P | — | — | — | — | P | P | — | — | — | — | — |
|   Supplementary material: reproducibility methodology | P | P | — | — | P | — | — | P | — | P | P | P | P | P | P | P | P | — | — | — | P | P | — | — | — | — | — | — | — | — | — | — | — |
|   Supplementary material: validation invariants and statistics | P | — | P | — | — | — | — | — | P | — | — | — | — | — | — | — | — | P | P | P | P | P | P | P | P | P | P | P | P | P | P | P | P |

**Totals:** {{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing.

<!-- sheaf-layers:legend -->
| Symbol | Coverage color | Meaning |
| --- | --- | --- |
| P | Black | Track **present** (bound and fragment exists) |
| — | White | **Absent** (not bound for this section) |
| M | Gray | **Missing** (bound but fragment file absent) |

<!-- sheaf-layers:section-status -->
## Section-track status

Generated status for the current manuscript sheaf, summarized per composable section.

| Section | IMRAD | Bound | Present | Missing | Status |
| --- | --- | ---: | ---: | ---: | --- |
| Motivation and scope | introduction | 2 | 2 | 0 | `fully_sheafed` |
| Contributions | introduction | 3 | 3 | 0 | `fully_sheafed` |
| Teacher and student coupling: the analytical model | methods | 7 | 7 | 0 | `fully_sheafed` |
| On-policy student: pymdp sophisticated inference | methods | 7 | 7 | 0 | `fully_sheafed` |
| Machine-checked correspondence (Lean) | methods | 6 | 6 | 0 | `fully_sheafed` |
| Teacher and student mutual information | results | 4 | 4 | 0 | `fully_sheafed` |
| Free-energy decomposition | results | 2 | 2 | 0 | `fully_sheafed` |
| On-policy student rollout (T-maze) | results | 3 | 3 | 0 | `fully_sheafed` |
| Limitations and outlook | discussion | 6 | 6 | 0 | `fully_sheafed` |
| Supplementary material: full coverage and concordance | appendix | 22 | 22 | 0 | `fully_sheafed` |
| Supplementary material: reproducibility methodology | appendix | 14 | 14 | 0 | `fully_sheafed` |
| Supplementary material: validation invariants and statistics | appendix | 19 | 19 | 0 | `fully_sheafed` |

**Section status:** 12 / 12 composable sections fully sheafed; 0 required bound fragments missing.

<!-- sheaf-layers:track-status -->
## Track status

| Track | Renderer | Bound sections | Present | Missing | Claims | Status |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `prose` | `markdown` | 12 | 12 | 0 | 0 | `complete` |
| `formalism` | `markdown` | 5 | 5 | 0 | 0 | `complete` |
| `simulation` | `markdown` | 5 | 5 | 0 | 29 | `complete` |
| `assumption_index` | `markdown` | 2 | 2 | 0 | 1 | `complete` |
| `layers` | `layers_report` | 1 | 1 | 0 | 1 | `complete` |
| `pymdp` | `markdown` | 3 | 3 | 0 | 24 | `complete` |
| `interop` | `markdown` | 2 | 2 | 0 | 6 | `complete` |
| `provenance` | `markdown` | 2 | 2 | 0 | 12 | `complete` |
| `replay_matrix` | `markdown` | 2 | 2 | 0 | 3 | `complete` |
| `counterexample` | `markdown` | 2 | 2 | 0 | 2 | `complete` |
| `adversarial_audit` | `markdown` | 2 | 2 | 0 | 11 | `complete` |
| `evidence_fields` | `markdown` | 2 | 2 | 0 | 2 | `complete` |
| `release_bundle` | `markdown` | 2 | 2 | 0 | 5 | `complete` |
| `gate_ergonomics` | `markdown` | 2 | 2 | 0 | 5 | `complete` |
| `artifact_diffoscope` | `markdown` | 2 | 2 | 0 | 1 | `complete` |
| `artifact_license` | `markdown` | 2 | 2 | 0 | 1 | `complete` |
| `scholarship` | `markdown` | 3 | 3 | 0 | 12 | `complete` |
| `sensitivity` | `markdown` | 2 | 2 | 0 | 10 | `complete` |
| `uncertainty` | `markdown` | 2 | 2 | 0 | 6 | `complete` |
| `benchmark` | `markdown` | 2 | 2 | 0 | 3 | `complete` |
| `manuscript_staleness` | `markdown` | 2 | 2 | 0 | 1 | `complete` |
| `visualization` | `section_figures` | 12 | 12 | 0 | 16 | `complete` |
| `lean` | `markdown` | 2 | 2 | 0 | 8 | `complete` |
| `model_checking` | `markdown` | 2 | 2 | 0 | 7 | `complete` |
| `theorem_traceability` | `markdown` | 2 | 2 | 0 | 3 | `complete` |
| `proof_extraction` | `markdown` | 2 | 2 | 0 | 2 | `complete` |
| `state_space_catalog` | `markdown` | 2 | 2 | 0 | 2 | `complete` |
| `causal_ablation` | `markdown` | 2 | 2 | 0 | 2 | `complete` |
| `gnn` | `markdown` | 3 | 3 | 0 | 5 | `complete` |
| `ontology` | `ontology_yaml` | 5 | 5 | 0 | 7 | `complete` |
| `animation` | `markdown` | 1 | 1 | 0 | 2 | `complete` |
| `animation_delta` | `markdown` | 1 | 1 | 0 | 1 | `complete` |
| `release_notes` | `markdown` | 2 | 2 | 0 | 2 | `complete` |

**Status cells:** 561 section-track cells.

<!-- sheaf-layers:render-log -->
## Render and logging summary

| Event | Component | Output | Status | Detail |
| --- | --- | --- | --- | --- |
| `registry_loaded` | `sheaf.registry` | `registered_tracks` | `ok` | 33 tracks |
| `manifest_loaded` | `sheaf.manifest` | `manifest_sections` | `ok` | 17 sections |
| `coverage_matrix_built` | `sheaf.coverage` | `output/data/sheaf_coverage_matrix.json` | `ok` | 95 present cells |
| `section_status_matrix_built` | `sheaf.status` | `output/data/sheaf_section_status_matrix.json` | `ok` | 561 section-track cells |
| `layers_renderer_bound` | `sheaf.layers_report` | `manuscript/19_supplement_reproducibility.md` | `ok` | methods sheaf layer tables |
| `semantic_artifacts_indexed` | `sheaf.semantic` | `output/data/validation_dependency_graph.json` | `ok` | 116 artifact producer rows |
| `validation_gates_indexed` | `gates` | `output/data/validation_gate_index.json` | `ok` | 3 gate groups |
| `manuscript_sections_composed` | `sheaf.compose` | `manuscript/*.md` | `ok` | 16 composed markdown files |

**Render events:** 8.

<!-- sheaf-layers:evidence-crosswalk -->
## Evidence crosswalk

| Claim | Artifact | Producer | Gates |
| --- | --- | --- | --- |
| `sheaf_registry` | `manuscript/sheaf/tracks.yaml` | `manual` | validate_outputs |
| `sheaf_manifest` | `manuscript/sheaf/manifest.yaml` | `manual` | validate_outputs |
| `sheaf_coverage_config` | `manuscript/sheaf/coverage.yaml` | `manual` | validate_outputs |
| `sheaf_coverage_matrix` | `output/data/sheaf_coverage_matrix.json` | `generate_figures.py` | validate_outputs, validate_manuscript |
| `sheaf_gluing_certificate` | `output/data/sheaf_gluing_certificate.json` | `generate_sheaf_tracks.py` | validate_manuscript, validate_outputs |
| `sheaf_evidence_crosswalk` | `output/data/sheaf_evidence_crosswalk.json` | `generate_sheaf_tracks.py` | validate_manuscript, validate_outputs |
| `evidence_field_index` | `output/data/evidence_field_index.json` | `generate_sheaf_tracks.py` | validate_outputs, validate_manuscript |
| `validation_dependency_graph` | `output/data/validation_dependency_graph.json` | `generate_sheaf_tracks.py` | validate_manuscript, validate_outputs |

**Claim rows:** 128 typed evidence claims.

<!-- sheaf-layers:artifact-producers -->
## Artifact producer graph

| Artifact | Producer | Configured | Consumers |
| --- | --- | --- | --- |
| `output/data/analysis_statistics.json` | `compute_statistics.py` | Yes | results_si_tmaze, results_invariants |
| `output/data/analytical_assumption_index.json` | `generate_toy_sweep_tracks.py` | Yes | methods_analytical, appendix_full_sheaf |
| `output/data/analytical_observable_sweep.json` | `generate_toy_sweep_tracks.py` | Yes | results_invariants, appendix_full_sheaf |
| `output/data/animation_frame_deltas.json` | `render_animation.py` | Yes | appendix_full_sheaf |
| `output/data/artifact_provenance.json` | `generate_sheaf_tracks.py` | Yes | methods_sheaf |
| `output/data/causal_ablation_matrix.json` | `generate_toy_sweep_tracks.py` | Yes | results_invariants, appendix_full_sheaf |
| `output/data/cross_track_symbol_table.json` | `generate_integration_audit.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/data/evidence_field_index.json` | `generate_sheaf_tracks.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/data/figure_source_map.json` | `generate_integration_audit.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/data/firstprinciples/benchmark_table.md` | `generate_firstprinciples.py` | Yes | appendix_full_sheaf |
| `output/data/firstprinciples/classroom.json` | `generate_firstprinciples.py` | Yes | intro_motivation, results_si_tmaze, discussion_outlook |
| `output/data/firstprinciples/correspondence_map.json` | `generate_firstprinciples.py` | Yes | intro_contributions, methods_analytical, methods_sheaf, discussion_outlook |
| `output/data/firstprinciples/correspondence_table.md` | `generate_firstprinciples.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/data/firstprinciples/divergence_demo.json` | `generate_firstprinciples.py` | Yes | methods_analytical, discussion_outlook |
| `output/data/firstprinciples/empirical_benchmark.json` | `generate_firstprinciples.py` | Yes | discussion_outlook, appendix_full_sheaf |
| `output/data/firstprinciples/exposure_bias_demo.json` | `generate_firstprinciples.py` | Yes | intro_motivation, methods_pymdp, discussion_outlook |
| `output/data/firstprinciples/opd_taxonomy.json` | `generate_firstprinciples.py` | Yes | intro_motivation, methods_sheaf, discussion_outlook |
| `output/data/firstprinciples/privilege_sweep.json` | `generate_firstprinciples.py` | Yes | results_si_tmaze, appendix_full_sheaf |
| `output/data/firstprinciples/reward_tilting_demo.json` | `generate_firstprinciples.py` | Yes | methods_analytical, discussion_outlook |
| `output/data/firstprinciples/sdpg_demo.json` | `generate_firstprinciples.py` | Yes | methods_analytical, discussion_outlook |
| `output/data/firstprinciples/sequential_shift.json` | `generate_firstprinciples.py` | Yes | results_si_tmaze, discussion_outlook |
| `output/data/firstprinciples/sequential_shift_sensitivity.json` | `generate_firstprinciples.py` | Yes | results_si_tmaze, discussion_outlook |
| `output/data/firstprinciples/statistics_demo.json` | `generate_firstprinciples.py` | Yes | results_invariants, appendix_full_sheaf |
| `output/data/firstprinciples/taxonomy_table.md` | `generate_firstprinciples.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/data/gnn_roundtrip_report.json` | `generate_formal_interop_tracks.py` | Yes | methods_pymdp, appendix_full_sheaf |
| `output/data/interop_roundtrip_report.json` | `generate_sheaf_tracks.py` | Yes | methods_pymdp, appendix_full_sheaf |
| `output/data/manuscript_evidence_tables.json` | `generate_integration_audit.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/data/manuscript_token_provenance.json` | `generate_integration_audit.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/data/manuscript_variables.json` | `z_generate_manuscript_variables.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/data/ontology_alias_index.json` | `generate_formal_interop_tracks.py` | Yes | methods_pymdp, appendix_full_sheaf |
| `output/data/ontology_profile_matrix.json` | `generate_formal_interop_tracks.py` | Yes | methods_pymdp, appendix_full_sheaf |
| `output/data/parameter_sweep.csv` | `run_analytical_sweep.py` | Yes | methods_analytical, results_mi_sweep |
| `output/data/proof_dependency_graph.json` | `generate_sheaf_tracks.py` | Yes | methods_lean, appendix_full_sheaf |
| `output/data/proof_extraction_index.json` | `generate_formal_interop_tracks.py` | Yes | methods_lean, appendix_full_sheaf |
| `output/data/pymdp_policy_posterior_grid.json` | `simulate_si_tmaze.py` | Yes | methods_pymdp, appendix_full_sheaf |
| `output/data/scholarship_source_matrix.json` | `generate_sheaf_tracks.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/data/sensitivity_sweep.json` | `generate_sheaf_tracks.py` | Yes | results_invariants, appendix_full_sheaf |
| `output/data/sheaf_coverage_matrix.json` | `generate_figures.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/data/sheaf_evidence_crosswalk.json` | `generate_sheaf_tracks.py` | Yes | methods_sheaf |
| `output/data/sheaf_gluing_certificate.json` | `generate_sheaf_tracks.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/data/sheaf_section_status_matrix.json` | `generate_sheaf_tracks.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/data/si_efe_terms.json` | `generate_toy_sweep_tracks.py` | Yes | results_invariants, appendix_full_sheaf |
| `output/data/si_graph_world_summary.json` | `simulate_si_graph_world.py` | Yes | methods_pymdp, results_si_tmaze |
| `output/data/si_graph_world_topology_sweep.json` | `generate_toy_sweep_tracks.py` | Yes | results_invariants, appendix_full_sheaf |
| `output/data/si_graph_world_topology_traces.json` | `generate_toy_sweep_tracks.py` | Yes | results_invariants, appendix_full_sheaf |
| `output/data/si_graph_world_trace.json` | `simulate_si_graph_world.py` | Yes | methods_pymdp, results_si_tmaze, appendix_full_sheaf |
| `output/data/si_policy_comparison.json` | `simulate_si_tmaze.py` | Yes | methods_pymdp, results_si_tmaze |
| `output/data/si_policy_grid.json` | `generate_toy_sweep_tracks.py` | Yes | results_invariants, appendix_full_sheaf |
| `output/data/si_tmaze_model_matrices.json` | `simulate_si_tmaze.py` | Yes | methods_pymdp, results_si_tmaze, appendix_full_sheaf |
| `output/data/si_tmaze_summary.json` | `simulate_si_tmaze.py` | Yes | methods_pymdp, results_si_tmaze |
| `output/data/si_tmaze_trace.json` | `simulate_si_tmaze.py` | Yes | methods_pymdp, results_si_tmaze |
| `output/data/state_space_catalog.json` | `generate_toy_sweep_tracks.py` | Yes | results_invariants, appendix_full_sheaf |
| `output/data/state_transition_table.json` | `generate_sheaf_tracks.py` | Yes | results_invariants, appendix_full_sheaf |
| `output/data/theorem_traceability_matrix.json` | `generate_sheaf_tracks.py` | Yes | methods_lean, appendix_full_sheaf |
| `output/data/toy_benchmark_matrix.json` | `generate_toy_sweep_tracks.py` | Yes | results_invariants, appendix_full_sheaf |
| `output/data/track_improvement_scope.json` | `generate_sheaf_tracks.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/data/uncertainty_summary.json` | `generate_sheaf_tracks.py` | Yes | results_invariants, appendix_full_sheaf |
| `output/data/validation_dependency_graph.json` | `generate_sheaf_tracks.py` | Yes | methods_sheaf |
| `output/data/validation_gate_index.json` | `generate_integration_audit.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/figures/si_belief_trajectory.gif` | `render_animation.py` | Yes | appendix_full_sheaf |
| `output/reports/ablation_sensitivity_report.json` | `generate_sheaf_tracks.py` | Yes | results_invariants, appendix_full_sheaf |
| `output/reports/adversarial_audit.json` | `generate_sheaf_tracks.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/reports/artifact_diffoscope.json` | `generate_integration_audit.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/reports/artifact_license_audit.json` | `generate_integration_audit.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/reports/blocked_scope_manifest.json` | `generate_sheaf_tracks.py` | Yes | methods_sheaf, discussion_outlook, appendix_full_sheaf |
| `output/reports/claim_evidence_audit.json` | `generate_integration_audit.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/reports/counterexample_matrix.json` | `generate_sheaf_tracks.py` | Yes | methods_sheaf |
| `output/reports/figure_hash_manifest.json` | `generate_integration_audit.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/reports/gnn_lint_report.json` | `generate_formal_interop_tracks.py` | Yes | methods_pymdp, appendix_full_sheaf |
| `output/reports/graph_world_invariants.json` | `generate_toy_sweep_tracks.py` | Yes | results_invariants, appendix_full_sheaf |
| `output/reports/invariants.json` | `run_analytical_sweep.py` | Yes | results_invariants |
| `output/reports/lean_graph_world_inventory.json` | `generate_formal_interop_tracks.py` | Yes | methods_lean, appendix_full_sheaf |
| `output/reports/lean_theorem_inventory.json` | `generate_formal_interop_tracks.py` | Yes | methods_lean, appendix_full_sheaf |
| `output/reports/manuscript_hardcoded_variable_audit.json` | `generate_integration_audit.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/reports/manuscript_staleness_report.json` | `z_generate_manuscript_variables.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/reports/model_checking_witnesses.json` | `generate_sheaf_tracks.py` | Yes | methods_lean, appendix_full_sheaf |
| `output/reports/producer_completeness.json` | `generate_integration_audit.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/reports/pymdp_runtime_diagnostics.json` | `simulate_si_tmaze.py` | Yes | methods_pymdp, appendix_full_sheaf |
| `output/reports/release_attestation.json` | `generate_sheaf_tracks.py` | Yes | discussion_outlook, appendix_full_sheaf |
| `output/reports/release_bundle_manifest.json` | `generate_sheaf_tracks.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/reports/release_notes_evidence.json` | `generate_integration_audit.py` | Yes | discussion_outlook, appendix_full_sheaf |
| `output/reports/replay_matrix.json` | `generate_sheaf_tracks.py` | Yes | results_invariants, appendix_full_sheaf |
| `output/reports/reproducibility_replay.json` | `generate_validation_spine.py` | Yes | results_invariants |
| `output/reports/scope_boundary_audit.json` | `generate_integration_audit.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/reports/sheaf_render_log.json` | `generate_sheaf_tracks.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/reports/si_invariants.json` | `simulate_si_tmaze.py` | Yes | results_si_tmaze |
| `output/reports/si_tmaze_run_report.json` | `simulate_si_tmaze.py` | Yes | results_si_tmaze |
| `output/reports/stale_artifact_report.json` | `generate_integration_audit.py` | Yes | methods_sheaf, appendix_full_sheaf |
| `output/reports/visualization_quality_audit.json` | `generate_integration_audit.py` | Yes | methods_sheaf, appendix_full_sheaf |

**Producer issues:** 0.

<!-- sheaf-layers:semantic-restrictions -->
## Semantic gluing restrictions

| Restriction | Value |
| --- | --- |
| Coverage missing | `0` |
| Policy comparison rows | `2` |
| Policy grid complete | `True` |
| Policy posterior rows | `14` |
| Policy posterior normalized | `True` |
| Runtime unexpected warnings | `0` |
| Graph-world trace agrees | `True` |
| Animation frames | `4` |
| Lean all proved | `True` |
| GNN ontology ok | `True` |
| Configured producers ok | `True` |
| Semantic certificate ok | `not evaluated` |
| Dependency edges ok | `True` |
| Track scope complete | `True` |
| Empirical adapter blocked | `True` |
| Provenance bundles complete | `True` |
| Replay rows matched | `True` |
| Sensitivity complete | `True` |
| Uncertainty normalized | `True` |
| Evidence fields mapped | `True` |
| Release bundle sources present | `True` |
| Theorem traceability linked | `True` |
| Gate ergonomics indexed | `True` |
| Interop lossless | `True` |
| Scope toy-only | `True` |

<!-- sheaf-layers:track-improvement-scope -->
## Track improvement scope

| Track | Status | Current proof | Next artifact | Gate | Negative control |
| --- | --- | --- | --- | --- | --- |
| `adversarial_audit` | live | `output/reports/adversarial_audit.json` | `output/reports/adversarial_audit.json` | `validate_outputs, validate_manuscript` | adversarial_known_bad_passes |
| `animation` | optional | `output/figures/si_belief_trajectory.gif` | `output/figures/si_belief_trajectory.gif` | `validate_outputs` | missing_fragment_coverage |
| `animation_delta` | live | `output/data/animation_frame_deltas.json` | `output/data/animation_frame_deltas.json` | `validate_outputs, validate_manuscript` | missing_fragment_coverage |
| `artifact_diffoscope` | live | `output/reports/artifact_diffoscope.json` | `output/reports/artifact_diffoscope.json` | `validate_outputs, validate_manuscript` | artifact_diffoscope_missed_hash_drift |
| `artifact_license` | live | `output/reports/artifact_license_audit.json` | `output/reports/artifact_license_audit.json` | `validate_outputs, validate_manuscript` | artifact_license_unsafe_artifact |
| `assumption_index` | live | `output/data/analytical_assumption_index.json` | `output/data/analytical_assumption_index.json` | `validate_outputs, validate_manuscript` | missing_fragment_coverage |
| `benchmark` | live | `output/data/toy_benchmark_matrix.json` | `output/data/toy_benchmark_matrix.json` | `validate_outputs` | missing_fragment_coverage |
| `causal_ablation` | live | `output/data/causal_ablation_matrix.json` | `output/data/causal_ablation_matrix.json` | `validate_outputs, validate_manuscript` | causal_ablation_missing_cell |
| `counterexample` | live | `output/reports/counterexample_matrix.json` | `output/reports/counterexample_matrix.json` | `validate_outputs, validate_manuscript` | known_bad_counterexample_passed |
| `evidence_fields` | live | `output/data/evidence_field_index.json` | `output/data/evidence_field_index.json` | `validate_outputs, validate_manuscript` | missing_typed_claim |
| `formalism` | live | `manuscript/sheaf/manifest.yaml` | `manuscript/sheaf/manifest.yaml` | `validate_manuscript` | missing_fragment_coverage |
| `gate_ergonomics` | live | `output/data/validation_gate_index.json` | `output/data/validation_gate_index.json` | `validate_outputs, validate_manuscript` | gate_ergonomics_unindexed |
| `gnn` | live | `output/reports/gnn_lint_report.json` | `output/reports/gnn_lint_report.json` | `validate_outputs` | missing_fragment_coverage |
| `interop` | live | `output/data/interop_roundtrip_report.json` | `output/data/interop_roundtrip_report.json` | `validate_outputs` | interop_shape_loss |
| `layers` | optional | `output/data/sheaf_coverage_matrix.json` | `output/data/sheaf_coverage_matrix.json` | `validate_outputs, validate_manuscript` | missing_fragment_coverage |
| `lean` | live | `output/reports/lean_theorem_inventory.json` | `output/reports/lean_theorem_inventory.json` | `validate_outputs` | missing_fragment_coverage |
| `manuscript_staleness` | live | `output/reports/manuscript_staleness_report.json` | `output/reports/manuscript_staleness_report.json` | `validate_outputs, validate_manuscript` | missing_fragment_coverage |
| `model_checking` | live | `output/reports/model_checking_witnesses.json` | `output/reports/model_checking_witnesses.json` | `validate_outputs` | missed_model_checking_counterexample |
| `ontology` | live | `output/data/ontology_profile_matrix.json` | `output/data/ontology_profile_matrix.json` | `validate_outputs` | missing_fragment_coverage |
| `proof_extraction` | live | `output/data/proof_extraction_index.json` | `output/data/proof_extraction_index.json` | `validate_outputs, validate_manuscript` | proof_extraction_missing_statement |
| `prose` | live | `manuscript/sheaf/manifest.yaml` | `manuscript/sheaf/manifest.yaml` | `validate_manuscript` | missing_fragment_coverage |
| `provenance` | live | `output/data/artifact_provenance.json` | `output/data/artifact_provenance.json` | `validate_manuscript, validate_outputs` | missing_sheaf_track_producer |
| `pymdp` | live | `output/data/si_policy_comparison.json` | `output/data/si_policy_comparison.json` | `validate_outputs` | missing_fragment_coverage |
| `release_bundle` | live | `output/reports/release_bundle_manifest.json` | `output/reports/release_bundle_manifest.json` | `validate_outputs, validate_manuscript` | release_bundle_parity_failure |
| `release_notes` | live | `output/reports/release_notes_evidence.json` | `output/reports/release_notes_evidence.json` | `validate_outputs, validate_manuscript` | release_notes_claim_failed_gate_passed |
| `replay_matrix` | live | `output/reports/replay_matrix.json` | `output/reports/replay_matrix.json` | `validate_outputs, validate_manuscript` | replay_mismatch |
| `scholarship` | live | `output/data/scholarship_source_matrix.json` | `output/data/scholarship_source_matrix.json` | `validate_outputs, validate_manuscript` | missing_scholarship_source_binding |
| `sensitivity` | live | `output/data/sensitivity_sweep.json` | `output/data/sensitivity_sweep.json` | `validate_outputs` | missing_sensitivity_cell |
| `simulation` | live | `output/data/analytical_observable_sweep.json` | `output/data/analytical_observable_sweep.json` | `validate_outputs` | missing_fragment_coverage |
| `state_space_catalog` | live | `output/data/state_space_catalog.json` | `output/data/state_space_catalog.json` | `validate_outputs, validate_manuscript` | state_space_catalog_missing_finite_space |
| `theorem_traceability` | live | `output/data/theorem_traceability_matrix.json` | `output/data/theorem_traceability_matrix.json` | `validate_outputs, validate_manuscript` | theorem_traceability_unlinked |
| `uncertainty` | live | `output/data/uncertainty_summary.json` | `output/data/uncertainty_summary.json` | `validate_outputs` | unnormalized_uncertainty_row |
| `visualization` | live | `output/data/figure_source_map.json` | `output/data/figure_source_map.json` | `validate_outputs, validate_manuscript` | missing_fragment_coverage |
| `empirical_adapter` | blocked | `output/reports/blocked_scope_manifest.json` | `output/data/empirical_adapter_manifest.json` | `blocked_scope_manifest.all_blocked` | empirical claim appears without manifest |
| `private_or_restricted_data` | blocked | `output/reports/blocked_scope_manifest.json` | `output/data/private_data_provenance_manifest.json` | `blocked_scope_manifest.all_blocked` | private data artifact appears without provenance manifest |
| `network_dependent_research` | blocked | `output/reports/blocked_scope_manifest.json` | `output/data/network_replay_manifest.json` | `blocked_scope_manifest.all_blocked` | network-derived claim appears without replay manifest |
| `llm_generated_evidence` | blocked | `output/reports/blocked_scope_manifest.json` | `output/data/llm_evidence_audit.json` | `blocked_scope_manifest.all_blocked` | LLM-generated evidence appears as a validation source |
| `non_toy_model_claims` | blocked | `output/reports/blocked_scope_manifest.json` | `output/data/non_toy_model_scope_manifest.json` | `blocked_scope_manifest.all_blocked` | non-toy result claim appears outside future-only scope |

**Improvement rows:** 38.

