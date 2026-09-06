from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_joint_bias_uncertainty_contract_freezes_fail_closed_rules():
    contract=json.loads((ROOT/"JOINT_BIAS_UNCERTAINTY_ROBUSTNESS_CONTRACT.json").read_text(encoding="utf-8"))
    assert contract["contract_id"]=="odsp-joint-bias-uncertainty-robustness-v1"
    design=contract["joint_design"]
    assert design["bootstrap_resamples_blocks_with_replacement"] is True
    assert design["within_each_bootstrap_draw_worst_and_best_allowed_reweighting_solved"] is True
    rule=contract["decision_rule"]
    assert rule["joint_robust_positive_requires_lower_bound_of_bootstrap_worst_case_gain_gt_zero"] is True
    assert rule["pooled_mean_can_override_group_failure"] is False
    ceiling=contract["claim_boundary"]
    assert ceiling["gamma_is_inferred_from_data"] is False
    assert ceiling["joint_robustness_proves_no_observation_bias"] is False
    assert ceiling["future_distribution_shift_robustness_guaranteed"] is False
