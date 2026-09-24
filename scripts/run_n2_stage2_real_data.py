#!/usr/bin/env python3
"""Execute the single fresh N2 stage-2 Palmer Penguins analysis."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from odsp.n2_failure_mode_stage2 import (
    FROZEN_CONTRACT_MERGE_SHA,
    load_stage2_contract,
    run_penguins_stage2,
    stage2_synthesis,
)


ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def build(source: Path, contract_path: Path) -> dict[str, object]:
    contract = load_stage2_contract(contract_path)
    penguins = run_penguins_stage2(source, contract=contract)
    bop = _read(ROOT / "BOP_RODENT_POPULATION_TRANSFER_AMENDMENT_RECEIPT_V2.json")
    bop_species = _read(ROOT / "BOP_RODENT_SPECIES_BASELINE_AMENDMENT_RECEIPT.json")
    serengeti = _read(ROOT / "N2_SERENGETI_TEMPORAL_TERMINAL_RECEIPT.json")

    if bop["contract_id"] != "bop-rodent-population-transfer-descriptive-amendment-v2":
        raise AssertionError("BOP corrected population receipt drifted")
    if bop["supersedes"]["v1_population_inference_should_not_be_used"] is not True:
        raise AssertionError("BOP v1 population inference was not superseded")
    if serengeti["terminal_category"] != "temporal_partition_generalizing":
        raise AssertionError("frozen Serengeti semantic control drifted")

    synthesis = stage2_synthesis(
        penguins,
        bop_v2_receipt=bop,
        bop_species_receipt=bop_species,
        serengeti_receipt=serengeti,
    )
    return {
        "schema_version": 1,
        "receipt_type": "n2_pooled_reference_failure_mode_stage2_real_data_v1",
        "contract_id": contract["contract_id"],
        "contract_merge_sha": FROZEN_CONTRACT_MERGE_SHA,
        "one_shot_execution": True,
        "fresh_result_system": "PALMER_PENGUINS",
        "penguins": penguins,
        "synthesis": synthesis,
        "scientific_boundary": {
            "stage1_full_claim_reclassified": False,
            "literature_prevalence_estimated": False,
            "BOP_rerun": False,
            "Serengeti_rerun": False,
            "post_result_dataset_addition_allowed": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.source, args.contract)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "fresh_penguins_decision": result["synthesis"][
                    "fresh_penguins_decision"
                ],
                "descriptive_counts": result["synthesis"]["descriptive_counts"],
                "prepared_row_count": result["penguins"]["prepared_row_count"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
