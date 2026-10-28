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

An ecological model can represent a species' state as a distribution over discrete altitude strata, habitat categories or temporal states, rather than compressing every event to a single predicted value. The benefit of conditioning on additional predictors can be assessed with proper probability scoring. However, three logical leaps often separate an encouraging result from a defensible future-animal claim.

First, one bird may contribute thousands of autocorrelated GPS observations. A gain measured across those positions does not create thousands of independent demonstrations of generalization. The appropriate calibration unit for a new-bird claim is the **bird**, not the GPS fix.

Second, the probability reference matters. A model conditioned on species, location and time may beat a species-pooled altitude-state marginal because it knows species identity, even if additional within-species context contributes little. An inferential statement about the value of context requires a comparator that fixes the lower-information content being claimed. Baselines are therefore a substantive part of the estimand, not a plotting choice.

Third, validating predictions against held-out birds does not automatically make the historical cross-validation gains suitable for a future model. Cross-fitting can score different birds under different fitted predictors. To assign a lower predictive bound to a future bird, calibration gains need to be computed under a common fixed predictor and comparator, using groups credibly exchangeable with the future target.

Conformal prediction provides established order-statistic tools for marginal coverage under exchangeability (Angelopoulos & Bates, 2023). It is not a new result that a lower calibration order statistic can cover a future score. Less automatic is the **entire ecological analysis chain**: defining the biological unit, creating a reference aligned to the scientific question, reproducing the fitted probability model, separating three outcome roles, preserving group identities across provider archives, and stopping when no eligible future sample exists.

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

**Experiment C — common input across source schemas.** In 24 artificial worlds, four strata had 20 source-style training, 39 target calibration and 30 target validation birds each, totaling 2,880 target animal scores per condition. A reduced, new species×binary mean-solar-clock learner was trained from source-style inputs and calibrated on target-source animals. The context variable was UTC hour plus longitude/15 categorized 06:00–18:00 vs the complement, **not astronomical daylight**. Target longitudes were simulated at 0.1° precision, and values near hard time-bin boundaries were disallowed. Source/target context amplitudes differed by design; calibration and validation groups remained drawn from the same target generator in the ordinary condition. In the negative control, only validation outcomes were shifted. The original BOP RF was never run on these inputs.

The post-result precision audit of Experiment C took **24 independent simulated training/model/calibration worlds**, not the 2,880 animals sharing 24 different fitted models, as the Monte Carlo replication units. We report approximate 95% t intervals for *retrained-world simulation means* separately from the finite-sample 90% individual gain prediction bound.

### 2.6 Prior biological BOP case and independent source admission

The historical biological case used checksum-fixed BOP_RODENT Zenodo v3 GPS records, four raw altitude-above-mean-sea-level classes, 60-minute within-individual thinning, four prospectively admitted raptor species, and individual-held-out random-forest scoring. That study's original training folds, predictor, bins, filters and conservative all-individual rule were never changed during the present method work.

Two **outcome-blind source eligibility audits** addressed whether a new empirical endpoint was possible. We compared public BOP v3 and 2026 reference-only identity files, separately from GPS outcomes. We also checked an independent Schaub et al. (2026) Dryad dataset's public version/field metadata and the historical RF's frozen input requirements. Neither exercise permitted opening raw Dryad altitude outcomes or claiming that publication-level counts were independent test animals.

## 3 | Results

### 3.1 The motivating biological model improved on average but not for every bird

The archived BOP source had 1,988,907 raw GPS records. Frozen admission and thinning retained 154,655 observations from 30 birds in four species: *Buteo buteo* (5), *Circus aeruginosus* (8), *C. cyaneus* (8) and *C. pygargus* (9). The primary RF log-score gain relative to the **pooled training-fold marginal** was positive in 27/30 birds; mean group gain was +0.570910 nats per event (descriptive), while three birds had non-positive gain. Multiclass Brier improvement was positive for all 30. Under the **frozen all-individual** decision rule, the result is \`empirical_state_prediction_mixed\`, not universally generalizing.

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

## 4 | Discussion

The principal result is a practical separation of four claims often compressed into one phrase, *generalization*: (i) within-dataset held-out predictive gain, (ii) a population-stratified finite-sample lower prediction bound on **one future animal's** score gain, (iii) reproducibility of the exact predictor-to-probability calculation, and (iv) real-world eligibility of the future animals and their source records. No one of these proves the others.

Our order-statistic interval is not a new conformal result. The methodological contribution is the integration of a biological group-level estimand, reference-aligned state probabilities, source-to-model execution checks, canonical identity and necessary-count admission, and explicit fail-closed exits when a real deployment claim cannot be identified. The historical BOP case illustrates the importance of the unit and the reference: most birds benefited over a pooled marginal, but the all-individual conclusion was mixed and that result did not become a future-bird coverage guarantee.

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

- Angelopoulos, A. N. & Bates, S. (2023). *Conformal Prediction: A Gentle Introduction*. Foundations and Trends in Machine Learning. https://doi.org/10.1561/2200000101
- Tibshirani, R. J., Barber, R. F., Candès, E. J. & Ramdas, A. (2019). *Conformal Prediction Under Covariate Shift*. Advances in Neural Information Processing Systems 32. https://proceedings.neurips.cc/paper_files/paper/2019/hash/8fb21ee7a2207526da55a679f0332de2-Abstract.html
- Barber, R. F., Candès, E. J., Ramdas, A. & Tibshirani, R. J. (2023). *Conformal prediction beyond exchangeability*. Annals of Statistics 51, 816–845. https://doi.org/10.1214/23-AOS2276
- Gibbs, I., Cherian, J. J. & Candès, E. J. (2025). *Conformal prediction with conditional guarantees*. Journal of the Royal Statistical Society: Series B 87, 1100–1126. https://doi.org/10.1093/jrsssb/qkaf008

**Submission-readiness label:** \`WORKING_DRAFT__NOT_FOR_SUBMISSION\`. Literature coverage is intentionally selective, author affiliations/correspondence are unassigned, and the scientific requirement for an independent external demonstration is not met. Do not use the draft as a final submission packet.
