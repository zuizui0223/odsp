#!/usr/bin/env python3
"""Build the first N2 failure-mode manuscript draft from frozen result receipts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
STAGE1 = ROOT / "N2_STAGE1_FAILURE_MODE_RESULT_RECEIPT_V1.json"
STAGE2 = ROOT / "N2_STAGE2_REAL_DATA_RESULT_RECEIPT_V1.json"
CONTRACT = ROOT / "N2_MEE_FAILURE_MODE_MANUSCRIPT_V1_CONTRACT.json"


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

    if stage1["frozen_decision"]["full_claim_supported"] is not True:
        raise ValueError("Stage 1 full claim is not frozen as supported")
    if stage2["fresh_palmer_penguins"]["decision"] != "fresh_empirical_reversal":
        raise ValueError("fresh Palmer Penguins reversal drifted")
    if stage2["paper_position_after_stage2"]["failure_mode_paper_positioning_supported"] is not True:
        raise ValueError("Stage 2 does not support frozen failure-mode positioning")
    if contract["positioning"]["framework_paper"] is not False:
        raise ValueError("manuscript contract drifted back to framework positioning")
    return contract, stage1, stage2


def build_manuscript_text() -> str:
    contract, s1, s2 = _assert_sources()
    anchors = s1["confirmatory_anchors"]
    factorial = s1["factorial_descriptive_summary"]
    peng = s2["fresh_palmer_penguins"]
    bop = s2["bop_rodent"]
    control = s2["snapshot_serengeti_semantic_control"]

    a = anchors["A_explicit_layer_pooled_reference"]
    b = anchors["B_context_proxy_for_layer"]
    c = anchors["C_proxy_negative_control"]
    d = anchors["D_context_power_correlated"]
    e = anchors["E_context_power_uncorrelated"]
    failure = factorial["failure_relevant_null_cells"]
    realistic = factorial["bop_realistic_layer_gain_cells"]

    naive = peng["naive_pooled_gain"]
    layer = peng["audit_layer_component"]
    context = peng["audit_context_gain"]
    total = peng["audit_total_gain"]
    buteo = bop["buteo_motivating_sentinel"]

    title = contract["working_title"]
    text = f"""# {title}

**Article type:** Research Article  
**Target journal:** Methods in Ecology and Evolution  
**Draft:** N2 failure-mode manuscript v1

## Abstract

Independent validation can show that a model predicts new ecological observations, but it does not by itself identify which information produced that predictive improvement. In hierarchical data, comparing a richer model with a pooled reference can credit species, region or population identity to the contextual information under study. We formalized this failure as a held-out score decomposition and tested it in a preregistered known-truth experiment varying layer effects, true within-layer context effects, replication, layer-context correlation and whether layer identity entered the learner. At a layer effect calibrated to a real multi-species tracking example, pooled-reference evaluation declared context transfer in {a['pooled_reference_false_positive_rate']:.1%} of explicit-layer null simulations and {b['pooled_reference_false_positive_rate']:.1%} of proxy-layer null simulations, although true within-layer context information was zero. A layer-conditioned decomposition reduced both rates to {a['decomposed_context_false_positive_rate']:.1%}, while retaining power of {d['decomposed_context_power']:.1%}–{e['decomposed_context_power']:.1%} when context truly carried information. Across {failure['cell_count']} failure-relevant null cells, the mean pooled declaration rate was {failure['mean_pooled_reference_positive_rate']:.3f}, versus {failure['mean_decomposed_context_positive_rate']:.4f} after decomposition. A fresh Palmer Penguins audit then reversed empirically: morphology appeared transferable against a pooled island marginal (mean log-score gain {naive['mean_gain']:+.3f}, 95% interval [{naive['mean_gain_lower']:+.3f}, {naive['mean_gain_upper']:+.3f}]), but its species-conditioned increment was negative ({context['mean_gain']:+.3f}, [{context['mean_gain_lower']:+.3f}, {context['mean_gain_upper']:+.3f}]). A Snapshot Serengeti control shows the boundary: pooled references remain appropriate when identity itself is the claimed information. Predictive skill and transfer of a named information source are therefore different claims. The reference distribution must already contain information that is not part of the transfer claim.

