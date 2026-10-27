#!/usr/bin/env python3
"""Validate the first-green synthetic fixed-model BOP method receipt.

Only reads a newly generated synthetic JSON report and the previously frozen
contract/result receipt. No empirical telemetry, predictor refit or overwrites.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "BOP_FIXED_MODEL_GROUP_TRANSFER_V1_VALIDATION_RECEIPT.json"
CONTRACT = ROOT / "research/BOP_FIXED_MODEL_GROUP_TRANSFER_V1_CONTRACT.json"


def validate_report(result: dict, receipt: dict, contract_bytes: bytes) -> None:
    if (
        result.get("contract_id") != "bop-fixed-model-group-transfer-known-truth-v1"
        or receipt.get("role") != "prospective_known_truth_methodology_validation_not_empirical_BOP"
        or result.get("result_role") != "prospective_known_truth_only_not_empirical_BOP"
    ):
        raise ValueError("synthetic methodology source/role mismatch")
    expected_contract_sha = hashlib.sha256(contract_bytes).hexdigest()
    if (
        expected_contract_sha != receipt["frozen_contract_sha256"]
        or result.get("contract_sha256") != expected_contract_sha
    ):
        raise ValueError("precommitted scientific contract was changed")
    if (
        result.get("frozen_empirical_terminal") != "empirical_state_prediction_mixed"
        or result.get("empirical_result_recomputed") is not False
        or receipt["scientific_boundary"]["new_real_BOP_individuals_tested"] is not False
        or receipt["scientific_boundary"]["historical_BOP_terminal"] != "empirical_state_prediction_mixed"
    ):
        raise ValueError("real BOP terminal cannot be promoted or recomputed")
    truth = receipt["first_result"]
    if (
        result.get("n_replicates") != receipt["generator"]["replicates"]
        or result.get("strata") != receipt["generator"]["stratum_count"]
        or result.get("validation_groups_each_scenario") != receipt["generator"]["validation_groups_per_scenario"]
        or result.get("passed") is not True
        or result.get("acceptance_checks") != truth["checks"]
    ):
        raise ValueError("first-result acceptance/counts changed")
    for key, expected in {
        "same_process": truth["same_process_group_coverage"],
        "shifted_validation_labels_plus_two_mod_four": truth["shifted_validation_labels_plus_two_mod_four_group_coverage"],
    }.items():
        actual = result["coverage"][key]
        if not math.isclose(actual, expected, abs_tol=0.0, rel_tol=0.0):
            raise ValueError(f"frozen first-result {key} coverage changed")
    reps = result.get("per_replicate_provenance")
    if not isinstance(reps, list) or len(reps) != 128:
        raise ValueError("full 128-replicate provenance missing")
    if sorted(r.get("replicate_index") for r in reps) != list(range(128)):
        raise ValueError("replicate indices missing or duplicated")
    for r in reps:
        if (
            r["validation_groups"] != 320
            or r["calibration_groups"] != 156
            or r["training_groups"] != 80
            or r["model_artifact_retrained_after_calibration"] is not False
            or r["calibration_touched_validation_labels"] is not False
            or not isinstance(r["plan_sha256"], str)
            or len(r["plan_sha256"]) != 64
            or not isinstance(r["calibration_sha256"], str)
            or len(r["calibration_sha256"]) != 64
        ):
            raise ValueError("unfrozen/overlapping individual-group provenance")
    same_count = sum(r["same_covered"] for r in reps)
    shift_count = sum(r["shift_covered"] for r in reps)
    n = result["validation_groups_each_scenario"]
    if (
        same_count / n != result["coverage"]["same_process"]
        or shift_count / n != result["coverage"]["shifted_validation_labels_plus_two_mod_four"]
    ):
        raise ValueError("coverage is inconsistent with group-level audit rows")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    result = json.loads(args.result.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    validate_report(result, receipt, CONTRACT.read_bytes())
    print("PASS: frozen first-green known-truth fixed-model group transfer receipt")


if __name__ == "__main__":
    main()
