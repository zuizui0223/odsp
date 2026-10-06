from __future__ import annotations

import json
from pathlib import Path


CONTRACT = Path(
    "ODSP_TRAINING_SOURCE_PROCESS_V0_MANAGED_FOCUSED_RECEIPT_CONTRACT.json"
)


def test_source_v0_focused_receipt_contract_freezes_exact_test_family():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    tests = payload["required_test_files"]
    assert len(tests) == len(set(tests))
    assert "tests/test_training_source_process_managed_internal_v0.py" in tests
    assert "tests/test_training_source_process_v0_primary_promotion_v5.py" in tests
    assert "tests/test_training_source_process_v0_evidence_plan_v2.py" in tests
    rule = payload["acceptance_rule"]
    assert rule["all_listed_focused_tests_must_pass_in_one_official_github_actions_run"] is True
    assert rule["failed_test_may_not_be_dropped_post_hoc"] is True


def test_source_v0_focused_receipt_contract_covers_core_provenance_failures():
    failures = json.loads(CONTRACT.read_text(encoding="utf-8"))[
        "required_failure_modes"
    ]
    assert all(failures.values())
    assert failures["declared_first_access_after_managed_read_rejected"] is True
    assert failures["missing_source_inner_scoring_execution_rejected"] is True
    assert failures["score_bundle_byte_tampering_rejected"] is True
