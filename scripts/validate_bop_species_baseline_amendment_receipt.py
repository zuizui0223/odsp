#!/usr/bin/env python3
"""Validate the canonical BOP species-baseline amendment receipt against a generated result."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "BOP_RODENT_SPECIES_BASELINE_AMENDMENT_RECEIPT.json"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _close(a: float, b: float, tol: float = 1e-12) -> bool:
    return math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=tol)


def validate(result_path: Path) -> None:
    result = _read(result_path)
    receipt = _read(RECEIPT)
    if result["contract_id"] != receipt["contract_id"]:
        raise AssertionError("contract id mismatch")
    if result["post_outcome_amendment"] is not True:
        raise AssertionError("generated result lost post-outcome amendment status")
    for key in ("model_refit_performed", "raw_source_data_reaccessed", "retuning_performed"):
        if result[key] is not False or receipt[key] is not False:
            raise AssertionError(f"forbidden mutation flag changed: {key}")

    result_primary = result["frozen_primary_endpoint"]
    receipt_primary = receipt["frozen_primary_endpoint"]
    for key in ("terminal_category", "positive_individual_count", "eligible_individual_count"):
        if result_primary[key] != receipt_primary[key]:
            raise AssertionError(f"primary endpoint drift: {key}")
    if not _close(result_primary["mean_total_gain"], receipt_primary["mean_total_gain"]):
        raise AssertionError("primary mean gain drift")
    if result_primary["terminal_decision_changed"] is not False:
        raise AssertionError("amendment changed primary terminal decision")

    generated = result["decomposition"]
    for key, expected in receipt["overall_summary"].items():
        observed = generated["overall_summary"][key]
        if isinstance(expected, float):
            if not _close(observed, expected, tol=1e-12):
                raise AssertionError(f"overall summary drift: {key}")
        elif observed != expected:
            raise AssertionError(f"overall summary drift: {key}")

    generated_species = generated["species_summary"]
    for species, expected in receipt["species_summary"].items():
        observed = generated_species[species]
        if observed["individual_count"] != expected["individual_count"]:
            raise AssertionError(f"individual count drift for {species}")
        if observed["eligible_allfold_state_counts"] != expected["state_counts"]:
            raise AssertionError(f"eligible state-count drift for {species}")
        if observed["heldout_state_counts"] != expected["state_counts"]:
            raise AssertionError(f"held-out state-count drift for {species}")
        for key in (
            "mean_total_gain",
            "mean_species_component",
            "mean_context_within_species_component",
        ):
            if not _close(observed[key], expected[key], tol=1e-12):
                raise AssertionError(f"{key} drift for {species}")
        for key in ("positive_species_component_count", "positive_context_component_count"):
            if observed[key] != expected[key]:
                raise AssertionError(f"{key} drift for {species}")

    if generated["primary_terminal_decision_recomputed"] is not False:
        raise AssertionError("generated amendment recomputed primary terminal decision")
    if generated["primary_terminal_decision_changed"] is not False:
        raise AssertionError("generated amendment changed primary terminal decision")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    validate(args.result)
    print("BOP species-baseline amendment receipt validated")


if __name__ == "__main__":
    main()
