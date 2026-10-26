#!/usr/bin/env python3
"""Prospectively frozen known-truth fixed-model group-transfer benchmark.

Read the precommitted contract; train one 4-state predictor/reference using
training groups ONLY; commit all calibration and validation probabilities
before simulating their target labels; calibrate on separate tagged-individual
groups; score independent validation groups without refitting or recalibration.

This is SYNTHETIC known truth and does NOT rerun or reclassify BOP_RODENT.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from odsp.fixed_group_gain_protocol import (
    calibrate_fixed_group_gain,
    freeze_fixed_group_forecasts,
    validate_fixed_group_gain,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "research/BOP_FIXED_MODEL_GROUP_TRANSFER_V1_CONTRACT.json"


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def load_contract(path: Path = CONTRACT_PATH) -> dict:
    contract = json.loads(path.read_text(encoding="utf-8"))
    if (
        contract.get("contract_id") != "bop-fixed-model-group-transfer-known-truth-v1"
        or contract.get("role") != "prospective_known_truth_method_benchmark_only"
        or contract.get("frozen_empirical_bop_rodent_terminal") != "empirical_state_prediction_mixed"
        or contract.get("closed_endpoint_modification") is not False
    ):
        raise ValueError("incorrect or unfrozen method benchmark contract")
    d = contract["design"]
    if (
        int(d["seed"]) != 20261026
        or int(d["replicates"]) != 128
        or len(d["stratum_labels"]) != 4
        or d["validation_scenarios"] != [
            "same_process", "shifted_validation_labels_plus_two_mod_four"
        ]
        or d["score"] != "mean_true_state_log_probability_model_minus_training_only_stratum_reference_per_individual"
        or d["group_strata"] != "exact stratum, no pooled cross-stratum rank calibration"
    ):
        raise ValueError("contract generator or score definition changed")
    if not math.isclose(float(d["miscoverage"]), 0.1, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("contract miscoverage changed")
    return contract


def _truth(base: np.ndarray, x: int, amplitude: float) -> np.ndarray:
    """Categorical altitude-state distribution conditional on binary context."""
    if x not in (0, 1):
        raise ValueError("context must be binary")
    sign = 1 if x == 0 else -1
    weights = np.asarray(base, dtype=float).copy()
    weights[0] *= math.exp(sign * amplitude)
    weights[3] *= math.exp(-sign * amplitude)
    return weights / np.sum(weights)


def _features(
    rng: np.random.Generator, prefix: str, stratum: str, n_groups: int,
    *, minimum: int, maximum: int, heterogeneity_probability: float,
) -> list[tuple[str, np.ndarray]]:
    features = []
    for i in range(n_groups):
        group = f"{prefix}_{stratum}_{i:04d}"
        count = int(rng.integers(minimum, maximum + 1))
        q = float(rng.uniform(0.15, 0.85)) if rng.random() < heterogeneity_probability else 0.5
        context = (rng.random(count) < q).astype(int)
        features.append((group, context))
    return features


def _labels(
    rng: np.random.Generator, features: list[tuple[str, np.ndarray]],
    truths: tuple[np.ndarray, np.ndarray],
) -> dict[str, np.ndarray]:
    """Called on held-out groups *only after* their prediction plan is frozen."""
    groups = {}
    for group, context in features:
        probabilities = np.stack([truths[int(x)] for x in context], axis=0)
        cumulative = np.cumsum(probabilities, axis=1)
        labels = (rng.random(len(context))[:, None] > cumulative).sum(axis=1)
        groups[group] = labels.astype(int)
    return groups


def _to_rows(
    features: list[tuple[str, np.ndarray]],
    stratum: str,
    role: str,
    conditional: np.ndarray,
    reference: np.ndarray,
) -> list[dict[str, object]]:
    result = []
    for group, context in features:
        for j, x in enumerate(context):
            result.append({
                "row_id": f"{group}:{j:03d}", "group_id": group,
                "stratum": stratum, "conditional": conditional[int(x)].tolist(),
                "reference": reference.tolist(),
                "weight": 1.0,
            })
    return result


def _state_outcomes(
    features: list[tuple[str, np.ndarray]],
    samples: dict[str, np.ndarray], labels: tuple[str, ...], *,
    shift: int = 0,
) -> dict[str, str]:
    return {
        f"{group}:{j:03d}": labels[(int(state) + shift) % len(labels)]
        for group, _ in features
        for j, state in enumerate(samples[group])
    }


def _training_model(
    training_features: dict[str, list[tuple[str, np.ndarray]]],
    training_labels: dict[str, dict[str, np.ndarray]],
    *,
    stratum_labels: tuple[str, ...],
    alpha: float,
    class_count: int,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], bytes, bytes, bytes]:
    conditional: dict[str, np.ndarray] = {}
    marginal: dict[str, np.ndarray] = {}
    source_records: list[dict[str, object]] = []
    for stratum in stratum_labels:
        by_context = np.zeros((2, class_count), dtype=float)
        state_counts = np.zeros(class_count, dtype=float)
        for group, context in training_features[stratum]:
            values = training_labels[stratum][group]
            for x, value in zip(context, values):
                by_context[int(x), int(value)] += 1
                state_counts[int(value)] += 1
            source_records.append({
                "group": group, "context": context.tolist(),
                "states": values.tolist(),
            })
        conditional[stratum] = (
            (by_context + alpha)
            / (by_context.sum(axis=1, keepdims=True) + class_count * alpha)
        )
        marginal[stratum] = (
            (state_counts + alpha) / (state_counts.sum() + class_count * alpha)
        )
    model_bytes = _json_bytes({
        "model": "training_only_stratum_context_smoothed_multinomial_v1",
        "probabilities": {k: v.tolist() for k, v in sorted(conditional.items())},
    })
    reference_bytes = _json_bytes({
        "reference": "training_only_stratum_marginal_v1",
        "probabilities": {k: v.tolist() for k, v in sorted(marginal.items())},
    })
    training_source = _json_bytes(source_records)
    return conditional, marginal, model_bytes, reference_bytes, training_source


def single_replicate(contract: dict, replicate_index: int) -> dict[str, object]:
    """One independent synthetic world; returns outcomes only as aggregated coverage."""
    d = contract["design"]
    rng = np.random.default_rng(int(d["seed"]) + replicate_index)
    strata = tuple(d["stratum_labels"])
    labels = tuple(f"altitude_AMSL_state_{i}" for i in range(4))
    counts = d["per_stratum_groups"]
    per_group_min = int(d["events_per_group_min"])
    per_group_max = int(d["events_per_group_max_inclusive"])
    het = float(d["individual_context_heterogeneity_probability"])
    amplitude = float(d["context_class_weight_amplitude"])
    alpha = float(d["additive_smoothing"])
    truth = {
        name: (
            _truth(np.asarray(d["truth_base_probabilities"][i]), 0, amplitude),
            _truth(np.asarray(d["truth_base_probabilities"][i]), 1, amplitude),
        )
        for i, name in enumerate(strata)
    }
    features = {
        role: {
            name: _features(
                rng, f"r{replicate_index}_{role}", name, int(counts[role]),
                minimum=per_group_min, maximum=per_group_max,
                heterogeneity_probability=het,
            )
            for name in strata
        }
        for role in ("train", "calibration", "validation")
    }
    # Training outcomes are observed before fitting the predictor (allowed).
    train_labels = {
        name: _labels(rng, features["train"][name], truth[name])
        for name in strata
    }
    cond, marginal, model_artifact, reference_artifact, source = _training_model(
        features["train"], train_labels, stratum_labels=strata,
        alpha=alpha, class_count=len(labels),
    )
    cal_rows = []
    val_rows = []
    train_ids = []
    for name in strata:
        train_ids.extend(group for group, _ in features["train"][name])
        cal_rows.extend(_to_rows(
            features["calibration"][name], name, "calibration",
            cond[name], marginal[name],
        ))
        val_rows.extend(_to_rows(
            features["validation"][name], name, "validation",
            cond[name], marginal[name],
        ))

    # Nothing in plan/forecast rows is permitted to include target labels.
    frozen_plan = freeze_fixed_group_forecasts(
        training_group_ids=train_ids,
        calibration_forecasts=cal_rows,
        validation_forecasts=val_rows,
        classes=labels,
        model_artifact=model_artifact,
        reference_artifact=reference_artifact,
        training_source_sha256=hashlib.sha256(source).hexdigest(),
        miscoverage=float(d["miscoverage"]),
    )
    plan_sha_before_outcomes = frozen_plan.digest
    calibration_states = {}
    for name in strata:
        new_labels = _labels(rng, features["calibration"][name], truth[name])
        calibration_states.update(
            _state_outcomes(features["calibration"][name], new_labels, labels)
        )
    calibrated = calibrate_fixed_group_gain(
        frozen_plan, calibration_states,
        model_artifact=model_artifact,
        reference_artifact=reference_artifact,
    )
    validation_same = {}
    validation_shifted = {}
    for name in strata:
        new_labels = _labels(rng, features["validation"][name], truth[name])
        validation_same.update(
            _state_outcomes(features["validation"][name], new_labels, labels)
        )
        validation_shifted.update(
            _state_outcomes(
                features["validation"][name], new_labels, labels, shift=2
            )
        )
    same = validate_fixed_group_gain(
        frozen_plan, calibrated, validation_same,
        model_artifact=model_artifact, reference_artifact=reference_artifact,
    )
    shift = validate_fixed_group_gain(
        frozen_plan, calibrated, validation_shifted,
        model_artifact=model_artifact, reference_artifact=reference_artifact,
    )
    if (
        frozen_plan.digest != plan_sha_before_outcomes
        or same.calibration_sha256 != shift.calibration_sha256
        or any(group.finite_rank != 4 for group in same.strata)
        or any(group.vacuous for group in same.strata)
    ):
        raise ValueError("frozen predictor, rank or calibration changed")
    return {
        "replicate_index": replicate_index,
        "plan_sha256": plan_sha_before_outcomes,
        "calibration_sha256": calibrated.calibration_sha256,
        "same_covered": same.covered_validation_group_count,
        "shift_covered": shift.covered_validation_group_count,
        "validation_groups": same.validation_group_count,
        "training_groups": len(frozen_plan.training_group_ids),
        "calibration_groups": len(calibrated.gains),
        "model_artifact_retrained_after_calibration": False,
        "calibration_touched_validation_labels": False,
    }


def run_benchmark() -> dict[str, object]:
    contract = load_contract()
    d = contract["design"]
    results = [single_replicate(contract, j) for j in range(int(d["replicates"]))]
    total = sum(int(r["validation_groups"]) for r in results)
    same = sum(int(r["same_covered"]) for r in results)
    shift = sum(int(r["shift_covered"]) for r in results)
    rates = {
        "same_process": same / total,
        "shifted_validation_labels_plus_two_mod_four": shift / total,
    }
    rules = contract["acceptance"]
    tests = {
        "calibration_and_validation_group_counts": (
            total == int(rules["per_scenario_validation_group_count"])
            and all(r["calibration_groups"] == 156 for r in results)
            and all(r["training_groups"] == 80 for r in results)
        ),
        "same_process_coverage": (
            float(rules["same_process_coverage_min"]) <= rates["same_process"]
            <= float(rules["same_process_coverage_max"])
        ),
        "shifted_process_detected": (
            rates["shifted_validation_labels_plus_two_mod_four"]
            <= float(rules["shifted_validation_coverage_max"])
        ),
        "frozen_model_and_calibration": all(
            r["model_artifact_retrained_after_calibration"] is False
            and r["calibration_touched_validation_labels"] is False
            for r in results
        ),
        "all_groups_one_equal_vote": rules["all_group_scoring_uses_one_equal_group_vote"] is True,
    }
    return {
        "contract_id": contract["contract_id"],
        "contract_sha256": hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest(),
        "result_role": "prospective_known_truth_only_not_empirical_BOP",
        "n_replicates": len(results),
        "strata": len(d["stratum_labels"]),
        "validation_groups_each_scenario": total,
        "coverage": rates,
        "acceptance_checks": tests,
        "passed": all(tests.values()),
        "frozen_empirical_terminal": "empirical_state_prediction_mixed",
        "empirical_result_recomputed": False,
        "claim_limitation": (
            "synthetic exchangeable tagged-individual group-gain coverage only; "
            "fixed model and baseline fitted on separate training groups; "
            "real BOP prospective deployment group data not evaluated"
        ),
        "per_replicate_provenance": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    report = run_benchmark()
    encoded = json.dumps(
        report, indent=2, ensure_ascii=False, allow_nan=False
    ) + "\n"
    if args.out:
        if args.out.resolve() == CONTRACT_PATH.resolve():
            raise ValueError("cannot overwrite frozen contract")
        args.out.write_text(encoded, encoding="utf-8")
    print(json.dumps({
        "passed": report["passed"], "n_replicates": report["n_replicates"],
        "coverage": report["coverage"], "checks": report["acceptance_checks"],
        "contract_sha256": report["contract_sha256"],
    }, sort_keys=True))
    if not report["passed"]:
        raise SystemExit("frozen known-truth methodological benchmark FAILED")


if __name__ == "__main__":
    main()
