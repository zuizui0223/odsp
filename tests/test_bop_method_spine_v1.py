"""Integrated BOP methodology spine: frozen archived evidence and claim ceiling.

This test never accesses GPS, held-out labels or external source files.
It checks that method development did not overwrite the six original
biological, synthetic, and source-eligibility decisions.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FROZEN_REPOSITORY_BLOB_SHA1={
    "BOP_RODENT_STATE_PREDICTION_TERMINAL_RECEIPT.json":
        "3da6937a410ae73d0976cd1b80334d69685ea006",
    "BOP_FIXED_MODEL_GROUP_TRANSFER_V1_VALIDATION_RECEIPT.json":
        "e587b435e1e3d06621eabfbae3569e55d294e763",
    "BOP_MANAGED_SOURCE_TO_FORECAST_V1_VALIDATION_RECEIPT.json":
        "16a9e529434359aae1651c5d3b273769fc65c252",
    "BOP_V3_V2026_REFERENCE_ONLY_GATE_V1_TERMINAL_RECEIPT.json":
        "8fba1499b4fd5333abcabf28cec83c6505b29cc3",
    "BOP_DRYAD_EXTERNAL_SCHEMA_PREFLIGHT_V1_TERMINAL_RECEIPT.json":
        "8a62516524cff760851d77f6d6679fe46235eba6",
    "BOP_COMMON_INPUT_TRANSPORT_V1_VALIDATION_RECEIPT.json":
        "51a3ad192546c5f8c0b2ff7329e17f02a16b83e1",
}


def _blob(raw: bytes)->str:
    return hashlib.sha1(
        b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw
    ).hexdigest()


def _receipts()->dict[str,dict]:
    return {name:json.loads((ROOT/name).read_text(encoding="utf-8"))
            for name in FROZEN_REPOSITORY_BLOB_SHA1}


def test_six_original_scientific_receipts_have_exact_immutable_blob_identity():
    for path,sha in FROZEN_REPOSITORY_BLOB_SHA1.items():
        original=(ROOT/path).read_bytes()
        assert _blob(original)==sha, "frozen receipt unexpectedly changed: "+path


def test_historic_BOP_biological_outcome_is_mixed_and_not_synthetic_certified():
    p=_receipts()["BOP_RODENT_STATE_PREDICTION_TERMINAL_RECEIPT.json"]
    r=p["primary_random_forest"]
    flow=p["data_flow"]
    assert p["contract_id"]=="bop-rodent-state-prediction-v1"
    assert r["terminal_category"]=="empirical_state_prediction_mixed"
    assert r["eligible_individual_count"]==30
    assert r["positive_individual_count"]==27
    assert r["nonpositive_individual_count"]==3
    assert r["positive_brier_improvement_count"]==30
    assert flow["eligible_event_count"]==154655
    assert flow["admitted_species_count"]==4
    assert len(flow["admitted_species"])==4


def test_synthetic_rank_and_provenance_validation_are_not_real_BOP_coverage():
    a=_receipts()
    fixed=a["BOP_FIXED_MODEL_GROUP_TRANSFER_V1_VALIDATION_RECEIPT.json"]
    managed=a["BOP_MANAGED_SOURCE_TO_FORECAST_V1_VALIDATION_RECEIPT.json"]
    f=fixed["first_result"]
    m=managed["observed_first_result"]
    assert fixed["generator"]["validation_groups_per_scenario"]==40960
    assert fixed["scientific_boundary"]["new_real_BOP_individuals_tested"] is False
    assert f["same_process_group_coverage"]==0.8994384765625
    assert f["shifted_validation_labels_plus_two_mod_four_group_coverage"]==0.0680908203125
    assert f["passed"] is True
    assert managed["fixed_design"]["validation_group_count_per_scenario"]==10240
    assert m["same_process_coverage"]==0.89150390625
    assert m["shifted_validation_coverage"]==0.1287109375
    assert m["passed"] is True
    assert managed["evidence_boundaries"]["synthetic_known_truth_only"] is True
    assert managed["evidence_boundaries"]["newly_observed_real_birds"]==0


def test_source_gates_and_target_calibration_remain_independent_issues():
    a=_receipts()
    older=a["BOP_V3_V2026_REFERENCE_ONLY_GATE_V1_TERMINAL_RECEIPT.json"]["first_terminal"]
    dryad=a["BOP_DRYAD_EXTERNAL_SCHEMA_PREFLIGHT_V1_TERMINAL_RECEIPT.json"]
    transport=a["BOP_COMMON_INPUT_TRANSPORT_V1_VALIDATION_RECEIPT.json"]
    assert older["category"]=="NO_WITHIN_STRATUM_NEW_GROUP_RANK_SUPPORT"
    assert older["old_unique_individual_ids"]==35
    assert older["new_unique_individual_ids"]==45
    assert older["novel_id_candidate_count"]==10
    assert older["maximum_single_species_new_ids"]==6
    assert older["no_species_met_threshold"] is True
    assert dryad["terminal"]["candidate"]=="NOT_ADMITTED"
    assert dryad["original_model_compatibility"]["direct_external_predictor_reuse"]==(
        "ORIGINAL_RF_PREDICTOR_INCOMPATIBLE"
    )
    assert dryad["original_model_compatibility"]["missing_documented_required_predictors"]==[
        "external-temperature"
    ]
    assert dryad["terminal"]["historical_BOP_terminal"]=="empirical_state_prediction_mixed"
    p=transport["first_result"]
    assert p["covered_target_individuals"]==2599
    assert p["covered_validation_shift_individuals"]==757
    assert p["stable_target_source_group_coverage"]==2599/2880
    assert p["validation_only_distribution_shift_group_coverage"]==757/2880
    assert p["passed"] is True
    assert transport["scientific_boundary"]["all_results_are_synthetic"] is True
    assert transport["scientific_boundary"]["real_Dryad_candidate_admitted"] is False
    assert transport["scientific_boundary"]["original_BOP_RF_direct_external_scoring_validated"] is False
    assert transport["scientific_boundary"]["original_BOP_terminal"]=="empirical_state_prediction_mixed"
