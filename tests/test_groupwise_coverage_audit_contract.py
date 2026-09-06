from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_groupwise_coverage_contract_freezes_fail_closed_claims():
    contract = json.loads((ROOT / "GROUPWISE_COVERAGE_AUDIT_CONTRACT.json").read_text(encoding="utf-8"))
    assert contract["contract_id"] == "odsp-groupwise-coverage-audit-v1"
    assert contract["coverage_semantics"]["groupwise_audit_is_conditional_coverage_guarantee"] is False
    assert contract["coverage_semantics"]["pooled_coverage_can_override_group_failure"] is False
    assert contract["trusted_admission"]["requires_positive_transfer_gain_in_every_independent_group"] is True
    assert contract["trusted_admission"]["requires_coverage_within_tolerance_in_every_independent_group"] is True
    assert contract["trusted_admission"]["aggregate_confidence_score_emitted"] is False
    assert contract["claim_boundary"]["good_coverage_proves_transferability"] is False
    assert contract["claim_boundary"]["positive_transfer_proves_calibration"] is False
    assert contract["frozen_v4_boundary"]["v4_manuscript_modified"] is False
    assert contract["frozen_v4_boundary"]["closed_empirical_endpoint_reopened"] is False
