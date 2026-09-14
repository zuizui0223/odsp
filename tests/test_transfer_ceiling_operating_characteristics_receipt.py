from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_frozen_transfer_ceiling_receipt_records_power_and_overreach_separately():
    receipt = json.loads(
        (ROOT / "TRANSFER_CEILING_OPERATING_CHARACTERISTICS_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["receipt_type"] == "odsp_transfer_ceiling_v2_mixed_truth_operating_characteristics"
    assert receipt["generator_version"] == "analytic_independent_group_two_step_mixed_truth_v1"
    assert receipt["empirical_endpoint"] is False
    assert receipt["frozen_endpoint_reclassified"] is False
    scenarios = {row["scenario_id"]: row for row in receipt["scenarios"]}
    assert scenarios["strong-full-normal-b20"]["exact_ceiling_recovery_rate"] == 0.986
    assert scenarios["strong-full-normal-b50"]["exact_ceiling_recovery_rate"] == 1.0
    assert scenarios["weak-full-normal-b20"]["exact_ceiling_recovery_rate"] == 0.011
    assert scenarios["coarse-null-normal-b20"]["overreach_rate"] == 0.0
    assert scenarios["coarse-adverse-normal-b20"]["overreach_rate"] == 0.0
    assert scenarios["coarse-null-t3-b20"]["exact_ceiling_recovery_rate"] == 0.588
    assert scenarios["coarse-null-t3-b20"]["underreach_rate"] == 0.412
    assert all(row["acceptance_pass"] is True for row in scenarios.values())
    boundary = receipt["scientific_boundary"]
    assert boundary["weak_positive_power_used_for_qualification"] is False
    assert "one-sided familywise lower" in boundary["next_method_question_identified"]
