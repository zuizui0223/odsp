#!/usr/bin/env python3
"""Build the N2 reference-to-claim alignment manuscript from frozen result receipts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
STAGE1 = ROOT / "N2_STAGE1_FAILURE_MODE_RESULT_RECEIPT_V1.json"
STAGE2 = ROOT / "N2_STAGE2_REAL_DATA_RESULT_RECEIPT_V1.json"
CONTRACT = ROOT / "N2_MEE_REFERENCE_ALIGNMENT_MANUSCRIPT_V2_CONTRACT.json"
SUPERSESSION = ROOT / "N2_FAILURE_MODE_MANUSCRIPT_SUPERSESSION_RECEIPT_V2.json"


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _words(text: str) -> list[str]:
    return re.findall(r"\b[\w'-]+\b", text)


def _assert_sources() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    contract = _read(CONTRACT)
    stage1 = _read(STAGE1)
    stage2 = _read(STAGE2)
    supersession = _read(SUPERSESSION)

    if stage1["frozen_decision"]["full_claim_supported"] is not True:
        raise ValueError("Stage 1 frozen known-truth result is not supported")
    if stage2["fresh_palmer_penguins"]["decision"] != "fresh_empirical_reversal":
        raise ValueError("fresh Palmer Penguins reversal drifted")
    supported = stage2["scientific_interpretation"]["supported"]
    if not any("reference-to-claim alignment" in str(row) for row in supported):
        raise ValueError("Stage 2 no longer freezes reference-to-claim alignment")
    positioning = contract["positioning"]
    if positioning["reference_to_claim_alignment_paper"] is not True:
        raise ValueError("reference-alignment positioning is not frozen")
    if positioning["failure_mode_paper"] is not False:
        raise ValueError("contract drifted back to failure-mode positioning")
    if positioning["framework_paper"] is not False:
        raise ValueError("contract drifted back to framework positioning")
    if supersession["historical_failure_mode_v1_submission_authorized"] is not False:
        raise ValueError("historical failure-mode manuscript is still submission-authorized")
    return contract, stage1, stage2


def build_manuscript_text() -> str:
    contract, s1, s2 = _assert_sources()
    anchors = s1["confirmatory_anchors"]
    factorial = s1["factorial_descriptive_summary"]
    diagnostics = s1["metric_diagnostics_at_primary_null_anchors"]
    peng = s2["fresh_palmer_penguins"]
    bop = s2["bop_rodent"]
    control = s2["snapshot_serengeti_semantic_control"]

    a = anchors["A_explicit_layer_pooled_reference"]
    b = anchors["B_context_proxy_for_layer"]
    c = anchors["C_proxy_negative_control"]
    d = anchors["D_context_power_correlated"]
    e = anchors["E_context_power_uncorrelated"]
    f = anchors["F_high_information_bias_correlated"]
    g = anchors["G_high_information_bias_uncorrelated"]
    failure = factorial["failure_relevant_null_cells"]
    realistic = factorial["bop_realistic_layer_gain_cells"]

    naive = peng["naive_pooled_gain"]
    layer = peng["audit_layer_component"]
    context = peng["audit_context_gain"]
    total = peng["audit_total_gain"]
    buteo = bop["buteo_motivating_sentinel"]
    auc_a = diagnostics["A_explicit_layer_pooled_reference"]["group_cv_auc_positive_rate"]
    auc_b = diagnostics["B_context_proxy_for_layer"]["group_cv_auc_positive_rate"]
    acc_a = diagnostics["A_explicit_layer_pooled_reference"]["group_cv_accuracy_positive_rate"]
    acc_b = diagnostics["B_context_proxy_for_layer"]["group_cv_accuracy_positive_rate"]

    title = contract["working_title"]

    return f"""# {title}

**Article type:** Research Article  
**Target journal:** Methods in Ecology and Evolution  
**Draft:** N2 reference-to-claim alignment manuscript v2

## Abstract