**Keywords:** cross-validation; hierarchical data; log score; predictive evaluation; reference model; species identity; transferability

## 1. Introduction

Ecologists increasingly use held-out prediction to test whether environmental, behavioural or biotic information generalizes beyond the observations used for fitting. This is a major improvement over interpreting fitted associations alone. Yet a further inferential step is common: when a richer model predicts better than a lower-information reference, the gain is attributed to the newly emphasized predictor or context. Predictive validity and information attribution are not the same problem. A model may generalize for one informational reason while its improvement is described as evidence for another.

A post-outcome decomposition of a frozen multi-species raptor analysis made the ambiguity concrete. For *Buteo buteo*, mean held-out gain relative to a pooled altitude distribution was {buteo['mean_total_gain']:+.5f} nats per event. Replacing the pooled distribution with a training-fold species distribution contributed {buteo['mean_species_component']:+.5f}, whereas the residual within-species contextual contribution was {buteo['mean_context_within_species_component']:+.5f}. This species-level contrast was not designed as confirmatory evidence, but it exposed a general question: when observations occur in species, regions or populations with different outcome distributions, how much of an apparent contextual gain is simply identity information omitted from the reference?

There are two routes to the same interpretive failure. In an **explicit-layer** case, the predictive model directly includes layer identity, but evaluation compares it with a pooled reference that does not. Improvement then necessarily contains any transferable identity signal. In a **proxy-layer** case, identity is omitted from the learner, but the purported contextual predictor is correlated with layer identity. Context can then recover part of the layer signal even when it carries no information within layers. Neither failure requires row leakage. Species differences and their proxies can generalize to entirely held-out groups, so group cross-validation can validate the prediction while leaving the attribution error intact.

We therefore tested a narrower claim than a general prediction framework would make: **predictive skill does not identify transfer of the claimed information unless the reference is aligned with that claim**. We first froze a known-truth experiment with explicit withdrawal conditions. We then froze a real-data phase before opening a fresh Palmer Penguins result, while treating the raptor example as read-only motivation and Snapshot Serengeti as a semantic control in which identity itself was the intended information. This design separates the mechanism, an empirical reversal and the boundary of the correction.

## 2. Methods

### 2.1 Claim-aligned references and additive score decomposition

Let S(M) denote mean held-out log predictive probability under model or reference M. Consider a pooled reference P, a layer-conditioned reference L, and a full predictor F that contains both layer and contextual information. The total held-out gain is

Delta_total = S(F) - S(P).

For the same full predictor this gain decomposes exactly as

Delta_total = [S(L) - S(P)] + [S(F) - S(L)]
            = Delta_layer + Delta_context.

Thus Delta_total > 0 does not imply Delta_context > 0. If the scientific claim is that contextual information transfers beyond species identity, species identity belongs in the reference. If the scientific claim is that species identity itself transfers, an identity-blind pooled reference is instead appropriate.

The second failure mode is not an algebraic decomposition of one fitted model. When a context-only learner omits layer identity but context is correlated with layer, its pooled-reference gain can reflect proxy information about layer. We therefore evaluated the original context-only learner against the pooled reference and separately audited a prespecified layer-aware full learner against the layer-conditioned reference.

### 2.2 Stage 1: preregistered known-truth experiment

The Stage-1 contract was merged before any simulation result was generated and executed once. Binary outcomes followed

logit P(Y=1) = -0.5 + delta z_L + beta X,

where z_L is a standardized layer score, delta is the layer effect and beta is the true within-layer context effect. We varied delta in {{0, 0.5, 1, 2}}, beta in {{0, 0.25, 0.5}}, 5/12/30 independent groups, 30/100/300 events per group, 2/4/10 layers, absent versus 0.7 layer-context correlation, and whether the focal learner included layer identity. Structurally inestimable combinations were excluded before execution, leaving 864 cells.

Primary validation used five-fold independent-group cross-validation. Random-row cross-validation, accuracy and AUC were diagnostic. The primary outcome was the rate at which the population mean interval declared positive transfer. All-group unanimity was not used. The layer effect delta=2 with four layers and 30 groups produced an oracle layer gain of 0.26647 nats, inside the preregistered 0.20–0.35 window around the motivating BOP species component.

