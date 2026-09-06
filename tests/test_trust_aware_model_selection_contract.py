from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_trust_aware_selection_contract_freezes_decision_order():
    contract = json.loads((ROOT / "TRUST_AWARE_MODEL_SELECTION_CONTRACT.json").read_text(encoding="utf-8"))
    assert contract["contract_id"] == "odsp-trust-aware-model-selection-v2"
    assert contract["rules"]["pooled_gain_can_override_group_failure"] is False
    assert contract["rules"]["pooled_coverage_can_override_group_failure"] is False
    assert contract["rules"]["sharpness_can_override_bad_coverage"] is False
    assert contract["rules"]["coverage_can_override_bad_transfer"] is False
    assert contract["rules"]["aggregate_confidence_score_emitted"] is False
    assert contract["claim_boundary"]["groupwise_empirical_coverage_is_conditional_coverage_guarantee"] is False
    assert contract["claim_boundary"]["recommended_candidate_is_true_biological_mechanism"] is False
    assert contract["frozen_v4_boundary"]["v4_manuscript_modified"] is False
    assert contract["frozen_v4_boundary"]["closed_empirical_endpoint_reopened"] is False
