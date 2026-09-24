"""Known-truth engine for the frozen N2 stratified-context failure-mode study."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import itertools
import json
import math
from pathlib import Path
from statistics import NormalDist
from typing import Mapping, Sequence

import numpy as np


CONTRACT_FILENAME = "N2_STRATIFIED_CONTEXT_TRANSFER_FAILURE_MODE_STAGE1_CONTRACT.json"
FROZEN_CONTRACT_MERGE_SHA = "05609e5a9fe4200d9cd7a1f46c807f9f682b1c72"
_T95 = {
    1: 12.7062047364,
    2: 4.30265272975,
    3: 3.18244630528,
    4: 2.77644510520,
    5: 2.57058183564,
    6: 2.44691184879,
    7: 2.36462425101,
    8: 2.30600413503,
    9: 2.26215716274,
}


@dataclass(frozen=True)
class Stage1Scenario:
    layer_effect_scale: float
    within_layer_context_effect: float
    group_count: int
    events_per_group: int
    layer_count: int
    context_layer_correlation: str
    focal_learner_layer_identity: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PopulationInterval:
    estimate: float
    lower: float
    upper: float
    method: str
    group_count: int
    declared_positive: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def load_stage1_contract(path: str | Path) -> dict[str, object]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if value.get("contract_id") != "n2-stratified-context-transfer-failure-mode-stage1-v1":
        raise ValueError("unexpected N2 stage-1 contract")
    if value.get("status") != "pre_result_frozen":
        raise ValueError("N2 stage-1 contract is not frozen pre-result")
    return value


def layer_scores(layer_count: int) -> np.ndarray:
    if layer_count < 2:
        raise ValueError("layer_count must be >= 2")
    values = np.linspace(-1.0, 1.0, int(layer_count), dtype=float)
    values -= float(np.mean(values))
    scale = float(np.sqrt(np.mean(values * values)))
    return values / scale


def group_layer_indices(group_count: int, layer_count: int) -> np.ndarray:
    if group_count < 2 * layer_count:
        raise ValueError("structural eligibility requires group_count >= 2 * layer_count")
    base, extra = divmod(int(group_count), int(layer_count))
    values: list[int] = []
    for layer in range(int(layer_count)):
        values.extend([layer] * (base + (1 if layer < extra else 0)))
    return np.asarray(values, dtype=int)


def scenario_grid(contract: Mapping[str, object]) -> tuple[Stage1Scenario, ...]:
    design = contract["factorial_design"]
    keys = (
        "layer_effect_scale",
        "within_layer_context_effect",
        "group_count",
        "events_per_group",
        "layer_count",
        "context_layer_correlation",
        "focal_learner_layer_identity",
    )
    result: list[Stage1Scenario] = []
    for values in itertools.product(*(design[key] for key in keys)):
        row = dict(zip(keys, values))
        if int(row["group_count"]) < 2 * int(row["layer_count"]):
            continue
        result.append(
            Stage1Scenario(
                layer_effect_scale=float(row["layer_effect_scale"]),
                within_layer_context_effect=float(row["within_layer_context_effect"]),
                group_count=int(row["group_count"]),
                events_per_group=int(row["events_per_group"]),
                layer_count=int(row["layer_count"]),
                context_layer_correlation=str(row["context_layer_correlation"]),
                focal_learner_layer_identity=str(row["focal_learner_layer_identity"]),
            )
        )
    return tuple(result)


def _sigmoid(value: np.ndarray) -> np.ndarray:
    value = np.asarray(value, dtype=float)
    result = np.empty_like(value)
    positive = value >= 0
    result[positive] = 1.0 / (1.0 + np.exp(-value[positive]))
    exp_value = np.exp(value[~positive])
    result[~positive] = exp_value / (1.0 + exp_value)
    return result


def _log_score(probability: np.ndarray, y: np.ndarray) -> np.ndarray:
    p = np.asarray(probability, dtype=float)
    labels = np.asarray(y, dtype=float)
    if np.any(~np.isfinite(p)) or np.any((p <= 0.0) | (p >= 1.0)):
        raise ValueError("log-score probability must lie strictly between zero and one")
    return labels * np.log(p) + (1.0 - labels) * np.log1p(-p)


def _log_likelihood(design: np.ndarray, y: np.ndarray, coef: np.ndarray) -> float:
    eta = design @ coef
    return float(np.sum(y * (-np.logaddexp(0.0, -eta)) + (1.0 - y) * (-np.logaddexp(0.0, eta))))


def _fit_logistic(
    design: np.ndarray,
    y: np.ndarray,
    *,
    tolerance: float = 1e-9,
    max_iterations: int = 100,
) -> np.ndarray | None:
    X = np.asarray(design, dtype=float)
    labels = np.asarray(y, dtype=float)
    if X.ndim != 2 or labels.shape != (X.shape[0],) or X.shape[0] == 0:
        raise ValueError("invalid logistic fit inputs")
    if np.any(~np.isfinite(X)) or np.any((labels != 0.0) & (labels != 1.0)):
        raise ValueError("invalid logistic fit data")
    if float(np.min(labels)) == float(np.max(labels)):
        return None

    coef = np.zeros(X.shape[1], dtype=float)
    previous = _log_likelihood(X, labels, coef)
    for _ in range(int(max_iterations)):
        eta = X @ coef
        p = _sigmoid(eta)
        weight = p * (1.0 - p)
        if np.any(weight < 1e-14):
            weight = np.maximum(weight, 1e-14)
        gradient = X.T @ (labels - p)
        information = X.T @ (weight[:, None] * X)
        try:
            step = np.linalg.solve(information, gradient)
        except np.linalg.LinAlgError:
            return None
        if not np.all(np.isfinite(step)):
            return None

        scale = 1.0
        accepted = False
        candidate = coef
        candidate_ll = previous
        for _ in range(25):
            proposal = coef + scale * step
            if np.max(np.abs(proposal)) > 40.0:
                scale *= 0.5
                continue
            proposal_ll = _log_likelihood(X, labels, proposal)
            if math.isfinite(proposal_ll) and proposal_ll >= previous - 1e-10:
                candidate = proposal
                candidate_ll = proposal_ll
                accepted = True
                break
            scale *= 0.5
        if not accepted:
            return None
        coef = candidate
        if np.max(np.abs(scale * step)) <= tolerance:
            if np.max(np.abs(X.T @ (labels - _sigmoid(X @ coef)))) <= 1e-6:
                return coef
        previous = candidate_ll
    return None


def _pooled_probability(y: np.ndarray) -> float | None:
    value = float(np.mean(y))
    if not 0.0 < value < 1.0:
        return None
    return value


def _layer_probabilities(y: np.ndarray, layer: np.ndarray, layer_count: int) -> np.ndarray | None:
    result = np.empty(int(layer_count), dtype=float)
    for index in range(int(layer_count)):
        local = y[layer == index]
        if local.size == 0:
            return None
        value = float(np.mean(local))
        if not 0.0 < value < 1.0:
            return None
        result[index] = value
    return result


def _design_layer_context(layer: np.ndarray, x: np.ndarray, layer_count: int) -> np.ndarray:
    onehot = np.zeros((layer.size, int(layer_count)), dtype=float)
    onehot[np.arange(layer.size), layer] = 1.0
    return np.column_stack([onehot, x])


def _design_context_only(x: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones(x.size, dtype=float), x])


def _balanced_row_folds(rng: np.random.Generator, n: int, folds: int = 5) -> np.ndarray:
    order = rng.permutation(n)
    result = np.empty(n, dtype=int)
    result[order] = np.arange(n, dtype=int) % int(folds)
    return result


def _group_folds(group_layer: np.ndarray, folds: int = 5) -> np.ndarray:
    result = np.empty(group_layer.size, dtype=int)
    start = 0
    for layer in sorted(set(group_layer.tolist())):
        ids = np.flatnonzero(group_layer == layer)
        for offset, group in enumerate(ids.tolist()):
            result[group] = int((start + offset) % folds)
        start = int((start + ids.size) % folds)
    return result


def _auc(y: np.ndarray, score: np.ndarray) -> float | None:
    labels = np.asarray(y, dtype=int)
    values = np.asarray(score, dtype=float)
    positives = int(np.sum(labels == 1))
    negatives = int(np.sum(labels == 0))
    if positives == 0 or negatives == 0:
        return None
    order = np.argsort(values, kind="mergesort")
    sorted_values = values[order]
    ranks = np.empty(values.size, dtype=float)
    start = 0
    while start < values.size:
        end = start + 1
        while end < values.size and sorted_values[end] == sorted_values[start]:
            end += 1
        mean_rank = 0.5 * ((start + 1) + end)
        ranks[order[start:end]] = mean_rank
        start = end
    rank_sum = float(np.sum(ranks[labels == 1]))
    return (rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)


def _population_intervals_many(
    values_by_name: Mapping[str, Sequence[float]],
    *,
    confidence_level: float,
    bootstrap_draws: int,
    seed: int,
    switch_threshold: int,
) -> dict[str, PopulationInterval]:
    arrays = {
        name: np.asarray(values, dtype=float)
        for name, values in values_by_name.items()
    }
    if not arrays:
        raise ValueError("at least one population metric is required")
    sizes = {value.size for value in arrays.values()}
    if len(sizes) != 1:
        raise ValueError("paired population metrics must use the same groups")
    group_count = sizes.pop()
    if group_count < 2 or any(
        value.ndim != 1 or not np.all(np.isfinite(value))
        for value in arrays.values()
    ):
        raise ValueError("population interval requires at least two finite group values")

    alpha = 1.0 - float(confidence_level)
    result: dict[str, PopulationInterval] = {}
    if group_count < int(switch_threshold):
        df = int(group_count - 1)
        if confidence_level != 0.95 or df not in _T95:
            raise ValueError("small-group Student t table supports frozen 95% rule only")
        for name, data in arrays.items():
            estimate = float(np.mean(data))
            se = float(np.std(data, ddof=1) / math.sqrt(group_count))
            half = _T95[df] * se
            lower = estimate - half
            upper = estimate + half
            result[name] = PopulationInterval(
                estimate=estimate,
                lower=float(lower),
                upper=float(upper),
                method=f"student_t_df_{df}",
                group_count=int(group_count),
                declared_positive=bool(lower > 0.0),
            )
        return result

    rng = np.random.default_rng(int(seed))
    weights = rng.multinomial(
        int(group_count),
        np.full(int(group_count), 1.0 / float(group_count)),
        size=int(bootstrap_draws),
    ).astype(float)
    weights /= float(group_count)
    names = list(arrays)
    matrix = np.column_stack([arrays[name] for name in names])
    bootstrap_means = weights @ matrix
    lower = np.quantile(bootstrap_means, alpha / 2.0, axis=0)
    upper = np.quantile(bootstrap_means, 1.0 - alpha / 2.0, axis=0)
    estimate = np.mean(matrix, axis=0)
    for index, name in enumerate(names):
        result[name] = PopulationInterval(
            estimate=float(estimate[index]),
            lower=float(lower[index]),
            upper=float(upper[index]),
            method=f"group_percentile_bootstrap_{int(bootstrap_draws)}",
            group_count=int(group_count),
            declared_positive=bool(lower[index] > 0.0),
        )
    return result


def _population_interval(
    values: Sequence[float],
    *,
    confidence_level: float,
    bootstrap_draws: int,
    seed: int,
    switch_threshold: int,
) -> PopulationInterval:
    return _population_intervals_many(
        {"value": values},
        confidence_level=confidence_level,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
        switch_threshold=switch_threshold,
    )["value"]

def _simulate_world(
    scenario: Stage1Scenario,
    *,
    seed: int,
    intercept: float,
    rho_correlated: float,
) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(int(seed))
    group_layer = group_layer_indices(scenario.group_count, scenario.layer_count)
    z = layer_scores(scenario.layer_count)
    group = np.repeat(np.arange(scenario.group_count, dtype=int), scenario.events_per_group)
    layer = group_layer[group]
    epsilon = rng.normal(size=group.size)
    rho = 0.0 if scenario.context_layer_correlation == "none" else float(rho_correlated)
    x = rho * z[layer] + math.sqrt(1.0 - rho * rho) * epsilon
    eta = (
        float(intercept)
        + scenario.layer_effect_scale * z[layer]
        + scenario.within_layer_context_effect * x
    )
    p = _sigmoid(eta)
    y = (rng.random(group.size) < p).astype(float)
    return {
        "group": group,
        "layer": layer,
        "x": x,
        "y": y,
        "true_probability": p,
        "row_fold": _balanced_row_folds(rng, group.size, 5),
        "group_fold": _group_folds(group_layer, 5),
        "group_layer": group_layer,
    }


def _cross_validated_predictions(
    world: Mapping[str, np.ndarray],
    scenario: Stage1Scenario,
    *,
    validation: str,
) -> dict[str, np.ndarray] | None:
    group = world["group"]
    layer = world["layer"]
    x = world["x"]
    y = world["y"]
    if validation == "random_row_cv":
        row_fold = world["row_fold"]
    elif validation == "group_cv":
        row_fold = world["group_fold"][group]
    else:
        raise ValueError("unknown validation mode")

    outputs = {
        "pooled": np.full(y.size, np.nan, dtype=float),
        "layer": np.full(y.size, np.nan, dtype=float),
        "full": np.full(y.size, np.nan, dtype=float),
        "focal": np.full(y.size, np.nan, dtype=float),
        "majority": np.full(y.size, np.nan, dtype=float),
    }

    for fold in sorted(set(row_fold.tolist())):
        test = row_fold == fold
        if not np.any(test):
            continue
        train = ~test
        pooled = _pooled_probability(y[train])
        layer_probability = _layer_probabilities(y[train], layer[train], scenario.layer_count)
        if pooled is None or layer_probability is None:
            return None

        full_design_train = _design_layer_context(
            layer[train], x[train], scenario.layer_count
        )
        full_coef = _fit_logistic(full_design_train, y[train])
        if full_coef is None:
            return None
        full_test = _sigmoid(
            _design_layer_context(layer[test], x[test], scenario.layer_count) @ full_coef
        )

        if scenario.focal_learner_layer_identity == "included":
            focal_test = full_test
        else:
            focal_coef = _fit_logistic(_design_context_only(x[train]), y[train])
            if focal_coef is None:
                return None
            focal_test = _sigmoid(_design_context_only(x[test]) @ focal_coef)

        outputs["pooled"][test] = pooled
        outputs["layer"][test] = layer_probability[layer[test]]
        outputs["full"][test] = full_test
        outputs["focal"][test] = focal_test
        outputs["majority"][test] = float(pooled >= 0.5)

    if any(np.any(~np.isfinite(value)) for value in outputs.values()):
        return None
    return outputs


def _group_means(values: np.ndarray, group: np.ndarray, group_count: int) -> np.ndarray:
    return np.asarray(
        [float(np.mean(values[group == index])) for index in range(int(group_count))],
        dtype=float,
    )


def _metrics_from_predictions(
    world: Mapping[str, np.ndarray],
    prediction: Mapping[str, np.ndarray] | None,
    scenario: Stage1Scenario,
) -> dict[str, object]:
    if prediction is None:
        return {"available": False}
    group = world["group"]
    y = world["y"]
    pooled_score = _log_score(prediction["pooled"], y)
    layer_score = _log_score(prediction["layer"], y)
    full_score = _log_score(prediction["full"], y)
    focal_score = _log_score(prediction["focal"], y)

    pooled_gain = _group_means(
        focal_score - pooled_score, group, scenario.group_count
    )
    layer_component = _group_means(
        layer_score - pooled_score, group, scenario.group_count
    )
    context_component = _group_means(
        full_score - layer_score, group, scenario.group_count
    )
    identity_error = float(
        np.max(
            np.abs(
                _group_means(full_score - pooled_score, group, scenario.group_count)
                - layer_component
                - context_component
            )
        )
    )

    accuracy = np.empty(scenario.group_count, dtype=float)
    accuracy_gain = np.empty(scenario.group_count, dtype=float)
    auc = np.full(scenario.group_count, np.nan, dtype=float)
    focal_class = prediction["focal"] >= 0.5
    majority_class = prediction["majority"] >= 0.5
    for index in range(scenario.group_count):
        mask = group == index
        accuracy[index] = float(np.mean(focal_class[mask] == y[mask]))
        reference_accuracy = float(np.mean(majority_class[mask] == y[mask]))
        accuracy_gain[index] = accuracy[index] - reference_accuracy
        value = _auc(y[mask], prediction["focal"][mask])
        if value is not None:
            auc[index] = value - 0.5

    return {
        "available": True,
        "pooled_gain": pooled_gain,
        "layer_component": layer_component,
        "context_component": context_component,
        "identity_error": identity_error,
        "auc_minus_half": auc,
        "accuracy_gain": accuracy_gain,
    }


def oracle_information_targets(
    scenario: Stage1Scenario,
    *,
    intercept: float,
    rho_correlated: float,
    quadrature_nodes: int = 60,
) -> dict[str, float]:
    z = layer_scores(scenario.layer_count)
    layer_index = group_layer_indices(scenario.group_count, scenario.layer_count)
    weights = np.bincount(layer_index, minlength=scenario.layer_count).astype(float)
    weights /= float(np.sum(weights))
    rho = 0.0 if scenario.context_layer_correlation == "none" else float(rho_correlated)
    nodes, node_weight = np.polynomial.hermite.hermgauss(int(quadrature_nodes))
    standard = math.sqrt(2.0) * nodes
    normalized_weight = node_weight / math.sqrt(math.pi)
    context_gain = 0.0
    layer_probability = np.empty(scenario.layer_count, dtype=float)

    for index in range(scenario.layer_count):
        x = rho * z[index] + math.sqrt(1.0 - rho * rho) * standard
        p = _sigmoid(
            intercept
            + scenario.layer_effect_scale * z[index]
            + scenario.within_layer_context_effect * x
        )
        marginal = float(np.sum(normalized_weight * p))
        layer_probability[index] = marginal
        if scenario.within_layer_context_effect != 0.0:
            kl = p * np.log(p / marginal) + (1.0 - p) * np.log(
                (1.0 - p) / (1.0 - marginal)
            )
            context_gain += float(weights[index] * np.sum(normalized_weight * kl))

    pooled = float(np.sum(weights * layer_probability))
    kl_layer = layer_probability * np.log(layer_probability / pooled) + (
        1.0 - layer_probability
    ) * np.log((1.0 - layer_probability) / (1.0 - pooled))
    layer_gain = float(np.sum(weights * kl_layer))
    return {
        "context_gain": float(context_gain),
        "layer_gain": layer_gain,
        "total_gain": float(context_gain + layer_gain),
    }


def run_world(
    scenario: Stage1Scenario,
    *,
    seed: int,
    contract: Mapping[str, object],
    bootstrap_draws: int,
) -> dict[str, object]:
    dgp = contract["data_generating_process"]
    rule = contract["population_decision_rule"]
    world = _simulate_world(
        scenario,
        seed=seed,
        intercept=float(dgp["intercept"]),
        rho_correlated=float(dgp["context_generation"]["rho_when_correlated"]),
    )
    random_prediction = _cross_validated_predictions(
        world, scenario, validation="random_row_cv"
    )
    group_prediction = _cross_validated_predictions(
        world, scenario, validation="group_cv"
    )
    random_metrics = _metrics_from_predictions(world, random_prediction, scenario)
    group_metrics = _metrics_from_predictions(world, group_prediction, scenario)

    result: dict[str, object] = {
        "seed": int(seed),
        "random_row_cv_available": bool(random_metrics["available"]),
        "group_cv_available": bool(group_metrics["available"]),
    }
    if not group_metrics["available"]:
        return result

    if float(group_metrics["identity_error"]) > float(
        contract["score_definitions"]["required_additivity_tolerance"]
    ):
        raise AssertionError("group-CV additive score identity failed")

    interval_seed_base = int(seed) * 100
    switch = int(rule["interval"]["switch_threshold_group_count"])
    confidence = float(rule["confidence_level"])
    paired_values: dict[str, Sequence[float]] = {
        "group_cv_pooled_log_gain": group_metrics["pooled_gain"],
        "group_cv_layer_decomposed_context_gain": group_metrics["context_component"],
        "group_cv_layer_component": group_metrics["layer_component"],
        "group_cv_accuracy": group_metrics["accuracy_gain"],
    }
    if random_metrics["available"]:
        paired_values["random_row_cv_pooled_log_gain"] = random_metrics["pooled_gain"]
        paired_values["random_row_cv_accuracy"] = random_metrics["accuracy_gain"]
    paired_intervals = _population_intervals_many(
        paired_values,
        confidence_level=confidence,
        bootstrap_draws=int(bootstrap_draws),
        seed=interval_seed_base + 1,
        switch_threshold=switch,
    )
    for name, interval in paired_intervals.items():
        result[name] = interval.as_dict()
    primary = paired_intervals["group_cv_pooled_log_gain"]
    if "random_row_cv_pooled_log_gain" in paired_intervals:
        result["random_row_minus_group_cv_optimism"] = float(
            paired_intervals["random_row_cv_pooled_log_gain"].estimate
            - primary.estimate
        )
    result["group_cv_identity_error"] = float(group_metrics["identity_error"])

    auc_values = np.asarray(group_metrics["auc_minus_half"], dtype=float)
    auc_finite = np.isfinite(auc_values)
    result["group_cv_auc_estimable_fraction"] = float(np.mean(auc_finite))
    if int(np.sum(auc_finite)) >= 2:
        auc_interval = _population_interval(
            auc_values[auc_finite],
            confidence_level=confidence,
            bootstrap_draws=int(bootstrap_draws),
            seed=interval_seed_base + 2,
            switch_threshold=switch,
        )
        result["group_cv_auc"] = auc_interval.as_dict()

    if random_metrics["available"]:
        random_auc = np.asarray(random_metrics["auc_minus_half"], dtype=float)
        random_auc_finite = np.isfinite(random_auc)
        result["random_row_cv_auc_estimable_fraction"] = float(
            np.mean(random_auc_finite)
        )
        if int(np.sum(random_auc_finite)) >= 2:
            random_auc_interval = _population_interval(
                random_auc[random_auc_finite],
                confidence_level=confidence,
                bootstrap_draws=int(bootstrap_draws),
                seed=interval_seed_base + 3,
                switch_threshold=switch,
            )
            result["random_row_cv_auc"] = random_auc_interval.as_dict()
    return result


def _wilson_bounds(successes: int, n: int, confidence_level: float = 0.95) -> tuple[float, float]:
    if n <= 0:
        return (float("nan"), float("nan"))
    alpha = 1.0 - confidence_level
    z = NormalDist().inv_cdf(1.0 - alpha / 2.0)
    p = successes / n
    denominator = 1.0 + z * z / n
    centre = p + z * z / (2.0 * n)
    radius = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))
    return (
        float(max(0.0, (centre - radius) / denominator)),
        float(min(1.0, (centre + radius) / denominator)),
    )


def summarize_replicates(
    scenario: Stage1Scenario,
    worlds: Sequence[Mapping[str, object]],
    *,
    contract: Mapping[str, object],
) -> dict[str, object]:
    planned = len(worlds)
    oracle = oracle_information_targets(
        scenario,
        intercept=float(contract["data_generating_process"]["intercept"]),
        rho_correlated=float(
            contract["data_generating_process"]["context_generation"]["rho_when_correlated"]
        ),
    )

    def method_summary(key: str) -> dict[str, object]:
        available = [row for row in worlds if key in row]
        declarations = sum(bool(row[key]["declared_positive"]) for row in available)
        lower, upper = _wilson_bounds(declarations, planned)
        estimates = [float(row[key]["estimate"]) for row in available]
        return {
            "planned_replicates": planned,
            "available_replicates": len(available),
            "availability_fraction": len(available) / planned if planned else 0.0,
            "positive_declaration_count": declarations,
            "positive_declaration_rate": declarations / planned if planned else 0.0,
            "positive_declaration_wilson_95_lower": lower,
            "positive_declaration_wilson_95_upper": upper,
            "mean_estimate": float(np.mean(estimates)) if estimates else None,
            "mean_interval_width": float(
                np.mean(
                    [
                        float(row[key]["upper"]) - float(row[key]["lower"])
                        for row in available
                    ]
                )
            )
            if available
            else None,
        }

    primary = method_summary("group_cv_pooled_log_gain")
    corrected = method_summary("group_cv_layer_decomposed_context_gain")
    layer = method_summary("group_cv_layer_component")
    if corrected["mean_estimate"] is not None:
        corrected["mean_bias_vs_oracle"] = float(
            corrected["mean_estimate"] - oracle["context_gain"]
        )
        corrected["absolute_mean_bias_nats_per_event"] = abs(
            corrected["mean_bias_vs_oracle"]
        )

    random = method_summary("random_row_cv_pooled_log_gain")
    optimism = [
        float(row["random_row_minus_group_cv_optimism"])
        for row in worlds
        if "random_row_minus_group_cv_optimism" in row
    ]
    auc = method_summary("group_cv_auc")
    accuracy = method_summary("group_cv_accuracy")
    random_auc = method_summary("random_row_cv_auc")
    random_accuracy = method_summary("random_row_cv_accuracy")
    auc_fraction = [
        float(row["group_cv_auc_estimable_fraction"])
        for row in worlds
        if "group_cv_auc_estimable_fraction" in row
    ]
    random_auc_fraction = [
        float(row["random_row_cv_auc_estimable_fraction"])
        for row in worlds
        if "random_row_cv_auc_estimable_fraction" in row
    ]

    return {
        "scenario": scenario.as_dict(),
        "oracle": oracle,
        "group_cv_pooled_log_gain": primary,
        "group_cv_layer_decomposed_context_gain": corrected,
        "group_cv_layer_component": layer,
        "random_row_cv_pooled_log_gain": random,
        "random_row_minus_group_cv_optimism": (
            float(np.mean(optimism)) if optimism else None
        ),
        "group_cv_auc": auc,
        "group_cv_accuracy": accuracy,
        "random_row_cv_auc": random_auc,
        "random_row_cv_accuracy": random_accuracy,
        "auc_estimable_group_fraction_mean": (
            float(np.mean(auc_fraction)) if auc_fraction else None
        ),
        "random_row_auc_estimable_group_fraction_mean": (
            float(np.mean(random_auc_fraction)) if random_auc_fraction else None
        ),
    }


def derive_seed(master_seed: int, namespace: str, index: int) -> int:
    import hashlib

    payload = f"{int(master_seed)}|{namespace}|{int(index)}".encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big") % (2**32 - 1)


def run_factorial_cells(
    contract: Mapping[str, object],
    *,
    cell_indices: Sequence[int],
) -> dict[str, object]:
    grid = scenario_grid(contract)
    design = contract["factorial_design"]
    master = int(contract["confirmatory_anchor_execution"]["master_seed"])
    replicates = int(design["replicates_per_factorial_cell"])
    draws = int(design["population_interval_bootstrap_draws_per_world"])
    cells = []
    for index in cell_indices:
        scenario = grid[int(index)]
        worlds = [
            run_world(
                scenario,
                seed=derive_seed(master, f"factorial:{index}", replicate),
                contract=contract,
                bootstrap_draws=draws,
            )
            for replicate in range(replicates)
        ]
        summary = summarize_replicates(scenario, worlds, contract=contract)
        summary["cell_index"] = int(index)
        cells.append(summary)
    return {
        "contract_id": contract["contract_id"],
        "contract_merge_sha": FROZEN_CONTRACT_MERGE_SHA,
        "result_role": "descriptive_factorial_shard",
        "cell_count": len(cells),
        "cells": cells,
    }


def _anchor_scenario(anchor: Mapping[str, object]) -> Stage1Scenario:
    return Stage1Scenario(
        layer_effect_scale=float(anchor["layer_effect_scale"]),
        within_layer_context_effect=float(anchor["within_layer_context_effect"]),
        group_count=int(anchor["group_count"]),
        events_per_group=int(anchor["events_per_group"]),
        layer_count=int(anchor["layer_count"]),
        context_layer_correlation=str(anchor["context_layer_correlation"]),
        focal_learner_layer_identity=str(anchor["focal_learner_layer_identity"]),
    )


def run_anchor_replicates(
    contract: Mapping[str, object],
    *,
    anchor_index: int,
    replicate_indices: Sequence[int],
) -> dict[str, object]:
    execution = contract["confirmatory_anchor_execution"]
    anchor = execution["anchors"][int(anchor_index)]
    scenario = _anchor_scenario(anchor)
    master = int(execution["master_seed"])
    draws = int(execution["bootstrap_draws_per_population_interval"])
    worlds = [
        run_world(
            scenario,
            seed=derive_seed(master, f"anchor:{anchor['anchor_id']}", replicate),
            contract=contract,
            bootstrap_draws=draws,
        )
        for replicate in replicate_indices
    ]
    return {
        "contract_id": contract["contract_id"],
        "contract_merge_sha": FROZEN_CONTRACT_MERGE_SHA,
        "result_role": "confirmatory_anchor_shard",
        "anchor_index": int(anchor_index),
        "anchor_id": anchor["anchor_id"],
        "replicate_indices": [int(value) for value in replicate_indices],
        "worlds": worlds,
    }


def bop_oracle_check(contract: Mapping[str, object]) -> dict[str, object]:
    calibration = contract["oracle_targets"]["bop_calibration"]
    scenario = Stage1Scenario(
        layer_effect_scale=float(calibration["anchor_layer_effect_scale"]),
        within_layer_context_effect=0.0,
        group_count=int(calibration["anchor_group_count"]),
        events_per_group=100,
        layer_count=int(calibration["anchor_layer_count"]),
        context_layer_correlation="none",
        focal_learner_layer_identity="included",
    )
    observed = oracle_information_targets(
        scenario,
        intercept=float(contract["data_generating_process"]["intercept"]),
        rho_correlated=float(
            contract["data_generating_process"]["context_generation"]["rho_when_correlated"]
        ),
    )["layer_gain"]
    expected = float(
        calibration[
            "deterministic_oracle_layer_gain_nats_under_balanced_30_group_allocation"
        ]
    )
    return {
        "observed_layer_gain": observed,
        "frozen_expected_layer_gain": expected,
        "absolute_error": abs(observed - expected),
        "passed": abs(observed - expected) <= 1e-12,
    }
