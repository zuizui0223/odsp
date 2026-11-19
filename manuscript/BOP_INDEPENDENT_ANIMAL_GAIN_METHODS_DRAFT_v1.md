# From held-out prediction gains to future animals: an auditable individual-level transfer protocol for ecological-state models

**Working manuscript v1 — not submission-ready.** The underlying statistical rank guarantee is standard split-conformal reasoning. The contribution evaluated here is an executable and auditable pipeline integrating ecological state-score references, animal-level independence, model-to-forecast provenance and fail-closed source eligibility. The external biological demonstration remains incomplete; all prior empirical and synthetic endpoints are frozen and unchanged.

**Potential article format:** methods development or software/methodology article. *Methods in Ecology and Evolution* is a possible fit based on its methodological remit, **not** a submission decision or a prediction of acceptance. Its scientific novelty relative to conformal inference and ODSP's existing N2 reference-alignment paper remains an editorial risk.

## Abstract

**1.** Ecological state-prediction models increasingly return full probabilities for movement, habitat or vertical states. Positive held-out performance averaged over many measurements can nevertheless obscure failures in individual animals and says little about the performance of one future independent animal. A second source of confusion is whether an apparent gain reflects added ecological context or an easier training-data reference distribution.

**2.** We present an auditable method that defines one mean log-score gain per animal against a prespecified training-only reference, fits a one-sided order-statistic lower prediction bound on separate calibration animals, and tests that frozen bound on untouched animals. The software binds source training rows to reproducible model and comparator artifacts, forecasts and animal-group identities, while stopping inference when independent calibration numbers or cross-source feature compatibility are insufficient. The rank coverage argument is standard and is valid only when calibration and future *animal gains* are exchangeable for the specified frozen predictor/reference.

**3.** In an earlier, prospectively frozen public BOP_RODENT analysis, the primary state random forest had positive log-score gain in 27 of 30 birds and positive Brier improvement in all 30, but the predetermined all-individual conclusion was **mixed**. Three independently frozen known-truth method experiments produced same-process future-group lower-bound coverage of 89.94%, 89.15% and 90.24% at nominal 90%; deliberately altered validation distributions reduced coverage to 6.81%, 12.87% and 26.28%, respectively. A post-result world-level uncertainty audit avoids treating animals sharing one model/calibrator as fully independent Monte Carlo replicates.

**4.** Public data-source audits also revealed a hard limit: a newer same-study BOP release did not supply enough genuinely new birds within any single species for the planned 90% calibration-plus-validation test, while the independent Schaub/Dryad source lacked a predictor required by the historical random forest and had unresolved animal-identity overlap. Neither source was promoted to empirical external validation. Our result is an **executable group-level evidence and stopping protocol**, not a novel conformal theorem or a claim of universal ecological prediction transfer.

**Keywords:** biologging; calibration; exchangeability; individual-level validation; predictive log score; reproducibility; species stratification; ecological states.

## 1 | Introduction

An ecological model can represent a species' state as a distribution over discrete altitude strata, habitat categories or temporal states, rather than compressing every event to a single predicted value. The benefit of conditioning on additional predictors can be assessed with proper probability scoring. Logarithmic and quadratic/Brier scoring rules are established proper scores for probabilistic forecasts (Gneiting & Raftery, 2007). However, three logical leaps often separate an encouraging result from a defensible future-animal claim.

First, one bird may contribute thousands of autocorrelated GPS observations. A gain measured across those positions does not create thousands of independent demonstrations of generalization. The appropriate calibration unit for a new-bird claim is the **bird**, not the GPS fix. This is also consistent with the established warning that unstructured cross-validation of temporally, spatially or hierarchically dependent ecological observations can understate prediction error (Roberts et al., 2017).

Second, the probability reference matters. A model conditioned on species, location and time may beat a species-pooled altitude-state marginal because it knows species identity, even if additional within-species context contributes little. An inferential statement about the value of context requires a comparator that fixes the lower-information content being claimed. Baselines are therefore a substantive part of the estimand, not a plotting choice.

Third, validating predictions against held-out birds does not automatically make the historical cross-validation gains suitable for a future model. Cross-fitting can score different birds under different fitted predictors. To assign a lower predictive bound to a future bird, calibration gains need to be computed under a common fixed predictor and comparator, using groups credibly exchangeable with the future target.

Conformal prediction provides established order-statistic tools for marginal coverage under exchangeability (Angelopoulos & Bates, 2023). Hierarchical conformal prediction already addresses dependence and prediction for observations from previously unseen groups (Dunn, Wasserman & Ramdas, 2023). It is not a new result that a lower calibration order statistic can cover a future score. Less automatic is the **entire ecological analysis chain**: defining the biological unit, creating a reference aligned to the scientific question, reproducing the fitted probability model, separating three outcome roles, preserving group identities across provider archives, and stopping when no eligible future sample exists.

Here we implement and verify that chain in ODSP. The motivating biological data are frozen public raptor telemetry, but the new future-group coverage experiments are entirely synthetic. We keep the archived biological conclusion separate from the method qualification and use independent-source metadata as a test of when new real-data inference must stop.

## 2 | Methods

### 2.1 Ecological-state target and individual-level gain