Seven 1000-replicate confirmatory anchors were frozen. The full failure-mode claim required pooled false-transfer probability above 0.5 with its Wilson lower bound above 0.5 in both explicit-layer and correlated-proxy null anchors, nominally controlled decomposed context error, at least 0.80 power for genuine context effects, low high-information bias and adequate method availability.

### 2.3 Population-mean uncertainty

Independent biological groups received equal weight. With no higher-level dependence cluster and at least 10 groups, intervals used group bootstrap. For fewer than 10 independent groups, the frozen Stage-1 rule used a Student t interval.

During development we identified a separate defect in the real-data population summary: percentile cluster bootstrap can become anti-conservative when only a few dependence clusters exist because the resampling support is extremely discrete. Before Stage 2, this was corrected prospectively for subsequent real-data use. With fewer than 10 declared dependence clusters, mean uncertainty uses a CR1 cluster-robust standard error with a Student t critical value on G-1 degrees of freedom. Small-cluster positive-fraction Wilson bounds are labelled descriptive rather than cluster-robust prevalence intervals.

### 2.4 Stage 2: preregistered real-data triangulation

Stage 2 contained exactly two failure-eligible systems and one semantic control.

**BOP_RODENT** was read-only. No model was refitted and raw tracking data were not re-accessed. We used the frozen pooled-to-species-to-context decomposition and its corrected four-species uncertainty. The *B. buteo* decomposition was predeclared as a motivating sentinel but excluded from the system-level reversal denominator.

**Palmer Penguins** was the only fresh Stage-2 result. The source table was pinned to the palmerpenguins upstream commit recorded in the frozen contract. We retained 342 complete observations across three species and three collection years. The naive learner was a random forest predicting island from four morphology measurements. Its held-out log score was compared with the pooled training island marginal. The audit learner used species identity plus the same morphology measurements and was evaluated relative to the training-fold species-conditioned island marginal. Training weights gave equal mass to species and then to individuals within species. Collection year was the held-out fold and dependence cluster. Because only three years were represented, population mean intervals used CR1 standard errors and t(2).

**Snapshot Serengeti** was not reanalysed as a failure candidate. Its frozen question asked whether species identity predicts camera-detected time, so species identity itself is the claimed information. The species-blind temporal marginal is therefore the appropriate lower-information reference. This system was predeclared as a semantic negative control and excluded from reversal counts.

Stage 2 separately reported point sign reversal, inferential downgrade and strong attenuation. The two-system denominator was explicitly descriptive and was not used to estimate prevalence in ecological studies.

### 2.5 Implementation and reproducibility

ODSP supplied the score-accounting implementation, deterministic contracts and frozen receipts. It is not the central scientific claim of this manuscript. Stage 1 and the fresh Stage-2 Penguins audit were each executed through one-shot workflows after their contracts were merged; neither exposed a manual rerun route. The superseded framework manuscript and historical certification-family development were not used as evidence for the present claim.

## 3. Results

### 3.1 Pooled-reference evaluation produced false context transfer under known truth

The preregistered Stage-1 claim passed all confirmatory conditions. In the explicit-layer null anchor, the pooled-reference false-transfer rate was {a['pooled_reference_false_positive_rate']:.3f}, with Wilson 95% lower bound {a['pooled_reference_false_positive_wilson_95_lower']:.3f}. In the correlated-proxy null anchor it was likewise {b['pooled_reference_false_positive_rate']:.3f}, with lower bound {b['pooled_reference_false_positive_wilson_95_lower']:.3f}. True within-layer context information was zero in both cases.

The claim-aligned decomposition removed those declarations: the decomposed context false-transfer rate was {a['decomposed_context_false_positive_rate']:.3f} in the explicit-layer anchor and {b['decomposed_context_false_positive_rate']:.3f} in the proxy anchor. In the negative control, where context neither contained a true effect nor proxied layer identity, the pooled false-transfer rate was {c['pooled_reference_false_positive_rate']:.3f} and the decomposed rate was {c['decomposed_context_false_positive_rate']:.3f}.

### 3.2 The failure occupied a broad and realistic parameter region

