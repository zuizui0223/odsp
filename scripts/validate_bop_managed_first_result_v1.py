#!/usr/bin/env python3
"""Replay validation against the first frozen managed BOP-method result.

The frozen source contract is pinned by its native Git blob SHA-1 as well
as the SHA-256 recorded in each synthetic benchmark result. The actual
first GitHub Actions ZIP has a separately pinned immutable artifact digest.
This validator requires identical scientific outcomes and all 64 group
rosters, but does not claim byte-for-byte replay of that remote ZIP.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "research/BOP_MANAGED_SOURCE_TO_FORECAST_V1_CONTRACT.json"
RECEIPT = ROOT / "BOP_MANAGED_SOURCE_TO_FORECAST_V1_VALIDATION_RECEIPT.json"
_HEX = re.compile(r"^[0-9a-f]{64}$")


def _git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def _validate_digest(value: object, name: str) -> None:
    if not isinstance(value, str) or _HEX.fullmatch(value) is None:
        raise ValueError(f"{name} must be SHA256 hexadecimal")


def validate_first_managed_result(
    result: dict, receipt: dict, contract_bytes: bytes,
) -> dict[str, object]:
    if (
        result.get("contract_id") != "bop-managed-source-model-forecast-v1-knowntruth"
        or result.get("role") != "prospective_known_truth_method_validation_not_real_BOP"
        or receipt.get("analysis_role") != "prospective_synthetic_methodology_validation_no_real_BOP_reopening"
        or result.get("frozen_BOP_terminal") != "empirical_state_prediction_mixed"
        or result.get("biological_BOP_endpoint_recomputed") is not False
    ):
        raise ValueError("managed benchmark is not the frozen known-truth method endpoint")
    if _git_blob_sha1(contract_bytes) != receipt["contract"]["blob_sha1"]:
        raise ValueError("frozen Git blob SHA mismatch for method contract")
    contract = json.loads(contract_bytes)
    if (
        contract.get("primary_immutable_terminal") != "empirical_state_prediction_mixed"
        or contract.get("rng_seed") != 20261027
        or contract.get("replicates") != 64
        or contract.get("acceptance",{}).get("n_expected_validation_groups_each_condition") != 10240
    ):
        raise ValueError("source contract semantic conditions changed")
    if result.get("contract_sha256") != hashlib.sha256(contract_bytes).hexdigest():
        raise ValueError("result does not derive from exactly frozen source contract")
    if receipt["first_run"]["status"] != "success" or not receipt["first_run"]["artifact_digest"].startswith("sha256:"):
        raise ValueError("first-run archived provenance missing")

    expected = receipt["observed_first_result"]
    design = receipt["fixed_design"]
    if (
        result.get("worlds") != design["world_count"]
        or result.get("validation_group_units_each_condition") != design["validation_group_count_per_scenario"]
        or result.get("checks") != expected["checks"]
        or result.get("passed") is not expected["passed"]
    ):
        raise ValueError("first-run scientific checks or group sizes changed")
    if (
        result.get("same_process_coverage") != expected["same_process_coverage"]
        or result.get("shifted_validation_coverage") != expected["shifted_validation_coverage"]
    ):
        raise ValueError("first-run observed coverage changed")
    worlds = result.get("world_audit")
    if not isinstance(worlds, list) or len(worlds) != design["world_count"]:
        raise ValueError("complete independent-world provenance missing")
    if sorted(row.get("world_index") for row in worlds) != list(range(64)):
        raise ValueError("world indices missing or duplicated")
    required_hashes = (
        "plan_sha256", "training_source_sha256",
        "model_sha256", "reference_sha256",
        "feature_roster_sha256", "calibration_sha256",
    )
    for row in worlds:
        if (
            row.get("training_groups") != design["train_groups_per_stratum"]*design["independent_strata"]
            or row.get("calibration_groups") != design["calibration_groups_per_world"]
            or row.get("validation_groups") != design["validation_groups_per_world"]
            or any(not row.get(k) for k in (
                "trained_only_before_calibration",
                "generated_forecasts_directly_from_model_artifacts",
                "validation_labels_not_used_to_adjust_model_or_calibration",
            ))
        ):
            raise ValueError("first-run group units or model/forecast trust changed")
        for field in required_hashes:
            _validate_digest(row.get(field), field)
        for key in ("same_covered","shift_covered"):
            if isinstance(row.get(key), bool) or not isinstance(row.get(key),int) or not 0<=row[key]<=design["validation_groups_per_world"]:
                raise ValueError("individual world coverage count invalid")
    all_n=design["validation_group_count_per_scenario"]
    same_count=sum(row["same_covered"] for row in worlds)
    shift_count=sum(row["shift_covered"] for row in worlds)
    if (
        same_count != expected["same_process_covered_groups"]
        or shift_count != expected["shifted_covered_groups"]
        or not math.isclose(same_count/all_n,expected["same_process_coverage"],rel_tol=0,abs_tol=0)
        or not math.isclose(shift_count/all_n,expected["shifted_validation_coverage"],rel_tol=0,abs_tol=0)
    ):
        raise ValueError("per-world outcomes disagree with preserved original coverage")
    return {
        "validated": True,
        "worlds":len(worlds),
        "same_covered_groups":same_count,
        "shifted_covered_groups":shift_count,
        "historical_BOP_changed":False,
    }


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result",type=Path,required=True)
    args=parser.parse_args()
    output=validate_first_managed_result(
        json.loads(args.result.read_text(encoding="utf-8")),
        json.loads(RECEIPT.read_text(encoding="utf-8")),
        CONTRACT.read_bytes(),
    )
    print(json.dumps(output,sort_keys=True))


if __name__=="__main__":
    main()