For individual \(j\), observation \(r\), and four-class altitude state \(A_{jr}\), let \(q_{\mathcal F}(A_{jr}\mid X_{jr},s_j)\) be the fitted model's probability for the realized state and \(b_{\mathcal F}(A_{jr}\mid s_j)\) its prespecified training-only reference probability. The individual-level gain is

\[
G_j=\frac{\sum_r w_{jr}[\log q_{\mathcal F}(A_{jr}\mid X_{jr},s_j)-\log b_{\mathcal F}(A_{jr}\mid s_j)]}{\sum_r w_{jr}},
\]

with positive, prespecified within-bird observation weights. \(G_j>0\) means greater average realized-state log likelihood for that animal, **relative to the chosen reference**. It does not estimate a causal effect.

For the original BOP random forest, the comparator was the **pooled training-fold marginal altitude-state distribution**. For the newer transparent categorical test learner, the comparator is instead the **training-only species marginal**. We keep these distinct and make no quantitative combination of their gains.

### 2.2 Rank lower limit for one future animal

Condition on upstream training information \(\mathcal F\) sufficient to fix a common predictor and comparator without using future response outcomes. For each predeclared target stratum, let \(G_1,\dots,G_n\) be one mean held-out gain for each calibration animal and \(G_{\rm new}\) one future gain. Assume that these \(n+1\) scalar scores are exchangeable conditional on \(\mathcal F\). For miscoverage \(\alpha\),

\[
k=\lfloor(n+1)\alpha\rfloor,\qquad
L_\alpha=
\begin{cases}
-\infty,&k=0,\\
G_{(k)},&k\ge 1,
\end{cases}
\]

where \(G_{(k)}\) is the \(k\)-th smallest calibration score. Exchangeability yields

\[
\Pr(G_{\rm new}\ge L_\alpha\mid\mathcal F)
\ge (n+1-k)/(n+1)\ge 1-\alpha.
\]

Ties are conservative for this non-strict event. The *meaningful* threshold for an animal with a positive gain requires \(L_\alpha>0\). Coverage of \(G_{\rm new}\ge L_\alpha\) itself does not guarantee \(G_{\rm new}>0\); neither establishes positive group gains for *every* animal or estimates a population mean.

At nominal 90%, \(n=8\) yields \(k=0\), a vacuous \(-\infty\) limit; \(n=9\) gives \(k=1\), and \(n=39\) gives \(k=4\). These are counts of **independently admitted calibration animals within one stratum**. At least one separate test animal is needed to inspect untouched validation. The detailed derivation, including ties and conditioning qualifications, is in [the inference note](../docs/bop_individual_gain_inference_theory_v1.md).

### 2.3 Executable training-to-forecast provenance

A fixed-model rank calculation is not by itself enough to show that probability vectors actually came from the declared fitted model. We therefore implement a strict managed learner that (i) fits a species×binary-context categorical model and species-marginal reference from **training rows only**, (ii) serializes deterministic artifacts and source checksums, (iii) reconstructs calibration and validation probability vectors from those exact artifacts without reading their state labels, and (iv) verifies model/source/forecast digests again before opening calibration and validation roles.

This exact model-generation guarantee holds for the declared categorical learner; it must **not** be generalized to the original externally trained BOP random forest without additional equivalent replay evidence.

Each calibration bird contributes one group mean log-score gain. Calibration produces the stratum-specific rank lower threshold; no validation outcome can update that threshold. The independent-group protocol rejects reused group identifiers, inconsistent state classes, altered model/reference bytes, malformed forecast rosters and partial outcome sets.

### 2.4 Canonical biological animal identity and sample eligibility

A prefixed software group identifier does not establish biological independence across studies. The source-only canonical identity gate requires an externally supplied mapping from each frozen group ID to one biological animal key, species stratum, source and study cluster. It checks exact training/calibration/validation rosters, duplicated canonical identities (including re-tagging under a different provider ID), and within-species rank feasibility before scoring any target response. Only aggregate counts and plan digests are exported.

An integrated *synthetic-only* execution route additionally reconciles the declared training-group species with the model's actual fitted training rows. It then replays both the model-to-forecast chain and identity/count gate before accepting calibration responses and before examining untouched validation responses.

Passing this gate does **not** certify the truth of the external identity crosswalk, the independence of biological study clusters or exchangeability of future animals. These remain scientific and provider-level obligations.

### 2.5 Three prespecified known-truth method studies

All three tests were frozen separately before their first simulation outputs; they are not interchangeable effect estimates.

**Experiment A — fixed predictor/rank.** In 128 artificial worlds, each of four strata contributed 20 training, 39 calibration and 80 validation groups. A single fixed predictor and training-only reference were scored at the animal level. Each of the two evaluation conditions therefore involved 40,960 independently generated validation groups. The negative control deliberately rotated future state labels by +2 modulo four.

**Experiment B — model-to-forecast replay.** In 64 artificial worlds, we required exact reconstruction of the categorical training model, training-only reference and both holdout probability rosters from source rows. Per stratum were 20 training, 39 calibration and 40 validation groups (10,240 validation groups per condition). The altered-label negative control again used a frozen model and calibrator.