Predictive skill is always defined relative to a reference model, yet ecological interpretations often name a narrower information source than the score contrast actually isolates. We propose **reference-to-claim alignment**: the lower-information reference should already contain every information layer excluded from the focal transfer claim. This turns held-out skill from a generic comparison into an interpretable predictive-information increment. We tested the principle with a preregistered known-truth experiment and a fresh real-data audit. At a layer effect calibrated to a multi-species tracking decomposition, the pooled-reference positive-declaration rate was {a['pooled_reference_false_positive_rate']:.3f} when layer identity entered explicitly and {b['pooled_reference_false_positive_rate']:.3f} when context acted as a proxy for omitted layer identity, although true within-layer context information was zero. The conditioned context declaration rate was {a['decomposed_context_false_positive_rate']:.3f} in both primary null mechanisms, while power was {d['decomposed_context_power']:.3f}–{e['decomposed_context_power']:.3f} when context truly carried information. A fresh Palmer Penguins analysis then separated two valid but different questions: morphology improved island prediction against a pooled reference (mean log-score gain {naive['mean_gain']:+.5f}), whereas morphology added negative incremental information after species was already represented ({context['mean_gain']:+.5f}). Snapshot Serengeti supplied the semantic boundary: because species identity itself was the claimed information, a species-blind pooled temporal reference was appropriate and all three held-out gains remained positive. Reference selection is therefore part of estimand definition, not a cosmetic benchmark choice. Aligning the reference with the scientific claim separates transferable predictive information without requiring a universal preference for pooled or conditioned baselines.

**Keywords:** conditional information; cross-validation; hierarchical data; log score; predictive evaluation; reference model; transferability

## 1. Introduction

Prediction has become a central language for ecological evidence. Held-out evaluation asks whether patterns learned from one part of an ecological system retain value in observations, individuals, sites or time periods that were not used for fitting. This is an important discipline because fitted association alone does not show that a model will work in the ecological units to which its conclusions are meant to generalize. Structured cross-validation has sharpened this point by showing that spatial, temporal, hierarchical and phylogenetic dependence must be respected in the split itself. If observations from effectively the same unit enter both training and validation, predictive performance can be badly overstated.

That literature establishes a principle about **where** prediction should be tested. A second question arises after prediction has genuinely generalized: **what information should receive credit for the improvement?** A model is not predictive in the abstract. Its skill is defined relative to another predictive distribution under a scoring rule. The lower-information distribution is often called a null, baseline or reference model, language that can make it sound like a technical convenience. Yet the reference is mathematically inside the score contrast. Change the reference and the predictive information increment changes.

This matters in hierarchical ecological data because rich predictors commonly combine multiple information sources. Species-distribution models combine species identity, environment, geography, dispersal history and sometimes biotic interactions. Movement models combine individual identity, habitat, time, behavioural state and memory. Community prediction can combine site identity, traits and taxonomic structure. A single held-out improvement from a rich model over a pooled marginal can therefore bundle several information sources that have different biological interpretations.

Suppose an outcome varies among species and also with environmental context. A full predictor uses both species identity and context. Comparing the full predictor with a pooled reference asks whether the **joint bundle** of species and context transfers. It does not isolate whether context adds information after species is already known. If the verbal claim is “context transfers beyond species identity”, then species belongs in the reference. Conversely, if the claim is “species identity transfers”, conditioning species away would remove the very information being tested. Both score contrasts can be scientifically valid, but they answer different questions.

This distinction is separate from ordinary leakage. An identity effect can generalize perfectly to held-out observations, and a context variable correlated with identity can be a stable proxy for that identity. Independent-group cross-validation can therefore validate the predictions while leaving the attribution of their skill unresolved. The split controls reuse and dependence; the reference controls the information semantics of the score difference.

We call the constructive rule **reference-to-claim alignment**. Before scoring, the analyst states the focal information and the information treated as already known. The lower-information reference is built from the already-known information. The richer predictor adds the focal block. The held-out score difference can then be interpreted as a realized predictive increment matched to the stated claim.

This framing builds on, but differs from, two established lines of work. Proper scoring rules provide coherent incentives and comparisons for predictive distributions, with the logarithmic score connected to entropy and information measures. Structured ecological cross-validation addresses the dependence structure of training and validation units. Forecast-evaluation work has also shown that baseline selection changes relative skill and model rankings. Reference-to-claim alignment adds a different criterion: beyond being fair, stable or difficult to beat, a reference must encode the information that the scientific claim treats as already known.

A post-outcome decomposition of a frozen multi-species raptor analysis first made the issue visible. For *Buteo buteo*, mean held-out gain over a pooled altitude distribution was {buteo['mean_total_gain']:+.5f} nats per event. Replacing the pooled distribution with the training-fold species distribution contributed {buteo['mean_species_component']:+.5f}, whereas the residual within-species context contribution was {buteo['mean_context_within_species_component']:+.5f}. This was not designed as confirmatory evidence. Its value was diagnostic: a positive total gain could coexist with a negative increment for the narrower information claim.

