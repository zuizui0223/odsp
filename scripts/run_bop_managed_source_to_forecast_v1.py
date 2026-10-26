#!/usr/bin/env python3
"""Frozen source-to-model-to-forecast known-truth audit for ODSP BOP methods.

No original BOP telemetry is accessed. All model and reference probabilities
are calculated by a deterministic learner on synthetic TRAINING individuals,
before calibration or validation labels are produced. It fails closed on
tampering and evaluates one gain per independent group, within each stratum.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from odsp.managed_group_forecast_v1 import (
    calibrate_managed_group_gain,
    freeze_managed_group_forecasts,
    validate_managed_group_gain,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "research/BOP_MANAGED_SOURCE_TO_FORECAST_V1_CONTRACT.json"


def load_contract(path: Path = CONTRACT_PATH) -> dict:
    c = json.loads(path.read_text(encoding="utf-8"))
    if (
        c.get("contract_id") != "bop-managed-source-model-forecast-v1-knowntruth"
        or c.get("role") != "prospective_known_truth_method_validation_not_real_BOP"
        or c.get("primary_immutable_terminal") != "empirical_state_prediction_mixed"
        or c.get("replicates") != 64
        or c.get("rng_seed") != 20261027
        or c.get("pseudocount") != 0.1
        or c.get("context_levels") != [0, 1]
        or c.get("target") != (
            "90% one-sided group gain lower rank prediction for one new "
            "individual within the same stratum; rank floor((39+1)*0.1)=4."
        )
        or c.get("independent_groups_per_stratum") != {
            "training": 20, "calibration": 39, "validation": 40
        }
    ):
        raise ValueError("managed-method benchmark contract changed")
    return c


def _p_state(base: list[float], context: int, amp: float) -> np.ndarray:
    raw = np.asarray(base, dtype=float).copy()
    sign = 1.0 if context == 0 else -1.0
    raw[0] *= math.exp(sign * amp)
    raw[-1] *= math.exp(-sign * amp)
    return raw / raw.sum()


def _features(
    rng: np.random.Generator, role: str, species: str, n: int, rep: int,
    min_n: int, max_n: int,
) -> list[dict[str, object]]:
    results = []
    for group_number in range(n):
        group = f"rep{rep}_role_{role}_{species}_{group_number:03d}"
        count = int(rng.integers(min_n, max_n + 1))
        frac = float(rng.uniform(0.1, 0.9))
        for event in range(count):
            results.append({
                "row_id": f"{group}_{event:03d}",
                "group_id": group,
                "stratum": species,
                "context": int(rng.random() < frac),
            })
    return results


def _sample_labels(
    rng: np.random.Generator, features: list[dict[str, object]],
    truth: dict[str, tuple[np.ndarray, np.ndarray]],
    classes: tuple[str, ...],
    shift: int = 0,
) -> dict[str, str]:
    outcomes = {}
    for row in features:
        p = truth[str(row["stratum"])][int(row["context"])]
        index = int(np.searchsorted(np.cumsum(p), rng.random(), side="right"))
        outcomes[str(row["row_id"])] = classes[(index + shift) % len(classes)]
    return outcomes


def run_world(contract: dict, rep: int) -> dict[str, object]:
    rng = np.random.default_rng(int(contract["rng_seed"]) + rep)
    strata = tuple(contract["independent_strata"])
    classes = tuple(contract["state_labels"])
    truth = {
        name: (
            _p_state(contract["true_base_probabilities"][i], 0, float(contract["context_amplitude"])),
            _p_state(contract["true_base_probabilities"][i], 1, float(contract["context_amplitude"])),
        )
        for i, name in enumerate(strata)
    }
    settings = contract["independent_groups_per_stratum"]
    all_features: dict[str, list[dict[str, object]]] = {
        role: [] for role in settings
    }
    for role in ("training", "calibration", "validation"):
        for stratum in strata:
            all_features[role].extend(
                _features(
                    rng, role, stratum, int(settings[role]), rep,
                    int(contract["group_event_count_min"]),
                    int(contract["group_event_count_max"]),
                )
            )

    # ONLY training observations can be read before model and forecasts freeze.
    training_outcomes = _sample_labels(
        rng, all_features["training"], truth, classes
    )
    training_rows = [
        {**row, "outcome": training_outcomes[row["row_id"]]}
        for row in all_features["training"]
    ]
    frozen = freeze_managed_group_forecasts(
        training_rows=training_rows,
        calibration_features=all_features["calibration"],
        validation_features=all_features["validation"],
        classes=classes,
        pseudocount=float(contract["pseudocount"]),
        miscoverage=0.1,
    )
    source_to_forecast = frozen.public_manifest()
    if (
        source_to_forecast["training_source_to_model_replay_verified"] is not True
        or source_to_forecast["artifact_to_forecast_replay_verified"] is not True
        or source_to_forecast["outcomes_accessed_by_freeze"] is not False
    ):
        raise ValueError("source/model/forecast provenance not validated")

    # Open calibration labels only after model bytes and calibration/validation
    # feature/prediction hashes have been set.
    cal_outcomes = _sample_labels(
        rng, all_features["calibration"], truth, classes
    )
    cal = calibrate_managed_group_gain(frozen, cal_outcomes)

    # Newly simulated independent validation outcomes are opened after
    # calibration; shift scenario is the same true label rotated by two.
    val_outcomes = _sample_labels(
        rng, all_features["validation"], truth, classes
    )
    shifted = {
        row_id: classes[(classes.index(label) + 2) % len(classes)]
        for row_id, label in val_outcomes.items()
    }
    score = validate_managed_group_gain(frozen, cal, val_outcomes)
    shift_score = validate_managed_group_gain(frozen, cal, shifted)
    expected_cal_count = len(strata)*int(settings["calibration"])
    expected_test_count = len(strata)*int(settings["validation"])
    if (
        score.validation_group_count != expected_test_count
        or shift_score.validation_group_count != expected_test_count
        or sum(s.calibration_group_count for s in score.strata) != expected_cal_count
        or any(s.finite_rank != 4 for s in score.strata)
        or any(s.vacuous for s in score.strata)
        or score.plan_sha256 != shift_score.plan_sha256
        or score.calibration_sha256 != shift_score.calibration_sha256
    ):
        raise ValueError("predeclared group count, rank or frozen calibration mismatch")
    return {
        "world_index": rep,
        "plan_sha256": frozen.plan.digest,
        "training_source_sha256": frozen.plan.training_source_sha256,
        "model_sha256": frozen.plan.model_sha256,
        "reference_sha256": frozen.plan.reference_sha256,
        "feature_roster_sha256": frozen.feature_sha256,
        "calibration_sha256": cal.calibration_sha256,
        "training_groups": source_to_forecast["training_group_count"],
        "calibration_groups": expected_cal_count,
        "validation_groups": expected_test_count,
        "same_covered": score.covered_validation_group_count,
        "shift_covered": shift_score.covered_validation_group_count,
        "trained_only_before_calibration": True,
        "generated_forecasts_directly_from_model_artifacts": True,
        "validation_labels_not_used_to_adjust_model_or_calibration": True,
    }


def run_all() -> dict[str, object]:
    c = load_contract()
    rows = [run_world(c, rep) for rep in range(c["replicates"])]
    expected_total = c["acceptance"]["n_expected_validation_groups_each_condition"]
    total = sum(r["validation_groups"] for r in rows)
    same = sum(r["same_covered"] for r in rows) / total
    shifted = sum(r["shift_covered"] for r in rows) / total
    accept = c["acceptance"]
    checks = {
        "group_roster": total == expected_total and all(
            row["training_groups"] == 80
            and row["calibration_groups"] == 156
            and row["validation_groups"] == 160
            for row in rows
        ),
        "exchangeable_coverage": (
            float(accept["same_process_coverage_range"][0])
            <= same
            <= float(accept["same_process_coverage_range"][1])
        ),
        "distribution_shift_detected": shifted <= float(accept["shifted_coverage_max"]),
        "source_to_model_to_forecast_binding": all(
            row["trained_only_before_calibration"]
            and row["generated_forecasts_directly_from_model_artifacts"]
            and row["validation_labels_not_used_to_adjust_model_or_calibration"]
            for row in rows
        ),
        "empirical_BOP_terminal_unchanged": (
            c["primary_immutable_terminal"] == "empirical_state_prediction_mixed"
        ),
    }
    return {
        "role": "prospective_known_truth_method_validation_not_real_BOP",
        "contract_id": c["contract_id"],
        "contract_sha256": hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest(),
        "worlds": len(rows),
        "validation_group_units_each_condition": total,
        "same_process_coverage": same,
        "shifted_validation_coverage": shifted,
        "passed": all(checks.values()),
        "checks": checks,
        "biological_BOP_endpoint_recomputed": False,
        "frozen_BOP_terminal": "empirical_state_prediction_mixed",
        "world_audit": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="New output path")
    args = parser.parse_args()
    result = run_all()
    report = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)+"\n"
    if args.out:
        if args.out.resolve() == CONTRACT_PATH.resolve():
            raise ValueError("cannot overwrite frozen benchmark contract")
        args.out.write_text(report, encoding="utf-8")
    print(json.dumps({
        "passed": result["passed"],
        "same_process_coverage": result["same_process_coverage"],
        "shifted_validation_coverage": result["shifted_validation_coverage"],
        "worlds": result["worlds"],
        "groups": result["validation_group_units_each_condition"],
        "checks": result["checks"],
    }, sort_keys=True))
    if not result["passed"]:
        raise SystemExit("PRE-FROZEN managed forecast benchmark failed")


if __name__ == "__main__":
    main()
