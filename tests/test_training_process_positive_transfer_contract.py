from __future__ import annotations

import json
from pathlib import Path


CONTRACT = Path("ODSP_TRAINING_PROCESS_POSITIVE_TRANSFER_CONTRACT.json")


def _payload():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_contract_freezes_distinct_process_mean_estimand():
    payload = _payload()
    target = payload["inferential_target"]
    assert payload["contract_id"] == "odsp-training-process-positive-transfer-v1"
    assert target["process_mean_target"] is True
    assert target["conditional_on_frozen_training_source"] is True
    assert target["original_training_dataset_sampling_uncertainty_included"] is False
    assert target["fixed_supplied_refit_set_is_estimand"] is False
    assert target["all_possible_refits_must_pass"] is False
    assert target["individual_future_refit_success_probability_is_estimand"] is False


def test_contract_freezes_crossed_not_validation_multiplied_resampling():
    crossed = _payload()["crossed_resampling"]
    assert crossed["training_refit_draws_per_bootstrap_replicate"] == "R_with_replacement"
    assert crossed["same_refit_resample_shared_across_all_group_contrast_cells"] is True
    assert crossed["same_validation_block_resample_shared_across_refits"] is True
    assert crossed["validation_blocks_redrawn_separately_per_refit"] is False
    assert crossed["training_and_validation_axes_resampled_independently"] is True
    assert crossed["validation_sample_size_multiplied_by_refit_count"] is False


def test_contract_records_null_qualification_without_premature_primary_promotion():
    payload = _payload()
    state = payload["qualification_state"]
    assert state["status"] == "null_qualified_pending_power_and_provenance"
    assert state["primary_confirmatory"] is False
    assert state["completed_qualification_evidence"] == [
        "TRAINING_PROCESS_POSITIVE_NULL_CALIBRATION_RECEIPT.json"
    ]
    assert (
        "prospective power operating-characteristic panel for crossed bootstrap-t"
        in state["required_before_primary_routing"]
    )
    assert payload["scope_v1"]["untouched_external_endpoint_qualified"] is False
    assert payload["studentization_v1"][
        "prospective_operating_characteristic_qualification_required_before_confirmatory_use"
    ] is True


def test_contract_forbids_reclassification_of_existing_refit_results():
    boundary = _payload()["claim_boundary"]
    assert boundary["fixed_set_intersection_used"] is False
    assert boundary["fixed_set_result_can_be_rescued_or_reclassified"] is False
    assert boundary["historical_empirical_endpoint_reclassified"] is False
    assert boundary["old_refit_mixture_sensitivity_promoted"] is False
