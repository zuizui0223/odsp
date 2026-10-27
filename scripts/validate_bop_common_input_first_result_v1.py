#!/usr/bin/env python3
"""Check common-input BOP known-truth reruns against FIRST archived outcomes.

This is a statistical-method receipt validator, not real BOP or Dryad
ecological confirmation. The original fixed contract, group-level
audit trace and artifact digest may not be tuned or overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"research/BOP_COMMON_INPUT_TRANSPORT_V1_CONTRACT.json"
RECEIPT=ROOT/"BOP_COMMON_INPUT_TRANSPORT_V1_VALIDATION_RECEIPT.json"
_SHA=re.compile(r"^[0-9a-f]{64}$")


def _sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def _world_fingerprint(worlds:list[dict])->str:
    raw=json.dumps(
        worlds,sort_keys=True,ensure_ascii=False,
        separators=(",",":"),allow_nan=False
    ).encode("utf-8")
    return _sha(raw)


def validate_first_bop_transport_result(
    result:dict,receipt:dict,contract_bytes:bytes,
    *,
    raw_result_bytes:bytes|None=None,
)->dict[str,object]:
    freeze=receipt["frozen_contract"]
    first=receipt["first_result"]
    design=receipt["design"]
    provenance=receipt["first_execution"]
    boundary=receipt["scientific_boundary"]
    if _sha(contract_bytes)!=freeze["contract_sha256"]:
        raise ValueError("pre-outcome original common-input contract drifted")
    if (
        freeze["contract_freeze_commit_sha"]!="b32eed2503b94cbec0bab21daa4f20f765bb6fe0"
        or provenance["workflow_run_id"]!=40281982238
        or provenance["artifact_id"]!=12633395633
        or provenance["artifact_zip_sha256"]!="e95e5e35f51b56ac136a8d93870868b4aab553fd6c5c30de78de22db758df993"
    ):
        raise ValueError("first official method contract/artifact provenance changed")
    if raw_result_bytes is not None:
        if _sha(raw_result_bytes)!=provenance["original_result_json_sha256"]:
            raise ValueError("new result raw JSON differs from original known-truth result")
        if len(raw_result_bytes)!=provenance["original_result_json_byte_count"]:
            raise ValueError("original known-truth JSON byte count changed")
    if (
        result.get("contract_id")!="bop-common-input-transport-new-individual-v1"
        or result.get("contract_sha256")!=freeze["contract_sha256"]
        or result.get("role")!="prospective_known_truth_method_validation_only_not_real_BOP_or_Dryad_results"
        or result.get("original_BOP_terminal")!="empirical_state_prediction_mixed"
        or result.get("original_RF_direct_external_transfer_admissible") is not False
        or result.get("external_Dryad_candidate_admitted") is not False
        or result.get("real_GPS_or_altitude_data_accessed") is not False
        or result.get("passed") is not True
        or result.get("checks")!=first["checks"]
        or result.get("worlds")!=design["worlds"]
        or result.get("validation_individual_groups_each_condition")
             !=design["validation_independent_animals_per_condition"]
    ):
        raise ValueError("BOP external methodology source/claim ceiling or checks changed")
    if (
        result.get("same_target_source_group_coverage")
            !=first["stable_target_source_group_coverage"]
        or result.get("shifted_validation_only_group_coverage")
            !=first["validation_only_distribution_shift_group_coverage"]
    ):
        raise ValueError("frozen first target-group coverage changed")
    worlds=result.get("full_world_audit")
    if (
        not isinstance(worlds,list)
        or len(worlds)!=design["worlds"]
        or sorted(x.get("world") for x in worlds)!=list(range(design["worlds"]))
    ):
        raise ValueError("complete 24-world independent group audit missing")
    for w in worlds:
        if (
            w.get("training_individuals")!=80
            or w.get("calibration_individuals")!=156
            or w.get("validation_individuals")!=120
            or w.get("source_shift_from_BOP_training_to_Dryad_target") is not True
            or w.get("group_sampling_target_source_stable_within_calibration_validation") is not True
            or w.get("training_model_refitted_after_target_outcome") is not False
            or w.get("target_identity_crosswalk_real_world_verified") is not False
            or w.get("original_bop_terminal_changed") is not False
        ):
            raise ValueError("independent group/sample or source-provenance audit changed")
        for field in ("model_sha256","reference_sha256","calibration_sha256","frozen_forecast_plan_sha256"):
            if not isinstance(w.get(field),str) or not _SHA.fullmatch(w[field]):
                raise ValueError("model, reference or calibration SHA invalid")
    n=design["validation_independent_animals_per_condition"]
    stable=sum(w["covered_same"] for w in worlds)
    shifted=sum(w["covered_validation_shift"] for w in worlds)
    if (
        stable!=first["covered_target_individuals"]
        or shifted!=first["covered_validation_shift_individuals"]
        or stable/n!=first["stable_target_source_group_coverage"]
        or shifted/n!=first["validation_only_distribution_shift_group_coverage"]
        or _world_fingerprint(worlds)!=provenance["original_result_world_audit_sha256"]
    ):
        raise ValueError("individual-world scores differ from first frozen known-truth audit")
    if (
        boundary.get("original_BOP_terminal")!="empirical_state_prediction_mixed"
        or boundary.get("real_Dryad_candidate_admitted") is not False
        or boundary.get("original_BOP_RF_direct_external_scoring_validated") is not False
        or boundary.get("original_BOP_scientific_results_modified") is not False
    ):
        raise ValueError("historical BOP or external Dryad claim exceeded")
    return {
        "frozen_method_result_verified":True,
        "original_workflow_run_id":provenance["workflow_run_id"],
        "independent_target_animals":n,
        "covered_target_animals":stable,
        "covered_under_validation_only_shift":shifted,
        "same_target_source_coverage":stable/n,
        "source_shift_target_coverage_supported_for_synthetic_only":True,
        "original_BOP_terminal_changed":False,
        "real_external_Dryad_scored":False,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result",required=True,type=Path)
    a=p.parse_args()
    raw=a.result.read_bytes()
    verified=validate_first_bop_transport_result(
        json.loads(raw),json.loads(RECEIPT.read_text()),
        CONTRACT.read_bytes(),raw_result_bytes=raw
    )
    print(json.dumps(verified,sort_keys=True))


if __name__=="__main__":
    main()