We therefore designed a study around the positive principle rather than around that single example. Stage 1 was frozen before execution and used known truth to ask whether the intended information increment could be recovered under explicit layer identity, proxy-layer correlation, negative controls and genuine context signal. Stage 2 was frozen after Stage 1 and before opening a fresh Palmer Penguins result. Penguins asked whether pooled morphology skill and species-conditioned morphology information could lead to different conclusions in public ecological data. Snapshot Serengeti supplied the semantic boundary in which species identity itself was the intended information, so pooling was the aligned choice.

Our goal is not to estimate the prevalence of comparator mismatch in published ecology, and it is not to introduce another general-purpose modelling framework. We ask whether reference-to-claim alignment identifies the intended predictive information under known truth, retains sensitivity when that information is real, discriminates between scientific claims in fresh data, and correctly leaves pooling in place when pooling matches the claim.

## 2. Methods

### 2.1 Reference-to-claim alignment

Let S(q) denote mean held-out log predictive probability under predictive distribution q. Let Z denote information treated as already known and X the focal information whose transfer is being tested. A claim that X adds predictive information beyond Z corresponds operationally to

G(X | Z) = S[q(Y | Z, X)] - S[q(Y | Z)].

A pooled comparison instead evaluates

G(Z, X) = S[q(Y | Z, X)] - S[q(Y)].

The two gains differ because they have different lower-information references. The first isolates the increment associated with adding X to Z. The second asks about the joint value of the combined information bundle relative to pooling.

For nested references scored on exactly the same held-out observations, the finite-sample score accounting is algebraically exact:

S(full) - S(pool)
  = [S(layer) - S(pool)]
  + [S(full) - S(layer)].

We refer to these as total, layer and context increments. The decomposition does not require a causal interpretation. It assigns realized held-out score contributions to nested information contrasts. The additive identity is elementary algebra rather than a new theorem; the methodological contribution is to use the information content of the reference prospectively to define which ecological claim a held-out score increment can support.

With oracle conditional distributions under log score, expected score differences connect naturally to conditional information. Our fitted ecological models are not assumed to be oracle distributions, so the manuscript uses the more limited phrase **realized held-out predictive information increment**. This keeps the interpretation predictive and avoids turning a score difference into a causal quantity.

In other words, the comparator defines the predictive information increment being measured. Reference-to-claim alignment therefore proceeds from the scientific sentence, not from a universal ranking of baselines. If species identity is already assumed and context is focal, the reference should know species. If species identity itself is focal, the reference should not know species.

### 2.2 Stage 1: preregistered known-truth identification and power experiment

The Stage-1 contract was merged before any simulation result was generated and was executed once. Binary outcomes followed a logistic data-generating process with an intercept, a layer effect and a within-layer context effect. The factorial design varied layer effect, true context effect, number of independent groups, observations per group, number of layers, layer-context correlation and whether layer identity entered the learner.

The design included 864 structurally estimable factorial cells. Primary validation used five-fold independent-group cross-validation. Random-row cross-validation, accuracy and AUC were diagnostics rather than primary evidence. The main decision quantity was the equal-weight mean gain across independent groups with the predeclared population interval.

The known-truth experiment contained three null identification controls. In the **explicit-layer** control, the learner could use layer identity but true within-layer context information was zero. A pooled reference lacked the layer, whereas the aligned context reference contained it. In the **proxy-layer** control, the original learner omitted layer identity but context correlated with layer, allowing context to recover identity signal despite zero within-layer context truth. A prespecified layer-aware audit then asked whether context still added information beyond the layer. In the **negative control**, layer was omitted and context was uncorrelated with it.

The reference-alignment predictions were directional and falsifiable. Pooled gain could be positive in the explicit and proxy cases because those contrasts legitimately included transferable layer information. The aligned context increment should remain null because context truth was zero. Both contrasts should remain null in the negative control. Positive-context controls separately required the aligned increment to detect real context information with high power and low bias.

The layer effect used for the main anchors was calibrated to the motivating BOP decomposition. Its deterministic oracle layer gain was {s1['bop_reality_check']['observed_oracle_layer_gain_nats']:.6f} nats, inside the predeclared 0.20–0.35 nats window.

### 2.3 Population uncertainty and small-cluster policy

Independent biological groups received equal weight. When no higher-level dependence cluster was declared and at least 10 independent groups were available, population mean intervals used the frozen group-bootstrap rule. During development, a separate issue was identified for real datasets with very few higher-level clusters: percentile cluster bootstrap can be anti-conservative because its support becomes highly discrete.