Across {failure['cell_count']} null-context cells satisfying the preregistered failure-relevant definition, the mean pooled positive-declaration rate was {failure['mean_pooled_reference_positive_rate']:.3f}, the median was {failure['median_pooled_reference_positive_rate']:.3f}, and {failure['fraction_of_cells_with_positive_rate_gt_0_5']:.1%} of cells had false-transfer rates above 0.5. The corresponding mean decomposed-context declaration rate was only {failure['mean_decomposed_context_positive_rate']:.4f}, with maximum {failure['max_decomposed_context_positive_rate']:.4f}.

The result was not confined to extreme layer effects. Among {realistic['failure_relevant_cell_count']} cells whose oracle layer gain fell in the preregistered BOP-realistic 0.20–0.35 nats window, mean pooled false-transfer rate was {realistic['mean_pooled_reference_positive_rate']:.3f}; {realistic['fraction_of_cells_with_positive_rate_gt_0_5']:.1%} of cells exceeded 0.5. Mean decomposed-context declaration rate was {realistic['mean_decomposed_context_positive_rate']:.5f}.

The decomposition retained sensitivity when context truly mattered. Power was {d['decomposed_context_power']:.3f} under correlated context and {e['decomposed_context_power']:.3f} without correlation. High-information absolute bias was below 0.001 nats in the confirmatory anchors.

### 3.3 A fresh real-data test reversed from positive to negative

The Palmer Penguins result matched the proxy-layer failure predicted by Stage 1. A morphology-only random forest evaluated against the pooled island marginal had mean held-out log-score gain {naive['mean_gain']:+.5f} nats, with CR1+t(2) 95% interval [{naive['mean_gain_lower']:+.5f}, {naive['mean_gain_upper']:+.5f}]. The pooled analysis therefore classified morphology transfer as positive.

Species identity alone carried a larger pooled-reference component: mean gain {layer['mean_gain']:+.5f}, interval [{layer['mean_gain_lower']:+.5f}, {layer['mean_gain_upper']:+.5f}]. Once the audit model was evaluated relative to the species-conditioned island distribution, the morphology increment reversed sign. Its mean was {context['mean_gain']:+.5f}, interval [{context['mean_gain_lower']:+.5f}, {context['mean_gain_upper']:+.5f}], and its status was nonpositive. The full species-plus-morphology model remained predictive relative to the pooled reference (mean {total['mean_gain']:+.5f}), illustrating precisely why total predictive skill and contextual transfer are different claims.

All three preregistered Stage-2 descriptors were triggered: point sign reversal, inferential downgrade and strong attenuation.

### 3.4 The motivating BOP system became a decomposition example rather than a positive population claim

After the few-cluster correction, BOP could not be used as evidence for positive population-mean transfer. The equal-individual total mean remained {bop['population_v2_total_mean_gain']:+.5f}, but its four-species CR1+t(3) interval crossed zero and its status was {bop['population_v2_total_status']}. The population mean within-species context component was likewise {bop['population_v2_context_mean_gain']:+.5f} and {bop['population_v2_context_status']}.

The predeclared *B. buteo* sentinel nevertheless remains useful descriptively: pooled total gain {buteo['mean_total_gain']:+.5f} decomposed into species component {buteo['mean_species_component']:+.5f} and within-species context component {buteo['mean_context_within_species_component']:+.5f}. It illustrates the failure mode but is not counted as an inferential system-level reversal.

### 3.5 A semantic control showed when pooling is correct

Snapshot Serengeti defined the boundary of the argument. Its scientific claim concerned species identity itself: whether species-conditioned detected-time distributions transfer to held-out site folds. The appropriate lower-information reference is therefore species-blind time. The three frozen held-out gains were {control['heldout_gains'][0]:+.5f}, {control['heldout_gains'][1]:+.5f} and {control['heldout_gains'][2]:+.5f}, all positive.

Thus the correction is not a blanket instruction to condition every reference. The appropriate comparator depends on the information claim.

## 4. Discussion

Our results identify a failure mode in the interpretation of predictive validation rather than in predictive validation itself. Held-out improvement can be entirely genuine and can generalize across independent groups, yet the improvement may still be assigned to the wrong information source. In the known-truth experiment, group cross-validation repeatedly validated a false context-transfer interpretation because the pooled reference omitted a stable layer effect or because context served as a proxy for an omitted layer. The problem survived independence-aware validation because it arose from the definition of the contrast.

