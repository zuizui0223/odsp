#!/usr/bin/env python3
"""Validate the corrected BOP population-transfer amendment v2 receipt."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "BOP_RODENT_POPULATION_TRANSFER_AMENDMENT_RECEIPT_V2.json"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _compare(observed: object, expected: object, path: str = "root") -> None:
    if isinstance(expected, dict):
        if not isinstance(observed, dict) or set(observed) != set(expected):
            raise AssertionError(f"mapping drift at {path}")
        for key in expected:
            _compare(observed[key], expected[key], f"{path}.{key}")
        return
    if isinstance(expected, list):
        if not isinstance(observed, list) or len(observed) != len(expected):
            raise AssertionError(f"list drift at {path}")
        for index, (left, right) in enumerate(zip(observed, expected)):
            _compare(left, right, f"{path}[{index}]")
        return
    if isinstance(expected, float):
        if not math.isclose(float(observed), expected, rel_tol=0.0, abs_tol=1e-12):
            raise AssertionError(f"numeric drift at {path}: {observed} != {expected}")
        return
    if observed != expected:
        raise AssertionError(f"value drift at {path}: {observed!r} != {expected!r}")


def validate(result_path: Path) -> None:
    result = _read(result_path)
    receipt = _read(RECEIPT)
    for key in (
        "schema_version",
        "contract_id",
        "post_outcome_amendment",
        "analysis_type",
        "supersedes",
        "source_evidence",
        "frozen_primary_endpoint",
        "population_result",
        "model_refit_performed",
        "raw_source_data_reaccessed",
        "retuning_performed",
    ):
        _compare(result[key], receipt[key], key)

    total = result["population_result"]["total_gain"]
    if total["mean_gain_status"] != "uncertain":
        raise AssertionError("corrected BOP total mean must remain uncertain")
    if not (
        float(total["mean_gain_lower"]) < 0.0 < float(total["mean_gain_upper"])
    ):
        raise AssertionError("corrected BOP total interval must cross zero")
    if total["positive_fraction_lower_method"] != (
        "wilson_score_group_level_small_cluster_fallback"
    ):
        raise AssertionError("small-cluster prevalence fallback drifted")
    if result["population_result"]["uncertainty"]["mean_interval_method"] != (
        "cluster_robust_t_cr1"
    ):
        raise AssertionError("small-cluster mean interval method drifted")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    validate(args.result)
    print("BOP population-transfer amendment v2 receipt validated")


if __name__ == "__main__":
    main()