Before the fresh Stage-2 result was opened, subsequent real-data summaries were prospectively corrected. With fewer than 10 declared dependence clusters, mean uncertainty uses a CR1 cluster-robust standard error with a Student t critical value on G-1 degrees of freedom. Positive-fraction Wilson intervals with few clusters are labelled descriptive rather than treated as cluster-robust prevalence intervals.

This correction matters for interpretation but does not change the Stage-1 result. It also does not create evidence about a broad ecological superpopulation from a handful of clusters.

### 2.4 Stage 2: preregistered real-data sign discrimination

Stage 2 contained two systems eligible for the comparator audit and one semantic boundary control.

**BOP_RODENT** was read only. No model was refitted and raw tracking data were not re-accessed. We used the frozen pooled-to-species-to-context decomposition and the corrected four-species population uncertainty. The *B. buteo* decomposition was predeclared as a motivating sentinel and excluded from the system-level reversal denominator.

**Palmer Penguins** was the only fresh Stage-2 result. The source table was pinned to the upstream commit recorded in the frozen contract. We retained {peng['prepared_row_count']} complete observations from three species across three collection years. The naive learner was a random forest predicting island from four morphology measurements and was scored against the pooled training island marginal. The claim-aligned audit learner used species identity plus the same morphology measurements and was scored against the species-conditioned training island distribution.

The two questions are intentionally different. The pooled contrast asks whether morphology predicts island better than ignoring species and morphology. The aligned contrast asks whether morphology adds island information after species is already known. Collection year was the held-out fold and the dependence cluster. With three collection years, the mean-gain intervals use CR1 standard errors and t(2).

Stage 2 reported point sign reversal, inferential downgrade and strong attenuation. These descriptors were frozen before the Penguins result was opened. The tiny two-system denominator is descriptive and is not used to estimate prevalence in ecological studies.

### 2.5 Snapshot Serengeti as a semantic boundary control

Snapshot Serengeti was not reopened as a candidate failure system. Its frozen scientific claim was whether species identity predicts camera-detected time. Species identity itself was the claimed information. A species-blind pooled temporal distribution is therefore the claim-aligned lower-information reference.

This control distinguishes the proposed principle from a blanket preference for conditioning. It is not a rule to condition every reference. The correct reference is the one whose information content matches what the claim treats as already known.

### 2.6 Implementation

ODSP supplied score accounting, frozen contracts and one-shot execution machinery. It is supporting infrastructure rather than the scientific novelty of this paper. The present manuscript does not add a certification family, a new empirical endpoint or a new inferential route. Stage 1 and the fresh Penguins analysis are read from frozen result receipts.

## 3. Results

### 3.1 Claim-aligned increments recovered the intended information source under known truth

The Stage-1 identification controls matched the preregistered predictions. In the explicit-layer null anchor, the pooled-reference positive-declaration rate was {a['pooled_reference_false_positive_rate']:.3f}, with Wilson 95% lower bound {a['pooled_reference_false_positive_wilson_95_lower']:.3f}. In the correlated proxy-layer null anchor, the pooled-reference positive-declaration rate was also {b['pooled_reference_false_positive_rate']:.3f}, with the same lower bound. True within-layer context information was zero in both worlds.

Once the reference represented layer identity, the conditioned context declaration rate was {a['decomposed_context_false_positive_rate']:.3f} in the explicit-layer anchor and {b['decomposed_context_false_positive_rate']:.3f} in the proxy-layer anchor. The negative control localized the distinction: with layer omitted and context uncorrelated with it, the pooled positive-declaration rate was {c['pooled_reference_false_positive_rate']:.3f} and the conditioned rate was {c['decomposed_context_false_positive_rate']:.3f}.

These results separate the information contrast rather than simply distinguishing a good and a bad predictive model. In the explicit-layer world, the rich predictor genuinely carries transferable layer information. The pooled gain is therefore not numerically wrong; it answers the broader joint-information question. The aligned context gain answers the narrower context-beyond-layer question and correctly remains null.

### 3.2 The aligned increment retained power for genuine context

Reference alignment did not control null attribution by erasing positive signal. In the positive-context anchor with correlated layer and context, power was {d['decomposed_context_power']:.3f}. Without layer-context correlation, power was {e['decomposed_context_power']:.3f}. Mean gains closely tracked oracle context information.