**Experiment C — common input across source schemas.** In 24 artificial worlds, four strata had 20 source-style training, 39 target calibration and 30 target validation birds each, totaling 2,880 target animal scores per condition. A reduced, new species×binary mean-solar-clock learner was trained from source-style inputs and calibrated on target-source animals. The context variable was UTC hour plus longitude/15 categorized 06:00–18:00 vs the complement, **not astronomical daylight**. Target longitudes were simulated at 0.1° precision, and values near hard time-bin boundaries were disallowed. Source/target context amplitudes differed by design; calibration and validation groups remained drawn from the same target generator in the ordinary condition. In the negative control, only validation outcomes were shifted. This new, deliberately reduced categorical learner is **not the original BOP** random forest. The original BOP RF was never run on these inputs.

The post-result precision audit of Experiment C took **24 independent simulated training/model/calibration worlds**, not the 2,880 animals sharing 24 different fitted models, as the Monte Carlo replication units. We report approximate 95% t intervals for *retrained-world simulation means* separately from the finite-sample 90% individual gain prediction bound.

### 2.6 Prior biological BOP case and independent source admission

The historical biological case used checksum-fixed BOP_RODENT Zenodo v3 GPS records, four raw altitude-above-mean-sea-level classes, 60-minute within-individual thinning, four prospectively admitted raptor species, and individual-held-out random-forest scoring. That study's original training folds, predictor, bins, filters and conservative all-individual rule were never changed during the present method work.

Two **outcome-blind source eligibility audits** addressed whether a new empirical endpoint was possible. We compared public BOP v3 and 2026 reference-only identity files, separately from GPS outcomes. We also checked an independent Schaub et al. (2026) Dryad dataset's public version/field metadata and the historical RF's frozen input requirements. Neither exercise permitted opening raw Dryad altitude outcomes or claiming that publication-level counts were independent test animals.

## 3 | Results

### 3.1 The motivating biological model improved on average but not for every bird

