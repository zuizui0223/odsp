from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_block_aware_transfer_contract_freezes_fail_closed_rules():
    contract = json.loads(
        (ROOT / "BLOCK_AWARE_TRANSFER_UNCERTAINTY_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["contract_id"] == "odsp-block-aware-transfer-uncertainty-v1"
    assert contract["bootstrap_design"]["minimum_blocks_per_group"] == 8
    assert contract["bootstrap_design"]["rows_within_resampled_block_kept_together"] is True
    rule = contract["decision_rule"]
    assert rule["robust_positive_requires_lower_bound_gt_zero"] is True
    assert rule["interval_crossing_zero_is_uncertain"] is True
    assert rule["too_few_blocks_is_unavailable"] is True
    assert rule["pooled_mean_can_override_group_failure"] is False
    assert rule["point_estimate_can_override_uncertainty"] is False
    assert rule["aggregate_confidence_score_emitted"] is False
    ceiling = contract["claim_boundary"]
    assert ceiling["bootstrap_interval_is_exact_finite_sample_guarantee"] is False
    assert ceiling["block_bootstrap_repairs_wrong_block_definition"] is False
    assert ceiling["robust_transfer_guarantees_future_distribution_shift_performance"] is False