At the high-information anchors, absolute mean bias was {f['absolute_mean_bias_nats']:.8f} nats in the correlated world and {g['absolute_mean_bias_nats']:.8f} nats in the uncorrelated world. Across all {factorial['positive_context_cells']['cell_count']} positive-context factorial cells, the mean absolute context-gain bias was {factorial['positive_context_cells']['mean_absolute_decomposed_context_bias_nats']:.6f} nats.

The constructive criterion therefore passed both sides of the identification problem: it withheld credit when the focal context carried no additional information, and it recovered signal when context truly contributed beyond the layer.

### 3.3 The distinction persisted across a broad and empirically realistic parameter region

Among {failure['cell_count']} null-context cells in which either explicit layer information or a correlated proxy could enter the pooled contrast, the mean pooled positive-declaration rate was {failure['mean_pooled_reference_positive_rate']:.3f}, the median was {failure['median_pooled_reference_positive_rate']:.3f}, and {failure['fraction_of_cells_with_positive_rate_gt_0_5']:.1%} of cells exceeded a declaration rate of 0.5. The aligned context rate averaged only {failure['mean_decomposed_context_positive_rate']:.5f}, with maximum {failure['max_decomposed_context_positive_rate']:.5f}.

The result was not restricted to extreme layer effects. Within the preregistered BOP-realistic oracle layer-gain window, {realistic['failure_relevant_cell_count']} relevant cells had mean pooled positive-declaration rate {realistic['mean_pooled_reference_positive_rate']:.3f}; {realistic['fraction_of_cells_with_positive_rate_gt_0_5']:.1%} of cells exceeded 0.5. The corresponding mean aligned-context declaration rate was {realistic['mean_decomposed_context_positive_rate']:.6f}. When context did not proxy the omitted layer, the same realistic regime had a pooled positive rate of only {realistic['uncorrelated_layer_omitted_negative_control_mean_pooled_positive_rate']:.6f}.

This factorial pattern matters because it shows that the principle is not supported only by a hand-picked sign reversal. The difference between pooled and aligned contrasts follows the information structure of the data-generating process.

### 3.4 Metric choice and reference semantics were not interchangeable

The diagnostic metrics responded differently to the same layer structure. At the explicit-layer null anchor, groupwise AUC had a positive-declaration rate of {auc_a:.3f}; at the proxy-layer null anchor it was {auc_b:.3f}. In contrast, groupwise accuracy declared positive improvement at rates {acc_a:.3f} and {acc_b:.3f}, while log-score gain was positive in every replicate.

This does not identify AUC as a preferred solution. The simulated layer signal is largely intercept-like: it can strongly affect calibration and decision thresholds without substantially changing within-group ranking. Groupwise AUC was therefore comparatively insensitive to this exact signal.

The broader point is that metric choice and reference semantics solve different problems. A metric determines what aspect of predictive performance is rewarded. A reference determines which information increment receives credit. A ranking metric that happens to ignore one kind of layer effect cannot establish that a verbal context claim has been isolated.

### 3.5 Palmer Penguins separated two valid scientific questions with opposite signs

The fresh Palmer Penguins result was the empirical centerpiece. The morphology-only predictor scored against a pooled island marginal had mean held-out log-score gain {naive['mean_gain']:+.5f}, with CR1+t(2) 95% interval [{naive['mean_gain_lower']:+.5f}, {naive['mean_gain_upper']:+.5f}]. Thus morphology carried substantial predictive information about island relative to pooling.

Species identity alone carried an even larger pooled-reference component: mean gain {layer['mean_gain']:+.5f}, interval [{layer['mean_gain_lower']:+.5f}, {layer['mean_gain_upper']:+.5f}]. Once species identity was represented in the reference, the incremental morphology contribution reversed sign. The mean species-conditioned morphology gain was {context['mean_gain']:+.5f}, interval [{context['mean_gain_lower']:+.5f}, {context['mean_gain_upper']:+.5f}], and its frozen status was nonpositive.

The full species-plus-morphology audit model remained strongly predictive relative to pooling, with mean gain {total['mean_gain']:+.5f}. This combination is exactly what reference-to-claim alignment predicts: the full prediction can be useful while the narrower focal increment is absent or negative.

All three preregistered Stage-2 descriptors fired: point sign reversal, inferential downgrade and strong attenuation. The scientific conclusion is not that morphology “fails”. It is that “morphology predicts island beyond pooling” and “morphology adds island information beyond species” are different empirical statements.