The magnitude of the failure was substantial. At a layer effect calibrated to an empirical multi-species tracking decomposition, pooled-reference false transfer was effectively certain in both explicit-layer and proxy-layer confirmatory worlds. Across the broader failure-relevant grid, most null-context cells produced false-transfer rates above one half. The conditioned decomposition reduced those rates to near zero while preserving high power for genuine context effects. The correction therefore did not succeed merely by making the test conservative.

The fresh Palmer Penguins reversal provides a concrete empirical analogue. Morphology strongly improved island prediction relative to a pooled island distribution, yet after species identity was placed in the reference, the incremental morphology signal was negative. The point is not that morphology is biologically irrelevant, nor that species causes island occupancy. Rather, the original pooled contrast did not identify the information source described by a within-species morphology interpretation.

The Snapshot Serengeti control is equally important. When species identity itself is the focal information, an identity-blind pooled reference is not a mistake; it is the correct comparator. We therefore propose a claim-alignment principle: **the reference should already contain every information layer that is not part of the transfer claim being tested**. This formulation avoids both extremes—crediting omitted layer identity to context, and conditioning away the very information one intends to evaluate.

The principle applies broadly to ecological prediction. Species distribution and movement models often combine environment, taxonomic identity, traits, movement capacity, activity time, spatial history and interactions. A richer model may improve out-of-sample prediction because of any combination of these sources. If a paper claims that one particular addition transfers, predictive skill should be decomposed relative to a reference that already contains the other relevant layers. This is directly relevant to future eSDM evaluation: improvements attributed to movement, activity or biotic interactions should not inherit stable species or regional identity signals through an under-informed comparator.

Several limitations bound the claim. Stage 2 contains empirical triangulation, not a survey of published-study prevalence. BOP has only four species clusters and Penguins only three collection-year clusters, motivating explicit small-cluster uncertainty rather than strong superpopulation claims. The decomposition attributes predictive score contributions but does not identify biological causality. Finally, the appropriate hierarchy is scientific rather than automatic: choosing which information belongs in a reference requires a clearly stated claim.

The central conclusion is consequently narrower than a general modelling framework but stronger as an inferential rule. **Prediction skill can generalize while attribution of that skill is wrong. Matching the reference to the claimed information is necessary before predictive improvement can be interpreted as transfer of that information.**

## 5. Data and code boundary

All empirical data were publicly archived by their original providers. The Palmer Penguins source was pinned to the upstream commit declared before the fresh Stage-2 result. BOP and Snapshot Serengeti were read only through frozen analysis artifacts or receipts. Stage-1 known-truth and Stage-2 fresh execution were run once after their contracts were merged.

The software implementation, analysis contracts, result receipts and figure-building code will accompany the manuscript. Historical ODSP certification-family, lattice and superseded framework-paper materials remain repository history and are not part of the scientific evidence for this manuscript.
"""
    return text


def build(output: Path, manifest_path: Path | None = None) -> dict[str, object]:
    contract, _, _ = _assert_sources()
    text = build_manuscript_text()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")

    abstract = text.split("## Abstract", 1)[1].split("**Keywords:**", 1)[0]
    abstract_words = len(_words(abstract))
    manifest = {
        "schema_version": 1,
        "role": "n2_mee_failure_mode_manuscript_v1",
        "contract_id": contract["contract_id"],
        "word_count": len(_words(text)),
        "abstract_word_count": abstract_words,
        "abstract_ceiling_words": int(contract["abstract"]["maximum_words"]),
        "abstract_within_ceiling": abstract_words <= int(contract["abstract"]["maximum_words"]),
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "framework_paper_positioning": False,
        "stage1_result_modified": False,
        "stage2_result_modified": False,
        "new_inference_added_by_manuscript_builder": False,
        "output": output.name,
    }
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
        default=Path("build/n2_failure_mode_v1/N2_MEE_FAILURE_MODE_MANUSCRIPT_DRAFT_v1.md"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("build/n2_failure_mode_v1/N2_MEE_FAILURE_MODE_MANUSCRIPT_DRAFT_v1.manifest.json"),
    )
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.manifest), sort_keys=True))


if __name__ == "__main__":
    main()
