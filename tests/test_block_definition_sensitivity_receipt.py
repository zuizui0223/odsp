import json
from pathlib import Path

import pytest

from odsp.block_definition_sensitivity_benchmark import run_block_definition_sensitivity_benchmark


ROOT=Path(__file__).resolve().parents[1]


def test_block_definition_sensitivity_receipt_replays():
    receipt=json.loads((ROOT/"BLOCK_DEFINITION_SENSITIVITY_VALIDATION_RECEIPT.json").read_text(encoding="utf-8"))
    result=run_block_definition_sensitivity_benchmark(seed=20260906,bootstrap_draws=2000)
    canonical=receipt["canonical_results"]
    assert result["passed"] is canonical["passed"] is True
    assert len(result["checks"])==canonical["obligation_count"]==12

    for result_key,receipt_key in [
        ("strong_positive","strong_positive"),
        ("strong_negative","strong_negative"),
        ("too_coarse","too_coarse"),
    ]:
        observed=result[result_key]
        expected=canonical[receipt_key]
        assert observed["sensitivity_category"]==expected["sensitivity_category"]
        assert observed["robust_category_set"]==expected["robust_category_set"]
        assert observed["point_category_set"]==expected["point_category_set"]
        assert observed["minimum_definition_group_block_count"]==expected["minimum_definition_group_block_count"]
        assert observed["maximum_definition_group_block_count"]==expected["maximum_definition_group_block_count"]

    pseudo=result["pseudoreplication"]
    expected=canonical["pseudoreplication"]
    assert pseudo["sensitivity_category"]==expected["sensitivity_category"]
    assert pseudo["robust_category_set"]==expected["robust_category_set"]
    assert pseudo["point_category_set"]==expected["point_category_set"]
    assert pseudo["group_status_flip_count"]==expected["group_status_flip_count"]
    assert result["pseudoreplication_row_iid_lower_bound"]==pytest.approx(expected["row_iid_minimum_group_lower_bound"],abs=1e-15)
    assert result["pseudoreplication_clustered_lower_bound"]==pytest.approx(expected["eight_cluster_minimum_group_lower_bound"],abs=1e-15)
    assert result["base_weight_scaling_error"]==pytest.approx(canonical["base_weight_scaling_error"],abs=1e-15)
    assert receipt["claim_boundary"]["audit_identifies_true_independence_structure"] is False
    assert receipt["claim_boundary"]["aggregate_confidence_score_emitted"] is False
    assert all(value is False for value in receipt["frozen_v4_preservation"].values())