Only three collection years were available as dependence clusters. The interval therefore has df=2 and should not be read as precise evidence about an unlimited population of future years. The limitation constrains generalization of effect size, but it does not change the fact that the two declared contrasts on the same dataset have opposite observed signs.

### 3.6 The BOP decomposition motivates the problem but does not carry the main inference

The BOP population summary remained uncertain after the small-cluster correction. The equal-individual total mean gain was {bop['population_v2_total_mean_gain']:+.5f}, but the four-species uncertainty interval crossed zero and the status remained {bop['population_v2_total_status']}. The within-species context population mean was {bop['population_v2_context_mean_gain']:+.5f} and likewise uncertain.

The *B. buteo* sentinel remains useful as a descriptive decomposition. Its pooled total gain {buteo['mean_total_gain']:+.5f} equals a species component of {buteo['mean_species_component']:+.5f} plus a within-species context component of {buteo['mean_context_within_species_component']:+.5f}. This makes the estimand issue intuitive but is not counted as an inferential system-level reversal.

### 3.7 Snapshot Serengeti showed when pooling is the aligned reference

Snapshot Serengeti defined the semantic boundary. Its target question was whether species identity itself generalized in detected-time distributions. The lower-information comparator should therefore omit species. Conditioning on species would answer a different question.

The three frozen held-out gains were {control['heldout_gains'][0]:+.5f}, {control['heldout_gains'][1]:+.5f} and {control['heldout_gains'][2]:+.5f}, all positive. Thus pooling is not intrinsically weak or invalid. It is appropriate when its missing information is precisely the information being tested.

This boundary is essential because it keeps the method claim dependent. Reference-to-claim alignment is not a rule to condition every reference; it is a rule to make the reference's information content explicit.

## 4. Discussion

### 4.1 Predictive validation and predictive attribution are different design problems

Our results support a constructive distinction between two stages of predictive inference. Validation design asks whether prediction generalizes to the intended units. Reference design asks which information source the held-out gain represents. These stages can fail independently. A random-row split can exaggerate generalization even when the reference is perfectly aligned, and an independent-group split can validate a broader information bundle than the verbal claim names.

This distinction complements the ecological cross-validation literature rather than replacing it. Roberts and colleagues emphasized that temporal, spatial, hierarchical and phylogenetic structure should shape resampling. Hijmans showed that spatial sorting can distort species-distribution model validation. Those lessons remain intact. Stage 1 deliberately used independent-group cross-validation and still separated pooled and aligned conclusions, showing that the present issue survives after the unit of validation is made defensible.

The distinction also clarifies why the proxy-layer case matters. If context is correlated with species, region or another layer, a context-only learner may generalize because context encodes stable information about that layer. Calling the resulting prediction “leakage” would be inaccurate: the signal can be entirely available at prediction time. What needs clarification is the scientific label assigned to the score gain.

### 4.2 A reference model is part of the estimand

Relative skill is sometimes discussed as though the scientific object were the complex model and the reference merely set a difficulty threshold. For an additive score difference, however, the lower-information distribution is part of the estimand. The same full prediction produces different increments against a pooled, species-aware or site-aware reference.

This gives reference selection a stronger role than baseline fairness. Recent forecasting work has demonstrated that different baselines can alter apparent relative performance and rankings. Reference-to-claim alignment asks a complementary question: **what information must a baseline already contain before the remaining skill can be credited to the focal information source?**

A well-calibrated baseline can still be scientifically under-informed for a narrow claim. Conversely, an intentionally simple pooled baseline can be exactly right if the omitted identity information is the target of interest. There is therefore no universal ordering from “weak” to “strong” reference that solves the problem.

### 4.3 Proper scores provide the accounting language, not the biological hierarchy

Strictly proper scoring rules are useful because they reward honest predictive distributions and allow held-out distributions to be compared on a common scale. Under logarithmic score, oracle expected score differences connect to entropy, Kullback-Leibler divergence and information. That mathematical connection motivates the language of predictive information.

The ecological analysis remains finite-sample and model dependent. We therefore avoid claiming that a fitted score increment equals an intrinsic causal information quantity. The phrase “realized held-out predictive information” keeps the scope clear. What is exact is the arithmetic of nested scores on the same held-out rows.

The biological hierarchy is not supplied by the score. Analysts must decide what information is focal and what is already assumed. That decision can be contested scientifically, and sometimes more than one claim is legitimate. In such cases the solution is not to hide the ambiguity but to report multiple declared contrasts.

### 4.4 Known truth establishes identification rather than a catalogue of failure

