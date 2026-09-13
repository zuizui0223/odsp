#!/usr/bin/env python3
"""Build MEE manuscript v6 with cross-geometry state-space generality.

Version 6 starts from the validated v5 manuscript.  It changes the methodological
framing from finite categorical state prediction to ecological-state distribution
prediction, using the separately validated common log-score layer across finite
discrete, continuous, circular and joint continuous-circular state spaces.

No empirical endpoint is rerun, no frozen comparator or terminal rule is changed,
and the post-outcome BOP species/context decomposition from v5 is preserved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from odsp.state_space_generality_benchmark import run_state_space_generality_benchmark
from scripts.build_n2_mee_manuscript_v5 import build_manuscript_text as build_v5_text


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "N2_MEE_STATE_PREDICTION_V6_CONTRACT.json"
STATE_SPACE_CONTRACT = ROOT / "N2_STATE_SPACE_GENERALITY_CONTRACT.json"


def _replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"expected exactly one occurrence, found {count}: {old!r}")
    return text.replace(old, new, 1)


def _words(text: str) -> list[str]:
    return re.findall(r"\b[\w'-]+\b", text)


def _abstract(text: str) -> str:
    start = text.index("## Abstract") + len("## Abstract")
    end = text.index("**Keywords:**", start)
    return text[start:end]


def _validated_contracts() -> tuple[dict[str, object], dict[str, object]]:
    manuscript = json.loads(CONTRACT.read_text(encoding="utf-8"))
    state_space = json.loads(STATE_SPACE_CONTRACT.read_text(encoding="utf-8"))
    if manuscript["contract_id"] != "n2-mee-state-prediction-manuscript-v6":
        raise ValueError("unexpected v6 manuscript contract")
    if state_space["contract_id"] != "n2-state-space-generality-v1":
        raise ValueError("unexpected state-space generality contract")
    if manuscript["common_primary_transfer_score"] != (
        "G_j = E_heldout,j[log q_train(A|X) - log q0_train(A)]"
    ):
        raise ValueError("unexpected v6 common primary score")
    if manuscript["empirical_endpoint_preservation"]["empirical_endpoint_rerun"] is not False:
        raise ValueError("v6 may not rerun empirical endpoints")
    return manuscript, state_space


def build_manuscript_text() -> str:
    _validated_contracts()
    benchmark = run_state_space_generality_benchmark()
    if not benchmark.passed or benchmark.check_count != 10:
        raise ValueError("cross-geometry state-space benchmark is not closed")
    max_error = benchmark.maximum_absolute_error

    text = build_v5_text()
    text = _replace_once(
        text,
        "**Review draft:** anonymized state-prediction version 5",
        "**Review draft:** anonymized state-prediction version 6",
    )

    abstract_old = (
        "2. We introduce ODSP, a model-agnostic framework for **state-resolved ecological prediction**. For declared ecological states `A` and contextual predictors `X`, ODSP represents predictions as `P(A|X)` and evaluates them against the lower-information training marginal `P(A)`. The primary transfer score for independent group `j` is `G_j = E[log P_train(A|X) - log P_train(A)]`. Multiclass Brier improvement, top-1 accuracy and assigned-state probability provide complementary diagnostics. Known-truth benchmarks test stable, unorganized and shifted predictive regimes, while a separate information-theoretic layer quantifies added-state thickness and fitted organization."
    )
    abstract_new = (
        "2. We introduce ODSP, a model-agnostic framework for **ecological-state distribution prediction**. For a declared ecological state space `A` and contextual predictors `X`, ODSP predicts `q(A|X)`: a probability mass function for finite states, a density for continuous or circular states, or a joint density for composite states. Across these geometries the primary transfer score for independent group `j` is `G_j = E[log q_train(A|X) - log q0_train(A)]`, where `q0` is a declared lower-information training comparator evaluated on the same realized state under the same reference measure. State-space-specific diagnostics complement this common score."
    )
    text = _replace_once(text, abstract_old, abstract_new)

    abstract4_old = (
        "4. ODSP therefore changes the prediction target from a collapsed ecological scalar to a distribution over explicit ecological states while keeping independent transfer as a separate evidential requirement. The framework can sit above different learners, including random forests, multinomial regression and other probabilistic models. It does not guarantee universal transfer, infer causal drivers or determine the biological meaning of an axis; instead it provides a reproducible way to ask **which state, with what probability, and does that extra resolution generalize?**"
    )
    abstract4_new = (
        f"4. ODSP therefore changes the prediction target from a collapsed ecological scalar to a distribution over explicit ecological states without requiring those states to be binned. The common log-score layer was numerically identical to native discrete, continuous, circular and joint scorers in {benchmark.passed_count}/{benchmark.check_count} cross-geometry obligations (maximum absolute error `{max_error:.2e}`). The framework can sit above different learners and does not make biological generality or causality follow from mathematical portability; it asks **which ecological-state distribution is predicted, and does its added resolution generalize?**"
    )
    text = _replace_once(text, abstract4_old, abstract4_new)

    intro_target_old = (
        "We therefore formulate a different prediction target. Let `A` denote one or more explicit ecological states, such as altitude class, depth class, activity-time bin, phenophase or behaviour, and let `X` denote the contextual information available to a predictor. Instead of returning only a scalar ecological support value, a state-resolved model returns\n\n`P(A|X)`.\n\nFor a flight-height example, this means predicting a probability distribution across altitude states for each environmental and spatiotemporal context. For a camera-trap example, it could mean a distribution over time states conditional on site, species and environmental context. Multiple state axes can be predicted jointly. The conceptual change is small but consequential: the output of the model is no longer only “suitable here” but “given this context, these ecological states have these probabilities.”"
    )
    intro_target_new = (
        "We therefore formulate a different prediction target. Let `A` denote a scientifically declared ecological state space and let `X` denote contextual information available to a predictor. Instead of returning only a scalar ecological support value, ODSP targets a conditional ecological-state distribution\n\n`q(A|X)`.\n\nThe probability object follows the geometry of the state rather than forcing every state into bins. For finite categories, `q` is a probability mass function; for real-valued altitude or depth it can be a continuous density; for clock time or another periodic state it can be a circular density; and multiple state dimensions can be represented jointly. The conceptual change is small but consequential: the output is no longer only “suitable here” but a distribution describing which ecological states are predicted under the declared context."
    )
    text = _replace_once(text, intro_target_old, intro_target_new)

    intro_score_old = (
        "A richer prediction requires a correspondingly stricter validation. Extra conditioning information will almost always create a more detailed fitted representation, but detail alone is not predictive value. We therefore compare the state-resolved prediction `P(A|X)` with an explicit lower-information comparator, the training marginal `P(A)`. On a prospectively independent group, the log-score gain\n\n`G = E[log P_train(A|X) - log P_train(A)]`\n\nasks whether retaining the contextual state structure improves probabilistic prediction over ignoring it. We score independent groups separately rather than allowing large groups to dominate a pooled average. This gives a fail-closed distinction among generalizing, non-generalizing and mixed outcomes. It also connects naturally to the information-theoretic foundation of ODSP: when training and target distributions are the same, expected conditional-versus-marginal log gain is the mutual information supplied by the conditioning state."
    )
    intro_score_new = (
        "A richer prediction requires a correspondingly stricter validation. Extra conditioning information will almost always create a more detailed fitted representation, but detail alone is not predictive value. We compare the context-conditioned distribution with a prospectively declared lower-information training comparator `q0`. On an independent group, the common log-score gain\n\n`G = E[log q_train(A|X) - log q0_train(A)]`\n\nasks whether retaining the contextual state structure improves probabilistic prediction over the lower-information baseline. Both terms are evaluated on the same realized held-out state and against the same reference measure, so common density/Jacobian terms cancel. We score independent groups separately rather than allowing large groups to dominate a pooled average. For the finite-discrete marginal comparator used in the empirical endpoints, the same-distribution expectation reduces to the familiar mutual-information identity."
    )
    text = _replace_once(text, intro_score_old, intro_score_new)

    intro_scope_old = (
        "Here we develop ODSP as a general framework for state-resolved ecological prediction and independent transfer evaluation. ODSP is not a competing occurrence-SDM learner. It defines a response representation, probability-field interface, scoring architecture and claim hierarchy that can be used with different upstream learners. We provide a transparent Dirichlet-smoothed discrete reference learner and an interface for probabilistic covariate models; random forest and multinomial logistic regression are used as reference covariate learners in the empirical prediction demonstration. We validate the predictive behavior under known truth, retain an axis-agnostic information-theoretic audit of state thickness and organization, and then execute two new public-data prediction endpoints frozen before outcome access. The first tests whether a seemingly data-rich tracking archive contains enough independent individuals to open prediction transfer. The second tests species-aware altitude-state prediction across 30 independent raptors from four species. Earlier Tawaki, bat and Snapshot Serengeti endpoints are retained as supporting evidence for the broader inferential hierarchy: estimability can fail, added-state thickness can be present without transfer, and non-spatial state organization can generalize. Our central question is therefore no longer only how much a flat representation hides, but whether the hidden ecological state can be **predicted and independently transferred**."
    )
    intro_scope_new = (
        "Here we develop ODSP as a general framework for ecological-state distribution prediction and independent transfer evaluation. ODSP is not a competing occurrence-SDM learner. It defines the prediction target, lower-information comparison and independent-transfer logic while allowing the upstream learner to depend on the state geometry. The software includes transparent reference implementations for finite discrete, continuous scalar, circular scalar and joint continuous-circular states, plus an adapter that scores externally supplied log probabilities or densities on the same held-out scale. We validate the common gain across those four geometries and separately retain the finite-discrete information-theoretic audit of state thickness and organization. The prospective empirical prediction endpoints remain finite-discrete altitude-state applications: one tests whether a data-rich archive contains enough independent individuals to open transfer, and the other tests species-aware prediction across 30 independent raptors from four species. Earlier Tawaki, bat and Snapshot Serengeti endpoints remain supporting evidence that estimability, state richness and transfer are distinct."
    )
    text = _replace_once(text, intro_scope_old, intro_scope_new)

    text = _replace_once(
        text,
        "## 2.1 State-resolved prediction target",
        "## 2.1 Ecological-state distribution prediction target",
    )
    methods_target_old = (
        "ODSP assumes a declared ecological state axis or set of axes `A` and a set of contextual predictors or base states `X`. The prediction target is a normalized probability distribution\n\n`P(A|X)`.\n\nThe elements of `A` must have explicit biological and measurement semantics. Examples include discretized flight altitude, depth, canopy stratum, activity-time class, phenological phase, microhabitat state or behaviour. Multiple axes can be combined into a joint state, for example `A=(depth,time)`. ODSP does not infer what an axis means from its values. A locality elevation is not automatically organism height, a camera timestamp is not automatically unbiased activity, and absolute altitude above mean sea level is not height above ground unless an explicit terrain transformation is applied.\n\nThis formulation differs from occurrence SDM. A conventional occurrence model may estimate `P(species occurrence|environment)`. ODSP can use outputs from such a model, but its state-resolved target is instead the conditional distribution of a declared ecological state. Thus random forest, multinomial regression, boosted trees, Bayesian models or neural networks can all act as state learners if they provide normalized predictive probabilities. ODSP supplies the common response representation and validation layer."
    )
    methods_target_new = (
        "ODSP assumes a scientifically declared ecological state space `A` and contextual predictors or base states `X`. The common target is a conditional distribution `q(A|X)`. Its mathematical form follows the state space: a probability mass function for finite categorical states, a density for a real-valued state, a periodic density for a circular state, or a joint density for a composite state. ODSP therefore does not require continuous altitude, depth or time to be discretized solely to enter the framework.\n\nThe state still requires explicit biological and measurement semantics. A locality elevation is not automatically organism height, a camera timestamp is not automatically unbiased activity, and absolute altitude above mean sea level is not height above ground without an explicit terrain transformation. Choosing a state geometry is part of the scientific design rather than an automatic software inference.\n\nThis formulation differs from occurrence SDM. A conventional occurrence model may estimate `P(species occurrence|environment)`. ODSP instead audits the distribution of a declared ecological state under context. Random forests, generalized models, Bayesian models, neural networks or other probabilistic learners can enter the framework if they provide evaluable predictive probability mass or density on held-out realized states. The framework supplies the common prediction-and-transfer layer; it does not prescribe one learner for every geometry."
    )
    text = _replace_once(text, methods_target_old, methods_target_new)

    text = _replace_once(
        text,
        "## 2.3 Covariate-to-state prediction",
        "## 2.3 State-space-specific learners and a common scoring interface",
    )
    methods_learner_old = (
        "For continuous or mixed contextual predictors, ODSP exposes a generic `predict_proba` interface. A fitted probabilistic classifier receives a feature matrix `X` and state labels `A`, then returns a probability vector over the training state classes for each new covariate row. The same ODSP scoring functions can therefore compare predictions from different algorithms under an identical state target and comparator."
    )
    methods_learner_new = (
        "For finite categorical responses, ODSP exposes a generic `predict_proba` interface: a probabilistic classifier receives a feature matrix `X` and state labels and returns a probability vector over training states for each new covariate row. The continuous reference implementation uses a weighted linear-Gaussian conditional density; the circular reference implementation predicts sine/cosine components and a von Mises residual density without creating an artificial boundary at the period origin; and the joint continuous-circular reference implementation uses the autoregressive factorization `p(z,t|X)=p(t|X)p(z|X,t)`. These learners are transparent demonstrations rather than mandatory algorithms. External models can enter the common layer by supplying richer and lower-information log probability/density values at the same realized held-out states."
    )
    text = _replace_once(text, methods_learner_old, methods_learner_new)

    text = _replace_once(
        text,
        "## 2.4 Predictive scoring against a lower-information comparator",
        "## 2.4 Predictive scoring against a lower-information comparator across state spaces",
    )
    methods_score_old = (
        "The primary held-out metric is conditional-versus-marginal log-score gain. For independent held-out group `j`,\n\n`G_j = E_heldout,j[log P_train(A|X) - log P_train(A)]`."
    )
    methods_score_new = (
        "The primary held-out metric is a conditional-versus-lower-information logarithmic-score gain. For independent held-out group `j`,\n\n`G_j = E_heldout,j[log q_train(A|X) - log q0_train(A)]`.\n\nFor finite states the score uses probability mass; for continuous, circular and joint states it uses density. The two terms must be evaluated on the same realized state against the same reference measure. Consequently a common change of units or Jacobian contributes the same row-wise log term to both scores and cancels from `G_j`. This shared score does not make differential entropy, effective-state counts or other geometry-specific summaries universal."
    )
    text = _replace_once(text, methods_score_old, methods_score_new)

    methods_marginal_old = (
        "The marginal comparator is estimated from the same training data as the state-resolved predictor and discards contextual organization. It therefore answers a concrete question: does the detailed state prediction outperform simply knowing the overall state frequencies available from the training sample?"
    )
    methods_marginal_new = (
        "The reference lower-information comparator is estimated from the same training data and discards the contextual organization under test. In the finite-discrete empirical endpoints it is the training marginal `P(A)`; other applications may use an equivalently declared lower-information density appropriate to their state geometry. The learner, comparator and independent validation unit must be fixed by the scientific design rather than inferred from the generic scoring layer."
    )
    text = _replace_once(text, methods_marginal_old, methods_marginal_new)

    methods_positive_old = (
        "Positive gain means that the conditional model assigns higher geometric-mean probability to the realized held-out states than the marginal comparator. A negative gain means that the additional conditioning structure harms held-out log score. Because the logarithmic score is sensitive to confidently assigning very low probability to realized states, it can expose transfer failures that are less visible to bounded metrics."
    )
    methods_positive_new = (
        "Positive gain means that the context-conditioned distribution assigns higher average logarithmic predictive density or mass to the realized held-out states than its declared lower-information comparator. A negative gain means that the additional conditioning structure harms held-out log score. Because logarithmic score strongly penalizes very low predictive mass or density at realized states, it can expose transfer failures that are less visible to bounded diagnostics."
    )
    text = _replace_once(text, methods_positive_old, methods_positive_new)

    methods_diag_old = (
        "We additionally report the multiclass Brier score, Brier improvement relative to the marginal comparator, top-1 state accuracy, top-1 improvement and mean probability assigned to the realized state. These are secondary diagnostics. They do not override the primary log-score terminal rule."
    )
    methods_diag_new = (
        "Secondary diagnostics remain state-space-specific. Finite categorical predictions can report multiclass Brier score, top-1 accuracy and assigned-state probability; continuous predictions can report RMSE and CRPS; circular predictions can report circular error; and joint distributions can be sampled or summarized marginally. The joint reference implementation also reports `E[log p(z|X,t)-log p(z|X)]` as a directional predictive coupling gain. This quantity asks whether the realized circular state improves prediction of the continuous state beyond context alone; it is neither a symmetric dependence measure nor a causal effect. None of these secondary quantities overrides the primary independent-group log-score rule."
    )
    text = _replace_once(text, methods_diag_old, methods_diag_new)

    generality_old = (
        "## 2.7 Information-theoretic audit and representation generality\n\nThe predictive layer retains the earlier ODSP information-theoretic audit. For non-negative support over base state `B` and added state `A`, conditional entropy\n\n`H(A|B)`\n\nmeasures how much added-state uncertainty remains after the base state is known, and `exp[H(A|B)]` gives the corresponding effective number of states. Fitted organization can be described by `I(A;B)` or an axis-appropriate conditional information quantity. Under the same generating distribution,\n\n`E[log P(A|B) - log P(A)] = I(A;B)`,\n\nlinking descriptive organization to the expected predictive advantage of conditioning.\n\nThe implementation was separately stress-tested for axis permutation, label relabelling, mass scaling, nuisance-axis refinement, chain-rule identities, coarse-graining behavior, sparse support and multi-axis composition. Across 1,873 property obligations there were no failures; maximum absolute numerical error was `2.49 x 10^-14`. This establishes implementation and representation genericity over the validated finite discrete domain, not universal biological generality."
    )
    generality_new = (
        f"## 2.7 Information-theoretic audit and two levels of mathematical generality\n\nFor finite non-negative support over base state `B` and added state `A`, ODSP retains the discrete information-theoretic audit. Conditional entropy `H(A|B)` describes residual added-state uncertainty and `exp[H(A|B)]` the corresponding effective number of finite states; fitted organization can be described by `I(A;B)` or an appropriate conditional-information quantity. Under the same finite-discrete generating distribution, `E[log P(A|B)-log P(A)] = I(A;B)`. The finite-discrete implementation was stress-tested for axis permutation, label relabelling, mass scaling, nuisance-axis refinement, chain rules, coarse-graining, sparse support and multi-axis composition. All 1,873 representation-level obligations passed, with maximum absolute numerical error `2.49 x 10^-14`.\n\nWe separately tested whether the primary held-out log-score estimand survives a change in the geometry of the ecological state. Native finite-discrete probability mass, continuous Gaussian density, circular von Mises density and joint continuous-circular density scorers were each compared with the same generic `E[log q(A|X)-log q0(A)]` implementation. For every geometry we also added an arbitrary common row-wise log reference-measure term to both richer and baseline scores; the gain had to remain unchanged. All {benchmark.check_count}/{benchmark.check_count} cross-geometry obligations passed, with maximum absolute error `{max_error:.2e}`. This establishes a common predictive-gain layer across the four validated state spaces. It does not make differential entropy coordinate-invariant, justify `exp(H)` as an effective-state count for continuous variables, or establish biological generality."
    )
    text = _replace_once(text, generality_old, generality_new)

    results_generality_old = (
        "## 3.2 The generic information and prediction core was representation-stable\n\nAll 1,873 axis-agnostic property obligations passed. The maximum absolute numerical error was `2.49 x 10^-14`. Tested properties included mass-scaling invariance, axis and category relabelling, nuisance-axis refinement, conditional-entropy monotonicity, chain rules, coarse-graining, sparse support, unavailable-mask invariance and multi-axis composition. This supports an axis-agnostic implementation over finite discrete state spaces; it does not imply that all biological axes are equally meaningful or equally predictable."
    )
    results_generality_new = (
        f"## 3.2 The predictive-gain estimand was stable across state-space geometries\n\nThe finite-discrete representation benchmark remained fully satisfied: all 1,873 axis-agnostic obligations passed, with maximum absolute numerical error `2.49 x 10^-14`. A separate cross-geometry benchmark then tested the common primary gain against the existing native implementations. All {benchmark.passed_count}/{benchmark.check_count} obligations passed with maximum absolute error `{max_error:.2e}`. The generic gain exactly matched the native finite-discrete, continuous, circular and joint continuous-circular primary gains within tolerance, and arbitrary common row-wise reference-measure shifts cancelled in each geometry. Conflicting independent groups remained `mixed` rather than being rescued by pooled observation mass. These results establish implementation-level portability of the primary predictive comparison, not equal biological validity or predictability of all ecological states."
    )
    text = _replace_once(text, results_generality_old, results_generality_new)

    discussion41_old = (
        "The central methodological shift is from predicting a scalar ecological surface to predicting a distribution over ecological states. Adding temperature, vegetation or topography to an occurrence model enriches the predictor set but can still return one number per location. ODSP instead changes the response representation: the model asks which ecological state is expected under a context and with what probability. A spatial map can therefore be accompanied by a vertical, temporal, phenological or behavioural state distribution at each prediction unit."
    )
    discussion41_new = (
        "The central methodological shift is from predicting a scalar ecological surface to predicting a distribution over ecological states. Adding temperature, vegetation or topography to an occurrence model enriches the predictor set but can still return one number per location. ODSP instead changes the response representation: the model asks how predictive probability is distributed over a scientifically declared state space. That space can be categorical, continuous, circular or joint, so a spatial prediction can be accompanied by a vertical, temporal, phenological or behavioural distribution without requiring every axis to be discretized."
    )
    text = _replace_once(text, discussion41_old, discussion41_new)

    discussion44_old = (
        "ODSP should not be presented as another entry in an algorithm tournament. MaxEnt, random forest, boosted trees, generalized additive models, hierarchical Bayesian models and neural networks differ in how they learn relationships. ODSP instead specifies **what is predicted and how the extra state resolution is audited**. Any learner that supplies a normalized state-probability field can be compared under the same state target, marginal comparator and independent-group scores."
    )
    discussion44_new = (
        "ODSP should not be presented as another entry in an algorithm tournament. MaxEnt, random forest, boosted trees, generalized additive models, hierarchical Bayesian models and neural networks differ in how they learn relationships. ODSP instead specifies **what distribution is predicted and how its extra state resolution is audited**. Any learner that supplies evaluable predictive mass or density at realized states can enter the common held-out log-score layer, while state-space-specific diagnostics remain attached to the appropriate geometry."
    )
    text = _replace_once(text, discussion44_old, discussion44_new)

    discussion45_old = (
        "## 4.5 Mathematical genericity is broader than current biological validation\n\nThe information and scoring core is axis-agnostic over validated finite discrete support. Height, depth, time, behaviour and multiple joint states can be represented through the same probability architecture, and the property benchmark confirms expected invariances and information identities. This is mathematical and implementation genericity.\n\nBiological generality is narrower. The prospective state-prediction demonstration currently concerns absolute-altitude states in tagged raptors. The earlier supporting chain adds temporal camera-trap states and bat vertical states, but it does not establish that every ecological axis will be equally predictable or transferable. Wider biological generality requires new prospectively designed state-prediction endpoints with different organisms, sensors, state semantics and independence structures."
    )
    discussion45_new = (
        "## 4.5 State-space generality is broader than current biological validation\n\nThe present evidence supports two different kinds of mathematical portability. Within finite discrete support, information and prediction quantities are stable to representation changes such as axis order, labels and nuisance refinements. Across state geometries, the primary conditional-versus-lower-information log-score gain is the same estimand for probability masses and for continuous, circular and joint densities when evaluated under a shared reference measure. The latter result is deliberately narrower than claiming that all information-theoretic summaries are geometry-free: differential entropy changes under reparameterization, and the finite-state effective-count interpretation is not carried into continuous spaces here.\n\nBiological generality is narrower still. The prospective state-prediction demonstration currently concerns discretized absolute-altitude states in tagged raptors. The earlier supporting chain adds temporal camera-trap states and bat vertical states, while the continuous, circular and joint modules in this paper provide implementation-level and known-structure validation rather than new prospective biological endpoints. Wider biological generality requires prospectively designed distribution-prediction endpoints with different organisms, sensors, state geometries and independence structures."
    )
    text = _replace_once(text, discussion45_old, discussion45_new)

    conclusion_old = (
        "ODSP provides a way to move beyond ecological predictions that collapse an organism or community to one scalar value. The framework predicts a probability distribution over explicitly declared ecological states and tests whether the additional resolution improves prediction for prospectively independent groups. Its known-truth benchmark distinguishes stable, null and shifted predictive regimes; its prospective empirical tests show both fail-closed unavailability and strong but heterogeneous cross-individual prediction."
    )
    conclusion_new = (
        "ODSP provides a way to move beyond ecological predictions that collapse an organism or community to one scalar value. The framework predicts a distribution over an explicitly declared ecological state space and tests whether the additional resolution improves prediction for prospectively independent groups. Its common logarithmic gain applies to validated finite-discrete, continuous, circular and joint state geometries, while geometry-specific diagnostics and biological semantics remain explicit. Its prospective empirical tests show both fail-closed unavailability and strong but heterogeneous cross-individual prediction."
    )
    text = _replace_once(text, conclusion_old, conclusion_new)

    final_old = (
        "The resulting question is richer than “where is the species?” but stricter than “can we fit another dimension?”: **which ecological state is predicted, with what probability, and does that prediction transfer?**"
    )
    final_new = (
        "The resulting question is richer than “where is the species?” but stricter than “can we fit another dimension?”: **what ecological-state distribution is predicted, how much does that resolution improve independent prediction, and where does transfer fail?**"
    )
    text = _replace_once(text, final_old, final_new)

    return text.rstrip() + "\n"


def build(output: Path, manifest_path: Path | None = None) -> dict[str, object]:
    text = build_manuscript_text()
    benchmark = run_state_space_generality_benchmark()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    abstract_words = len(_words(_abstract(text)))
    manifest = {
        "schema_version": 1,
        "role": "n2_mee_state_prediction_manuscript_v6",
        "base_manuscript_builder": "scripts/build_n2_mee_manuscript_v5.py",
        "new_evidence_contract": STATE_SPACE_CONTRACT.name,
        "word_count": len(_words(text)),
        "abstract_word_count": abstract_words,
        "abstract_within_350_words": abstract_words <= 350,
        "state_space_generality_check_count": benchmark.check_count,
        "state_space_generality_failed_count": benchmark.failed_count,
        "state_space_generality_maximum_absolute_error": benchmark.maximum_absolute_error,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "empirical_endpoint_rerun": False,
        "primary_bop_comparator_changed": False,
        "primary_bop_terminal_changed": False,
        "mh_terminal_changed": False,
        "n2_to_n3_promoted": False,
        "output": output.name,
    }
    if not manifest["abstract_within_350_words"]:
        raise ValueError(f"abstract remains too long: {abstract_words} words")
    if benchmark.failed_count != 0:
        raise ValueError("state-space generality benchmark has failures")
    if manifest_path is not None:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("build/state_prediction_v6/manuscript/N2_MEE_MANUSCRIPT_DRAFT_v6.md"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("build/state_prediction_v6/manuscript/N2_MEE_MANUSCRIPT_DRAFT_v6.manifest.json"),
    )
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.manifest), sort_keys=True))


if __name__ == "__main__":
    main()
