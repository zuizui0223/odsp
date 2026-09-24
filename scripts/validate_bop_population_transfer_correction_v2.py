#!/usr/bin/env python3
"""Validate the canonical corrected BOP few-cluster receipt v2."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "BOP_RODENT_POPULATION_TRANSFER_CORRECTION_RECEIPT_V2.json"


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
        if not math.isclose(float(observed), expected, rel_tol=0.0, abs_tol=1e-10):
            raise AssertionError(f"numeric drift at {path}: {observed} != {expected}")
        return
    if observed != expected:
        raise AssertionError(f"value drift at {path}: {observed!r} != {expected!r}")


def validate(result_path: Path) -> None:
    result = _read(result_path)
    receipt = _read(RECEIPT)
    for key in (
        "contract_id",
        "supersedes_inference_from_contract_id",
        "post_outcome_amendment",
        "analysis_type",
    ):
        if result[key] != receipt[key]:
            raise AssertionError(f"amendment metadata drift: {key}")
    for key in ("model_refit_performed", "raw_source_data_reaccessed", "retuning_performed"):
        if result[key] is not False or receipt[key] is not False:
            raise AssertionError(f"forbidden mutation flag changed: {key}")
    _compare(result["source_evidence"], receipt["source_evidence"], "source_evidence")
    _compare(
        result["frozen_primary_endpoint"],
        receipt["frozen_primary_endpoint"],
        "frozen_primary_endpoint",
    )
    _compare(result["population_result"], receipt["population_result"], "population_result")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    validate(args.result)
    print("BOP few-cluster correction v2 receipt validated")


if __name__ == "__main__":
    main()