The known-truth experiment is strongest when interpreted as an identification study. The explicit-layer and proxy-layer worlds represent two distinct ways a pooled contrast can contain layer information. The negative control removes those routes. The true-context anchors ask whether the aligned contrast still detects the information it is meant to measure.

All parts of that pattern were observed. Pooled declarations reached 1.000 in both primary null mechanisms at the BOP-scale layer effect, while aligned context declarations fell to 0.000. The negative control remained near zero. Genuine context power was 0.959–1.000, and high-information bias was tiny.

That combination matters more than the existence of a large false-declaration rate by itself. It shows that changing the reference targets the intended information contrast rather than merely making significance harder to achieve.

### 4.5 Palmer Penguins demonstrates a change of question, not a broken model

The fresh Penguins reversal makes the principle tangible because neither of its two questions is nonsensical. “Does morphology predict island better than pooling?” is a legitimate forecasting question, and the answer is strongly positive. “Does morphology add island information beyond species?” is a legitimate incremental-information question, and the observed answer is negative.

The same dataset therefore supports two different statements because the statements refer to different information sets. This is the positive methodological lesson: predictive analyses become more interpretable when the reference is chosen from the scientific sentence rather than inherited automatically from a default null.

The three-year cluster structure remains a limitation. CR1+t(2) is preferable to an asymptotic interval, but df=2 leaves little information about variation among years. We therefore emphasize the sign discrimination between declared contrasts rather than a precise general-population effect size.

### 4.6 Snapshot Serengeti prevents overcorrection

A methodological rule is more credible if it specifies when not to apply a correction. Snapshot Serengeti does that here. Because species identity itself was the claimed information, a species-blind temporal reference is aligned with the scientific question. A species-conditioned reference would erase the estimand.

This is why the paper should not be summarized as “condition on the hierarchy”. The correct summary is **align the reference to the claim**. Conditioning is one possible consequence, not the principle itself.

### 4.7 A practical workflow

The method can be implemented as a short pre-analysis checklist.

1. **Write the claim as an increment.** State the outcome Y, the focal information X, and the information Z treated as already known: “X adds predictive information about Y beyond Z in held-out units.”
2. **Choose the validation unit independently.** Decide whether held-out units are observations, individuals, sites, years, populations or species based on the intended generalization.
3. **Construct the reference from Z.** The lower-information predictor must use exactly the information that the claim assumes before X is added.
4. **Construct the richer predictor from Z + X.** Training and preprocessing must follow the same fold discipline as the reference.
5. **Score both on the same held-out rows.** Use a proper scoring rule when predictive distributions are available.
6. **Report adjacent and total increments when nested.** A large total gain may coexist with a null or negative later increment; both quantities remain useful if labelled correctly.
7. **Declare multiple contrasts when multiple questions matter.** Do not choose the reference after seeing which contrast is more favorable.
8. **Keep causal language separate.** A held-out predictive increment is not an intervention effect.

This workflow is intentionally model agnostic. A reference can be an empirical marginal, generalized linear model, random forest, Bayesian model or another predictive distribution. The important object is the information set available to it.

### 4.8 Implications for ecological modelling

Ecological models increasingly combine data layers that historically lived in separate analyses. Species-distribution models may incorporate traits, dispersal, spatial history and interactions. Movement models may use behavioural state, environmental context and individual identity. Biodiversity forecasts may combine taxonomic identity, site history and remotely sensed context.

As these models become richer, total predictive skill becomes less informative about any one source. Reference-to-claim alignment provides a way to retain rich models while making narrow claims. A paper can report both the total improvement of a comprehensive predictor and the incremental contribution of a focal layer beyond a declared baseline of already-known information.

The principle is also useful when a factor is not scientifically interesting but is strongly predictive. Species identity, site identity or season may be included to improve calibration. If the paper's claim concerns another variable, those nuisance-but-informative factors belong in the reference. If the factor itself is the hypothesis, it belongs outside the reference.

### 4.9 Limits and next questions

This study establishes identification and empirical plausibility, not literature prevalence. Stage 2 contains one fresh sign reversal, one descriptive motivating decomposition and one semantic boundary control. We therefore do not estimate how common comparator mismatch is in published ecology.

The BOP population result has only four species clusters and remains uncertain. Penguins has only three year clusters. These small-cluster structures restrict superpopulation inference.

Reference-to-claim alignment does not identify biological causality. A positive increment means that the focal information improves held-out predictive distributions beyond the declared reference under the fitted procedure. It does not show that manipulating the focal variable would change the ecological outcome.

