from __future__ import annotations

from copy import deepcopy
import json

import pytest

from scripts.audit_bop_common_input_world_uncertainty_v1 import (
    ORIGINAL_CONTRACT, RECEIPT, SOURCE, audit_world_uncertainty,
)


def _fixture():
    return (
        json.loads(SOURCE.read_text(encoding="utf-8")),
        json.loads(RECEIPT.read_text(encoding="utf-8")),
        ORIGINAL_CONTRACT.read_bytes(),
    )


def test_24_independent_world_monte_carlo_uncertainty_and_paired_shift():
    source, receipt, contract = _fixture()
    result = audit_world_uncertainty(source, receipt, contract)
    assert result["evidence_role"] == (
        "POST_RESULT_DESCRIPTIVE_WORLD_LEVEL_PRECISION_AUDIT_NOT_PREREGISTERED"
    )
    assert result["independent_monte_carlo_world_count"] == 24
    assert result["groups_per_world_sharing_fitted_model_and_calibrator"] == 120
    assert result["total_validation_animal_scores_per_condition"] == 2880
    assert result["original_24world_first_result_preserved"] is True
    assert result["new_external_BOP_or_Dryad_measurements"] is False
    assert result["new_confirmatory_hypothesis_test_performed"] is False
    assert result["original_frozen_method_pass_reclassified"] is False
    assert result["original_BOP_empirical_terminal"] == (
        "empirical_state_prediction_mixed"
    )
    same = result["source_target_group_coverage"]
    shifted = result["validation_only_shift_group_coverage"]
    paired = result["paired_coverage_difference"]
    assert same["mean"] == pytest.approx(2599 / 2880, abs=1e-15)
    assert shifted["mean"] == pytest.approx(757 / 2880, abs=1e-15)
    assert paired["mean"] == pytest.approx((2599 - 757) / 2880, abs=1e-15)
    assert (same["t95_lower"], same["t95_upper"]) == pytest.approx(
        (0.88613973587544, 0.918721375235671), abs=1e-10
    )
    assert (shifted["t95_lower"], shifted["t95_upper"]) == pytest.approx(
        (0.23678206564255413, 0.28891237880189036), abs=1e-10
    )
    assert (paired["t95_lower"], paired["t95_upper"]) == pytest.approx(
        (0.6151763817632907, 0.6639902849033759), abs=1e-10
    )
    assert same["min_world"] == pytest.approx(95 / 120)
    assert same["max_world"] == pytest.approx(118 / 120)
    assert shifted["max_world"] == pytest.approx(50 / 120)
    assert paired["min_world"] > 0
    assert same["independent_world_monte_carlo_se"] > 0.007
    assert shifted["independent_world_monte_carlo_se"] > 0.012
    assert same["independent_world_monte_carlo_se"] > result[
        "naive_2880_iid_binomial_se_invalid_for_shared_worlds"
    ]["source_target"]
    assert shifted["independent_world_monte_carlo_se"] > result[
        "naive_2880_iid_binomial_se_invalid_for_shared_worlds"
    ]["validation_only_shift"]
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("change, message", [
    ("modified_one_world", "world-count trace"),
    ("duplicated_world_id", "world row"),
    ("wrong_total", "world row"),
    ("added_raw_animal_id", "extra fields"),
    ("changed_first_source", "original first-run provenance"),
    ("shifted_to_empirical", "science"),
    ("altered_contract", "frozen first-run science"),
])
def test_tampering_or_empirical_promotion_rejected(change, message):
    source, receipt, contract = _fixture()
    source = deepcopy(source)
    if change == "modified_one_world":
        source["worlds"][0]["same"] -= 1
    elif change == "duplicated_world_id":
        source["worlds"][1]["world"] = 0
    elif change == "wrong_total":
        source["worlds"][0]["n"] = 121
    elif change == "added_raw_animal_id":
        source["worlds"][0]["tag"] = "EXTRA"
    elif change == "changed_first_source":
        source["original_actions"]["artifact_id"] = 0
    elif change == "shifted_to_empirical":
        source["role"] = "new_prospective_real_BOP"
    elif change == "altered_contract":
        contract += b" "
    with pytest.raises(ValueError, match=message):
        audit_world_uncertainty(source, receipt, contract)


def test_not_all_simulated_training_worlds_have_conditional_90_percent_coverage():
    source, receipt, contract = _fixture()
    out = audit_world_uncertainty(source, receipt, contract)
    # Marginal exchangeable rank validity across worlds cannot claim a
    # 90% conditional guarantee for every fitted model and calibrator.
    assert out["source_target_group_coverage"]["min_world"] < 0.8
    assert out["source_target_group_coverage"]["max_world"] > 0.98
    assert "NOT 90% conformal gain bound" in out["confidence_interval_interpretation"]