The archived BOP source had 1,988,907 raw GPS records. Frozen admission and thinning retained 154,655 observations from 30 birds in four species: *Buteo buteo* (5), *Circus aeruginosus* (8), *C. cyaneus* (8) and *C. pygargus* (9). The primary RF log-score gain relative to the **pooled training-fold marginal** was positive in 27/30 birds; mean group gain was +0.570910 nats per event (descriptive), while three birds had non-positive gain. Multiclass Brier improvement was positive for **30/30** birds. Under the **frozen all-individual** decision rule, the result is \`empirical_state_prediction_mixed\`, not universally generalizing.

This observation motivates new-animal individual-level calibration; it does **not** supply a future-deployment conformal certificate. A historical descriptive 90%-rank pooled lower value of approximately −0.026803 remained negative, and same-species historical ranks were mostly vacuous at 90% because sample counts were too small.

### 3.2 Known-truth method coverage and deliberately broken exchangeability

| Method test | Independent target group scores per condition | Normal target-source coverage | Validation-only shifted coverage | Role |
|---|---:|---:|---:|---|
| Fixed-model independent-group lower bound (128 worlds) | 40,960 | 0.899438 | 0.068091 | Frozen predictor and group-rank construction |
| Source-to-artifact-to-forecast managed learner (64 worlds) | 10,240 | 0.891504 | 0.128711 | Executable training/forecast linkage |
| Reduced common-input target calibration (24 worlds) | 2,880 | 0.902431 | 0.262847 | Different training-source and target-source generators, exchangeability within target |

Every experiment passed its own predeclared method-level acceptance checks. The relative ordering of shifted coverage values is not a biological comparison, because generators and shift settings differ. No row-level pseudo-replication was used to qualify the rank thresholds.

For Experiment C, 2,599 of 2,880 artificial future animals met the lower bound under the normal target process, versus 757 of 2,880 under the intentionally shifted validation outcomes. An explicitly **post-result descriptive** audit of 24 independent worlds gave mean normal coverage 0.90243 with approximate 95% Monte Carlo interval [0.88614, 0.91872]. The validation-only shift yielded mean 0.26285 [0.23678, 0.28891]; the paired within-world difference was 0.63958 [0.61518, 0.66399]. Normal coverage ranged between **0.7917 and 0.9833 across individual fitted-model worlds**, so a marginal average of approximately 90% must not be presented as 90% conditional coverage for every particular fitted model.

### 3.3 Data-source eligibility stopped prospective external inference

In the newer BOP source-version metadata, 35 old reference animal IDs matched after one documented ID correction. The updated reference contained 45 unique IDs and ten new animal-ID candidates, with no more than six within one species. The 90% same-stratum rank design requires at least nine distinct new calibration animals and one further untouched new test animal. No taxon met that necessary-count gate; the original \`NO_WITHIN_STRATUM_NEW_GROUP_RANK_SUPPORT\` terminal remains closed.

The independent Schaub/Dryad public source lists 280 tagged individuals across six taxa (271 in its Data_1a GPS table, according to provider metadata). An apparent total of 217 animals from the four BOP species refers to the **whole published dataset** and is neither the actual Data_1a subset of those species nor a verified set of independent birds. The published Data_1a fields lack an external-temperature predictor required by the original BOP RF and use longitudes/latitudes rounded to 0.1°. Existing biological individual identity and study overlap were not verified. Accordingly the original RF remained \`ORIGINAL_RF_PREDICTOR_INCOMPATIBLE\`, and the source status remained \`NOT_ADMITTED\`.

The software's additional canonical-ID and training-stratum reconciliation tests passed on synthetic known truth. These verify correct gate behavior **when the supplied identities are correct**, not actual identity or source access in Dryad.

### 3.4 Source-only reality check: animal IDs are not transmitter IDs

We subsequently examined **two newly selected public source-reference files**, without opening their GPS response records, to see whether the necessary biological-group identity checks encountered a real data issue. The fixed-reference MH_WATERLAND v7 (DOI 10.5281/zenodo.10053583) and H_GRONINGEN v7 (DOI 10.5281/zenodo.10053658) animal/tag tables were downloaded directly from their published Zenodo deposits, and each file's MD5 was checked against the official manifest. Both matched.

The original pre-access contract specified incorrect aliases for the provider's animal/species columns, so this route properly stopped as **\`SOURCE_SCHEMA_HOLD\`**. Only a separately documented, explicitly **post-header** descriptive reconciliation using the observed \`animal-id\`, \`animal-taxon\` and \`tag-id\` columns generated subsequent counts. MH_WATERLAND had **seven distinct animal IDs but six distinct tag IDs**, including one tag reused between **two different animals**. H_GRONINGEN had four animal IDs and four tag IDs. These real source-reference observations confirm why **transmitter identity cannot be substituted for biological animal identity** in a new-individual validation protocol.

The source ID-string intersection was zero, but two disjoint textual ID sets do **not** prove that every tag history corresponds to a genuinely new biological animal. The nominal total of 11 candidate animals also spans **two independent study labels**, neither of which has the ten group identities required to assign nine calibration animals and one untouched validation animal within the same population. Pooling these sites would assume target-group score exchangeability across study populations without sufficient evidence. A study-blocked calibration/test allocation also provides no finite nominal-90% rank limit in either direction: treating the seven WATERLAND animals as calibration gives \(k=\lfloor 8(0.10)\rfloor=0\), and using the four GRONINGEN animals as calibration gives \(k=\lfloor 5(0.10)\rfloor=0\). This arithmetic requires no GPS outcome access. The source-only gate therefore remains **\`HOLD_POPULATION_AND_IDENTITY_EXCHANGEABILITY_UNVERIFIED\`**, not an external state-prediction result. MH_ANTWERPEN, previously opened by ODSP for an earlier empirical analysis, was explicitly excluded from the candidate untouched sample. Neither BOP nor these external sources were refitted or scored in this source audit.

The first official GitHub Actions run, provider MD5s, source SHA256s, and the permanent original-v1 / corrected-v2 evidence separation are preserved in \`BOP_TWO_MARSH_REFERENCE_ONLY_V1_V2_FIRST_RECEIPT.json\`. This addendum was written *after* inspecting the source reference CSV headers, rather than as a new pre-registered biological hypothesis test.



### 3.5 A source-population denominator can masquerade as an eligible-animal count

An explicitly **postpublication, no-outcome** source-admission audit of the Oppel et al. (2025) red-kite nesting-state data (Zenodo DOI 10.5281/zenodo.13736049) provides a second concrete identity/denominator failure mode. The paper reports 163 original German bird-seasons from 65 birds and **99 GPS-eligible seasons from 63 birds**. However, the exact checksum-verified deposited German individual-season table contains **159 different year IDs from 63 distinct bird-ID strings**. Under our separately frozen primary source GPS eligibility rule (original provider records, Germany bounds, predeclared breeding dates and strictly >800 valid seasonal GPS fixes), **99 year IDs correspond to only 49 bird-ID strings**, a result unchanged by independently checking all five source-selection stages. The difference between source metadata 159/63 and quality-eligible 99/49 arises at the **GPS-coverage threshold**, which removes 60 seasons and 14 bird strings. We did not inspect nesting labels or compute predictions in this audit.

The authors' original 29 August 2024 [archived full-analysis script](https://zenodo.org/records/13736049/files/NestTool_archived_full_analysis.r?download=1) reads the two deposited German CSVs directly before calling `data_prep()`. In its subsequent sample-size section, it contains an **unfiltered** `length(unique(GERseasondata$bird_id))` expression alongside a different, *filtered* calculation on the admitted `GER_data_input$summary$year_id`. The former produces **63** on the deposited source, matching the article's stated eligible-bird count. A dated [28 August 2024 NestTool source snapshot](https://github.com/Vogelwarte/NestTool/blob/8fdf3884b5f6079afdffdc5c563c9050766670a4/R/data_prep.R) also shows the source function's `number_of_fixes > minlocs` admission (not a count of independent animals). **This is a plausible unfiltered-denominator mechanism, not proof of the authors' reporting process or an identified publication error.** A separate official code-only source check verified that the archived ZIP's `R/data_prep.R` is **byte-identical** to the dated GitHub file (Git blob SHA1 `3fa42eddbfb852d5dbc29364281bffef8410563e`), and located the unfiltered count on **line 501** of the provider-MD5-verified archived analysis script (correcting the earlier approximate line 486). The **whole R package/runtime**, upstream 60-minute downsampling and article's original 163/65 roster remain unreconciled. A further prospectively fixed source-only audit of deposited German GPS timestamps found that **48.74% of 210,321 positive consecutive within-season gaps in the 99-season/49-bird-ID source cohort were shorter than 55 min**, with a median of 59.03 min and 67 of 99 seasons containing at least one such interval. The published GPS source is thus **not a strictly one-fix-per-hour stream**; neither this observation nor its thresholds recovers the authors' pre-archive filtering or validates the paper's 63-bird eligible count. The original full-file MD5s and first official Actions output digests are preserved in `BOP_RED_KITE_GER_GPS_CADENCE_V1_FIRST_RECEIPT.json`. No reproductive labels or model probabilities were accessed in this cadence audit. No reproductive responses or GPS rows were read in this separate code comparison.

Thus even when the **season total of 99 matches**, the independent group sample is not admitted as **63**. In this source-only analysis **49 remains a count of bird-ID strings**, not a certified canonical-animal set with exchangeable population membership. No target-source calibration, ecological predictive advantage or future-animal lower-bound claim follows. The frozen evidence and its explicit uncertainty are recorded in `research/BOP_RED_KITE_2024_PAPER_SOURCE_COUNT_AUDIT_V1.json` and `docs/bop_red_kite_2024_paper_source_count_audit_v1.md`. The original BOP mixed verdict remains unchanged.


### 3.6 Season-held-out prediction is not necessarily bird-held-out prediction

A separate historical-code and **aggregate-only mathematical** audit examined the 2024 NestTool training functions (Oppel et al., 2025; archived package DOI 10.5281/zenodo.13736049). Dated near-publication R sources for each of the three binary reproductive classifiers construct the training set by sampling `unique(...$year_id)`, not unique biological `bird_id`. Thus a bird followed in multiple years can contribute one season to training and another to internal testing. The paper reports **697 Swiss bird-seasons from 258 birds (up to seven seasons per bird)** and an internal split of **488 training / 209 test seasons**, approximately 70/30. A code-only first-source audit verified **byte-for-byte identity of all three trainer R files** between the official 2024 archived NestTool package and the frozen 28 August 2024 GitHub commit (original Actions run `44307730106`); no current-code substitution is needed for this split-unit claim.

Even without opening original individual identities, this provides a sharp **expectation-only** calculation. For a bird present in \(k\) seasons, the probability that at least one season enters both roles under a uniformly random 488-of-697 season split is

\[
P_{\mathrm{both}}(k)=1-\prod_{j=0}^{k-1}\frac{488-j}{697-j}-\prod_{j=0}^{k-1}\frac{209-j}{697-j}.
\]

Among all possible integer bird-season histograms with 258 birds, 697 season rows and \(1\leq k\leq7\), the expected number of birds represented in *both* roles is bounded sharply by **67.463–146.540**. The minimum is achieved with 184 one-season birds, one two-season bird and 73 seven-season birds; the maximum with 77 two-season and 181 three-season birds. Strict discrete concavity of \(P_{\mathrm{both}}(k)\) proves these extrema. These are **bounds on expectation over random season-row splits**, not a lower bound on the realized number of overlapped birds in the paper's unknown random split, and not a test of accuracy inflation.

This is precisely the estimand distinction motivating ODSP: season-level internal accuracy, previously unseen biological-bird accuracy, and transfer to a geographically different population require different samples and cannot be substituted for one another. The training code's potential within-bird overlap concerns the **Swiss internal** evaluation; it does **not** by itself invalidate the separately published Swiss-to-Germany external accuracy. The nesting-success model has a smaller conditional Swiss subset, so the 697-row numerical bounds do not apply to that response. Neither the realized original random split nor canonical animal identities, new models or outcome scores were inspected. The original code ZIP/source hashes and the sharp expectation bounds are pinned in `BOP_NESTTOOL_2024_YEARID_ANIMAL_OVERLAP_V1_FIRST_RECEIPT.json`. See `docs/bop_nesttool_2024_yearid_animal_overlap_v1.md` and `research/BOP_NESTTOOL_2024_YEARID_SPLIT_ANIMAL_OVERLAP_V1_CONTRACT.json`.


### 3.7 The Swiss source resolves the *expected* cross-year bird overlap without opening outcomes

To move beyond the unknown-histogram calculation above, we performed an independent, prospectively specified **source-only** audit of the published [Oppel et al. Zenodo v1 deposit](https://zenodo.org/records/13736049). After committing the original two-source checksum/field/eligibility contract and passing offline safety tests, we streamed the original Swiss GPS and used only the three initial individual-season identity/year fields, with no reading of HR, nesting or reproductive-success values. All source files matched the official full-file MD5 and the archived header fingerprints; no coordinates, timestamps or animal-ID strings were exported.

The deposited Swiss metadata contain **2,866 unique season IDs / 553 bird-ID strings**. A preregistered 2 × 3 × 2 comparison fixed Swiss geobounds (strictly >45°N and >4°E), breeding-season definitions (fixed 2023 UTC DOY 70–175 versus calendar March 11–June 24), three source timing rules (raw, unique UTC hour or rolling ≥3,600 s), and >800 versus ≥800 seasonal fixes. **Eight of twelve** fixed rules gave precisely **697 eligible season IDs / 258 bird-ID strings**, matching both article-reported numbers. The declared primary descriptive rule was fixed DOY × unique UTC hour × strictly >800; a rolling-3600-s rule instead retained only 620–623 seasons/246 bird IDs. Neither these comparisons nor matching sample totals proves the exact authors' undocumented 60-minute thinning method or their realized model-training row identities.

The original-source **697-season/258-bird-ID** histogram was **66 birds with one eligible season, 51 with two, 62 with three, 56 with four, 20 with five, two with six, and one with seven**. Thus **192 bird-ID strings recurred across multiple eligible years**. Conditional on this directly observed source histogram, the mathematically expected number of bird-ID strings represented in both train and test under a hypothetical uniformly random split of **488/209 distinct year IDs** is **121.992374**. This replaces the earlier 67.463–146.540 expectation envelope over all unknown feasible histograms by one **source-specific conditional expectation**. It is **not** the number that overlapped in the actual original random split, a bound on that realized overlap, or a measured change in model accuracy. Genuine biological identity equivalence across providers and original saved split assignments were not independently authenticated.

The published source-selection denominator also remains partly unreconciled: the paper describes **336 excluded seasons**, while the frozen Swiss source GPS screen had 967 in-season year IDs before the >800 threshold and excluded **270** from that stage. This does not change the reproduced eligible numerator; it rules out claiming that we have recovered every historical candidate-record decision. The smaller response-conditioned nest-success sample was not analysed, and the original Swiss-to-Germany geographical external-validation scores remain a separate inferential question. The complete original source counts-only artifact and scientific limits are pinned in `BOP_RED_KITE_SUI_GPS_YEAR_ID_ADMISSION_V1_FIRST_RECEIPT.json` and `docs/bop_red_kite_sui_gps_year_id_admission_v1.md`.


### 3.8 Biological-bird-heldout refitting preserves strong within-Swiss predictive performance

The original R model split by season rather than animal, but a season-level split alone does not determine whether the model's apparent predictive performance depends on repeated birds. To distinguish the two questions, we conducted a separate, *prospectively frozen* fixed-family refitting analysis using the dated 2024 public [`input_data_prepared.rds`](https://github.com/Vogelwarte/NestTool/blob/8fdf3884b5f6079afdffdc5c563c9050766670a4/input_data_prepared.rds). Before opening any reproductive values, the entire data-source Git blob, source-schema conditions, predictor set, outcome definitions, split construction and model hyperparameters were committed to `research/BOP_NESTTOOL_SWISS_BIRD_HELDOUT_REFIT_V1_CONTRACT.json`. An outcome-blind gate confirmed that the prepared feature table had **697 unique year IDs from 258 bird-ID strings**, precisely the full seven-bin multiplicity histogram reconstructed independently from the Zenodo Swiss GPS. It also contained the original 34 movement predictors and HR/nest response columns; nest-success values were not used.

Two source-only responses were refitted with the same predeclared 500-tree, five-candidate-feature scikit-learn random forest, across **eight frozen random seeds**. For each seed and response, the training set contained **488 season rows** and the test set **209**. The conventional random `year_id` split was compared with a *bird-ID-disjoint* exact-size subset-sum allocation, without outcome-guided group allocation or test-set model tuning. In the newly generated year-ID splits, **115–128 bird ID strings** occurred in both training and testing (mean **120.375**), whereas in every bird-ID split the overlap was exactly **zero**.

Despite this substantial contrast in repeated-bird exposure, the bird-heldout models retained high mean test accuracy: **96.23%** for ranging/home-range presence versus **96.83%** under season-heldout, and **94.02%** versus **94.74%** for nesting. Mean Brier scores were **0.030738 versus 0.029506** (ranging) and **0.048585 versus 0.046422** (nesting); corresponding mean log-score gains against each split's *training-only* prevalence baseline were **+0.573996 versus +0.546518** and **+0.516542 versus +0.523484**. Accordingly, under this **explicitly different fixed-family refit**, strong *within-source* accuracy remained even when test bird IDs were completely unseen during training. The simple assumption that the originally high Swiss internal accuracy must collapse under individual disjointness is not supported by this test.

This result **does not reconstruct the original 2024 tuned R `ranger` forests or original random split**, and the prepared GitHub RDS is an independent, dated source that is not byte-identical to the Zenodo input CSV. Source ID strings are not a cross-study canonical identity crosswalk. The eight splits reuse one Swiss study; small protocol differences are descriptive rather than independent-study effects, and distinct test birds prevent a strict same-test-row causal comparison of accuracy inflation. We therefore do not claim the original paper's accuracy estimates were inflated by a measured amount, assert finite-sample future-bird rank coverage, or promote this already-published population to a new external holdout. The Swiss→Germany external evaluation and the smaller conditional breeding-success sample were not rerun. The first original source-schema/model result, ZIP/JSON SHA256 receipts and offline-only regression are preserved in `BOP_NESTTOOL_SWISS_BIRD_HELDOUT_REFIT_V1_FIRST_RECEIPT.json` and `docs/bop_nesttool_swiss_birdheldout_refit_v1.md`.


### 3.9 Holding test animals constant: the other-year exposure comparison using R ranger

The previous Swiss seasonal versus bird-heldout refitting experiment (Section 3.8) used distinct test birds under the two split protocols, limiting interpretation of the small accuracy differences. We therefore designed a complementary **same-test, source-outcome-gated R ranger comparison** before reopening the original 2024 public prepared-feature RDS. The original cohort contains **51 bird-ID strings represented in exactly two seasons**. In each of 16 prospectively fixed source-only random splits, we selected 50 such strings and designated **one season from each** as the **same 50-season test set** for both models. From seasons belonging to other birds we retained **438 identical training records**; the control model added 50 unused records from unrelated birds, whereas the exposure model added **the other season of each of the 50 test birds**. Both models therefore used **488 training season rows**, shared **438/488 rows**, and evaluated the **exact same 50 test rows** within each split. The former had no bird-ID overlap across roles; the latter had 50 overlapping bird IDs but no duplicated year-ID row. The alternative season was not assumed to precede the test year chronologically.

Both models used R `ranger` probability forests, the original NestTool's algorithm family, but with **independently fixed** 500 trees, five candidate predictors, minimum terminal node size ten, the same original 34 movement features, training-only predictor imputation and equal per-pair random seeds, rather than the original publication's tuned forest. Every outcome-blind source-schema criterion was satisfied, and all fixed **16 × 2 binary responses × 2 exposures = 64 model fits** succeeded after a source-free R synthetic test. Only HR and nest outcomes were used; no breeding-success response, animal-level predictions or individual identifiers were exported.

Across the 16 paired test sets, home-range accuracy was **97.00% under both exposures**. Mean test Brier scores were **0.028638** (unrelated-bird control) and **0.029346** (same-bird-other-year exposure); mean test log loss was **0.121264** versus **0.143140**. The exposure-minus-control paired mean log-loss difference was **+0.021876**, and exposure produced greater log loss in **14 of 16** source resamples. For nesting, accuracy was **94.75% for both exposures**, Brier **0.031082 versus 0.031009**, log loss **0.100935 versus 0.100025**, and paired mean exposed-minus-control log loss **−0.000909** (higher in **7 of 16** resamples). ROC AUC remained high in both modes: HR **0.988142 versus 0.982926** and nesting **0.994950 versus 0.994688**, respectively. Thus, for these **identical test birds and seasons**, learning the test birds' other years was **not associated with a reproducible gain in classification accuracy**, and the probabilistic contrasts differed between the two biological targets.

Although the same-test construction removes a major test-set-composition discrepancy from the previous experiment, it **does not identify a pure causal contribution of individual familiarity**, because the 50 swapped training records also carry different environments, movement features and labels. Furthermore, the test subset was restricted to birds with two available years, the 16 random splits reuse the same single Swiss study, the source IDs have not been cross-provider canonically authenticated, and the original authors' 2024 hyperparameter tuning and exact random partition were not reproduced. Hence no independent-study significance claim, correction to the original paper's accuracy or untapped external new-bird lower-bound guarantee follows. The original source ZIP, all 32 within-seed paired summaries and the fixed BOP inference ceilings are retained in `BOP_SWISS_RANGER_PAIRED_OTHER_YEAR_EXPOSURE_V1_FIRST_RECEIPT.json` and `docs/bop_swiss_ranger_paired_other_year_exposure_v1.md`. This result is a narrowly positive **robustness of within-population predictive discrimination under strict same-test, bird-disjoint training**, rather than evidence that within-bird independence is irrelevant in general.

## 4 | Discussion

The principal result is a practical separation of four claims often compressed into one phrase, *generalization*: (i) within-dataset held-out predictive gain, (ii) a population-stratified finite-sample lower prediction bound on **one future animal's** score gain, (iii) reproducibility of the exact predictor-to-probability calculation, and (iv) real-world eligibility of the future animals and their source records. No one of these proves the others.

Our order-statistic interval is not a new conformal result. Unlike hierarchical conformal methods constructing prediction sets for *observations* inside a newly sampled group, our response target is a single aggregated **mean log-score difference for an entire independently held-out animal**. We do not claim hierarchical conditional coverage for each GPS event, or introduce a new generic conformal validity theorem. The methodological contribution is the integration of a biological group-level estimand, reference-aligned state probabilities, source-to-model execution checks, canonical identity and necessary-count admission, and explicit fail-closed exits when a real deployment claim cannot be identified. The historical BOP case illustrates the importance of the unit and the reference: most birds benefited over a pooled marginal, but the all-individual conclusion was mixed and that result did not become a future-bird coverage guarantee.

The simulations clarify a distinction relevant to ecological transfer. **A shift from training source to target source does not, by itself, invalidate the rank bound** if group gains in target calibration and future target validation remain exchangeable for the fixed predictor. Yet the trained model could have poor or negative mean target gain. Source shift therefore demands separate evaluation of (a) predictive gain itself and (b) coverage of the individual gain threshold. When calibration-to-future exchangeability was deliberately broken, coverage deteriorated, as expected from conformal validity theory.

Software provenance is similarly necessary but insufficient. Artifact hashes cannot establish that a tagged animal is new or that sampling designs are exchangeable. A cross-source ID crosswalk may be inaccurate, and multiple individuals in the same study cluster can be dependent. The system avoids reporting any real-data coverage or positive transfer while these questions remain unanswered.

### 4.1 Limits and next substantive test

There is currently **no untouched, verified, outcome-accessible independent raptor source** supporting a full prospective BOP-to-new-study empirical group calibration plus validation test. The two public source screens instead produced meaningful stopping results. The new reduced common-feature learner also lacks the original RF's temperature predictor and makes a different ecological estimand; it must never be represented as a validation of that historical model.

The strongest next scientific advance would be one prespecified external individual roster whose biological identities, four-state altitude target, covariate completeness and source version are independently audited **before outcomes are read**. This would permit a target population and exchangeability argument to be defended explicitly, even if resulting gains were non-positive. Additional synthetic success alone would not resolve that gap.

### 4.2 Relation to the separate ODSP N2 reference-alignment manuscript

ODSP's existing N2 failure-mode/reference-alignment manuscript asks how pooled reference distributions can create **apparent** predictive gains relative to claim-aligned baselines. The present draft should not duplicate that demonstration. It instead targets the *sampling/inference unit of a future biological individual* and an executable admission-to-validation protocol. The original BOP pooled comparator is a cautionary background example here, not new evidence that within-species context transfers.

A journal submission should be chosen only after deciding whether this is a **distinct contribution** from the reference-alignment paper and demonstrating a convincing independent real-data deployment, or alternatively packaging the future-animal rank protocol as a technical companion rather than a second full empirical paper.

## 5 | Reproducibility, ethics and evidence boundaries

- **Software:** <https://github.com/zuizui0223/odsp>, merged main through commit \`b2e77482ccbf55117e57f99c1f6514757ac3f040\`. All PRs #274–#280 are merged.
- **Primary empirical data source:** BOP_RODENT Zenodo v3, DOI <https://doi.org/10.5281/zenodo.10055071>. The deposited records were used for the original frozen analysis, not reopened for this manuscript draft.
- **Independent-source metadata candidate:** Schaub et al. 2026 Dryad, DOI <https://doi.org/10.5061/dryad.n8pk0p398>, **not** admitted for actual external validation.
- **Ground-truth method evidence:** the original independent test receipts for fixed-model group ranking, source→forecast replay and reduced common-input transport, including frozen GitHub Actions artifact SHA256 values, are linked in \`research/BOP_METHOD_PAPER_EVIDENCE_MATRIX_V1.json\`.
- **Post-result precision analysis:** \`research/BOP_COMMON_INPUT_V1_WORLD_COUNT_AUDIT_SOURCE.json\` contains 24 original, checksum-backed deidentified world-count records.
- **Identity/privacy:** the proposed cross-source canonical animal audit exports only aggregated biological group counts. No raw animal identities, GPS coordinate streams or new study outcomes were retrieved for this paper draft.
- **Scientific decision:** the original empirical BOP all-individual status remains \`mixed\`; the newer same-study BOP prospective count gate remains closed and independent Dryad status remains \`NOT_ADMITTED\`.

## Figure and table plan (not yet generated)

**Figure 1 — Sampling and evidence architecture.** One animal contributes many GPS fixes, but one gain calibration unit; diagram the separate training, calibration, untouched validation and canonical-animal ID stages; mark source-specific HOLD exits and reference alignment.

**Figure 2 — Frozen simulation evidence, not ecological effects.** Three independent known-truth scenario groups with nominal 0.90 horizontal line; ordinary vs deliberately shifted validation coverage as paired markers. A companion panel isolates 24 independent retrained-world Monte Carlo uncertainty from the one-animal rank guarantee.

**Figure 3 — Source admission and claim ceilings.** BOP v2026 maximum-six-within-species candidate count versus required nine-plus-one; original RF Dryad predictor mismatch; available metadata versus necessary external study/animal evidence.

**Table 1 — Comparator and evidence roles.** Historical pooled-fold RF versus new species-marginal categorical reference; first empirical terminal, synthetic method qualification, source-only admission, and unavailable real generalization.

## Literature (verified, methodological context)
- Dunn, R., Wasserman, L. & Ramdas, A. (2023). *Distribution-Free Prediction Sets for Two-Layer Hierarchical Models*. Journal of the American Statistical Association 118, 2491–2502. https://doi.org/10.1080/01621459.2022.2060112

- Gneiting, T. & Raftery, A. E. (2007). *Strictly proper scoring rules, prediction, and estimation*. Journal of the American Statistical Association 102, 359–378. https://doi.org/10.1198/016214506000001437
- Roberts, D. R. et al. (2017). *Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure*. Ecography 40, 913–929. https://doi.org/10.1111/ecog.02881

- Angelopoulos, A. N. & Bates, S. (2023). *Conformal Prediction: A Gentle Introduction*. Foundations and Trends in Machine Learning. https://doi.org/10.1561/2200000101
- Tibshirani, R. J., Barber, R. F., Candès, E. J. & Ramdas, A. (2019). *Conformal Prediction Under Covariate Shift*. Advances in Neural Information Processing Systems 32. https://proceedings.neurips.cc/paper_files/paper/2019/hash/8fb21ee7a2207526da55a679f0332de2-Abstract.html
- Barber, R. F., Candès, E. J., Ramdas, A. & Tibshirani, R. J. (2023). *Conformal prediction beyond exchangeability*. Annals of Statistics 51, 816–845. https://doi.org/10.1214/23-AOS2276
- Gibbs, I., Cherian, J. J. & Candès, E. J. (2025). *Conformal prediction with conditional guarantees*. Journal of the Royal Statistical Society: Series B 87, 1100–1126. https://doi.org/10.1093/jrsssb/qkaf008

**Submission-readiness label:** \`WORKING_DRAFT__NOT_FOR_SUBMISSION\`. Literature coverage is intentionally selective, author affiliations/correspondence are unassigned, and the scientific requirement for an independent external demonstration is not met. Do not use the draft as a final submission packet.
