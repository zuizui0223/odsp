from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_bounded_reweighting_contract_freezes_claim_boundaries():
    contract=json.loads((ROOT/"BOUNDED_REWEIGHTING_ROBUSTNESS_CONTRACT.json").read_text(encoding="utf-8"))
    assert contract["contract_id"]=="odsp-bounded-reweighting-robustness-v1"
    env=contract["weight_envelope"]
    assert env["allowed_multiplier_interval"]=="[1/gamma, gamma] independently for every validation row"
    assert env["normalization_irrelevant"] is True
    rule=contract["decision_rule"]
    assert rule["group_robust_positive_requires_worst_case_gain_gt_zero"] is True
    assert rule["pooled_mean_can_override_group_failure"] is False
    assert rule["automatic_bias_correction_performed"] is False
    ceiling=contract["claim_boundary"]
    assert ceiling["gamma_is_inferred_from_data"] is False
    assert ceiling["robustness_within_gamma_proves_no_observation_bias"] is False
    assert ceiling["deterministic_envelope_is_sampling_uncertainty_interval"] is False
