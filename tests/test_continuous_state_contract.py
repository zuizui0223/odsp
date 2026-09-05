from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "CONTINUOUS_STATE_PREDICTION_CONTRACT.json"
V4_RECEIPT = ROOT / "N2_MEE_STATE_PREDICTION_V4_FINAL_READINESS_RECEIPT.json"


def test_continuous_contract_fixes_primary_score_and_conservative_independence():
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert c["contract_id"] == "odsp-continuous-state-prediction-v1"
    assert c["primary_target"] == "p(a|X) for one real-valued ecological state a"
    assert "log p_train(a|X)" in c["primary_transfer_score"]
    independence = c["independence"]
    assert independence["groups_scored_separately"] is True
    assert independence["all_positive_required_for_generalizing"] is True
    assert independence["mixed_signs_remain_mixed"] is True
    assert independence["pooled_mean_may_rescue_conflicting_group"] is False


def test_continuous_contract_keeps_reference_learner_and_semantics_narrow():
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    learner = c["reference_learner"]
    assert learner["name"] == "weighted linear Gaussian state model"
    boundary = c["semantic_boundary"]
    assert not any(boundary.values())
    assert "circular time density" in c["out_of_scope"]
    assert "multivariate continuous response density" in c["out_of_scope"]


def test_continuous_extension_does_not_rewrite_frozen_v4_empirical_state():
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    frozen = c["frozen_v4_preservation"]
    assert not any(frozen.values())

    r = json.loads(V4_RECEIPT.read_text(encoding="utf-8"))
    assert r["prospective_empirical_prediction"]["MH_ANTWERPEN"]["terminal_category"] == "empirical_state_prediction_unavailable"
    assert r["prospective_empirical_prediction"]["BOP_RODENT"]["terminal_category"] == "empirical_state_prediction_mixed"
    assert r["prospective_empirical_prediction"]["BOP_RODENT"]["primary_positive_log_gain_individuals"] == 27