Finally, the information hierarchy may itself be scientifically ambiguous. If several blocks have no defensible order, a future analysis can report multiple prespecified contrasts or a complete information lattice. That extension is separate from the present paper. The core principle is prior to any lattice: a score difference has meaning only relative to the information already present in its reference.

### 4.10 Conclusion

Prediction is inherently comparative. The reference determines not only how hard the benchmark is to beat, but also which predictive information increment the comparison measures.

The known-truth experiment shows that claim-aligned increments recover the intended information source while preserving power for genuine context. Palmer Penguins shows that two legitimate references can yield opposite signs because they answer different scientific questions. Snapshot Serengeti shows that pooling remains correct when identity itself is the claim.

Reference-to-claim alignment therefore offers a practical route from predictive skill to interpretable information transfer: **state what information is already assumed, put that information in the reference, and assign the remaining held-out score gain only to the information that was actually added.**

## 5. Data and code boundary

All empirical data were publicly archived by their original providers. The Palmer Penguins source was pinned to the upstream commit declared before the fresh Stage-2 result. BOP and Snapshot Serengeti were read only through frozen analysis artifacts or receipts. Stage-1 known-truth and Stage-2 fresh execution were each run once after their contracts were merged.

The software implementation, frozen contracts, result receipts and manuscript builder accompany the study. Historical method-development and reproducibility-hardening work remains repository history and is not presented as scientific evidence for this manuscript.

## 6. References cited for methodological positioning

Gneiting, T. & Raftery, A.E. (2007). Strictly proper scoring rules, prediction, and estimation. Journal of the American Statistical Association, 102, 359–378.

Hijmans, R.J. (2012). Cross-validation of species distribution models: removing spatial sorting bias and calibration with a null model. Ecology, 93, 679–688.

Roberts, D.R. et al. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. Ecography, 40, 913–929.

Stapper, M. & Funk, S. (2025). Mind the Baseline: The Hidden Impact of Reference Model Selection on Forecast Assessment. medRxiv preprint. doi:10.1101/2025.08.01.25332807.

Wesselkamp, M. et al. (2025). The ecological forecast limit revisited: Potential, absolute and relative system predictability. Methods in Ecology and Evolution.
"""


def build(output: Path, manifest_path: Path | None = None) -> dict[str, object]:
    contract, _, _ = _assert_sources()
    text = build_manuscript_text()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")

    abstract = text.split("## Abstract", 1)[1].split("**Keywords:**", 1)[0]
    abstract_words = len(_words(abstract))
    word_count = len(_words(text))
    minimum_words = int(contract["manuscript_quality"]["target_main_text_word_range"][0])
    maximum_words = int(contract["manuscript_quality"]["target_main_text_word_range"][1])

    manifest = {
        "schema_version": 2,
        "role": "n2_mee_reference_alignment_manuscript_v2",
        "contract_id": contract["contract_id"],
        "word_count": word_count,
        "target_word_range": [minimum_words, maximum_words],
        "abstract_word_count": abstract_words,
        "abstract_ceiling_words": int(contract["abstract"]["maximum_words"]),
        "abstract_within_ceiling": abstract_words <= int(contract["abstract"]["maximum_words"]),
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "reference_alignment_positioning": True,
        "failure_mode_primary_positioning": False,
        "framework_paper_positioning": False,
        "stage1_result_modified": False,
        "stage2_result_modified": False,
        "new_inference_added_by_manuscript_builder": False,
        "output": output.name,
    }

    if word_count < minimum_words:
        raise ValueError(
            f"manuscript below frozen minimum length: {word_count} < {minimum_words}"
        )
    if word_count > maximum_words:
        raise ValueError(
            f"manuscript above frozen maximum length: {word_count} > {maximum_words}"
        )
    if not manifest["abstract_within_ceiling"]:
        raise ValueError(
            f"abstract exceeds frozen ceiling: {abstract_words} > "
            f"{contract['abstract']['maximum_words']}"
        )

    if manifest_path is not None:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "build/n2_reference_alignment_v2/"
            "N2_MEE_REFERENCE_ALIGNMENT_MANUSCRIPT_DRAFT_v2.md"
        ),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(
            "build/n2_reference_alignment_v2/"
            "N2_MEE_REFERENCE_ALIGNMENT_MANUSCRIPT_DRAFT_v2.manifest.json"
        ),
    )
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.manifest), sort_keys=True))


if __name__ == "__main__":
    main()
