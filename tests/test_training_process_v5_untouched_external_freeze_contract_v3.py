from __future__ import annotations
import json
from pathlib import Path

CONTRACT=Path("ODSP_TRAINING_PROCESS_V5_UNTOUCHED_EXTERNAL_FREEZE_CONTRACT_V3.json")


def test_v3_external_contract_requires_declared_access_chronology():
    p=json.loads(CONTRACT.read_text(encoding="utf-8"))
    c=p["chronology"]
    assert c["external_outcomes_first_accessed_at_utc_required"] is True
    assert c["required_relation"] == (
        "frozen_at_utc < external_outcomes_first_accessed_at_utc"
    )
    assert c["relation_machine_verified"] is True
    assert c["historical_truth_of_first_access_declaration_machine_proven"] is False
    assert c["trusted_timestamp_authority_used"] is False


def test_v3_keeps_untouched_claim_narrow():
    b=json.loads(CONTRACT.read_text(encoding="utf-8"))["claim_boundary"]
    assert b[
        "untouched_external_means_predeclared_freeze_precedes_declared_first_outcome_access"
    ] is True
    assert b["historical_no_prior_external_outcome_access_machine_proven"] is False
    assert b["external_distribution_shift_robustness_claimed"] is False
    assert b["fixed_set_results_reclassified"] is False
