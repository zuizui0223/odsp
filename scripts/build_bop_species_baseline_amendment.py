#!/usr/bin/env python3
"""Build the post-outcome descriptive BOP species-baseline amendment result.

The builder consumes only the checksum-pinned frozen state-prediction result
artifact.  It does not download raw tracking data and does not refit the frozen
random-forest model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from odsp.bop_species_baseline import decompose_frozen_bop_gains


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "BOP_RODENT_SPECIES_BASELINE_AMENDMENT_CONTRACT.json"
PRIMARY_RECEIPT_PATH = ROOT / "BOP_RODENT_STATE_PREDICTION_TERMINAL_RECEIPT.json"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(frozen_result_path: Path) -> dict[str, object]:
    contract = _read(CONTRACT_PATH)
    primary_receipt = _read(PRIMARY_RECEIPT_PATH)
    expected_sha = str(contract["source_evidence"]["result_json_sha256"])
    observed_sha = _sha256(frozen_result_path)
    if observed_sha != expected_sha:
        raise AssertionError(
            f"frozen result sha256 mismatch: expected {expected_sha}, observed {observed_sha}"
        )
    frozen_result = _read(frozen_result_path)
    if frozen_result.get("contract_id") != contract["frozen_primary_endpoint"]["contract_id"]:
        raise AssertionError("frozen result contract_id does not match amendment contract")
    if frozen_result.get("endpoint") != primary_receipt.get("endpoint"):
        raise AssertionError("frozen result endpoint does not match primary terminal receipt")
    if primary_receipt["primary_random_forest"]["terminal_category"] != contract["frozen_primary_endpoint"]["terminal_category"]:
        raise AssertionError("primary terminal category drifted")
    if int(primary_receipt["primary_random_forest"]["positive_individual_count"]) != int(
        contract["frozen_primary_endpoint"]["positive_individual_count"]
    ):
        raise AssertionError("primary positive-individual count drifted")

    decomposition = decompose_frozen_bop_gains(
        frozen_result,
        reconstruction_tolerance=1e-10,
        additivity_tolerance=float(contract["per_individual_decomposition"]["required_additivity_tolerance"]),
    )
    return {
        "schema_version": 1,
        "amendment_id": "bop-rodent-species-baseline-descriptive-amendment-result-v1",
        "contract_id": contract["contract_id"],
        "post_outcome_amendment": True,
        "analysis_type": contract["analysis_type"],
        "source_evidence": {
            "workflow_run_id": int(contract["source_evidence"]["workflow_run_id"]),
            "artifact_id": int(contract["source_evidence"]["artifact_id"]),
            "artifact_digest": contract["source_evidence"]["artifact_digest"],
            "result_json_sha256": observed_sha,
        },
        "frozen_primary_endpoint": {
            "terminal_category": primary_receipt["primary_random_forest"]["terminal_category"],
            "positive_individual_count": int(primary_receipt["primary_random_forest"]["positive_individual_count"]),
            "eligible_individual_count": int(primary_receipt["primary_random_forest"]["eligible_individual_count"]),
            "mean_total_gain": float(primary_receipt["primary_random_forest"]["mean_gain_descriptive"]),
            "terminal_decision_recomputed": False,
            "terminal_decision_changed": False,
        },
        "decomposition": decomposition,
        "model_refit_performed": False,
        "raw_source_data_reaccessed": False,
        "retuning_performed": False,
        "claim_boundary": contract["claim_boundary"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frozen-result", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.frozen_result)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["decomposition"]["overall_summary"], sort_keys=True))


if __name__ == "__main__":
    main()
