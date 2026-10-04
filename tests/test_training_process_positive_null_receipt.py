from __future__ import annotations

import json
import math
from pathlib import Path

from odsp.training_process_positive_calibration import GENERATOR_VERSION, SCENARIOS


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "TRAINING_PROCESS_POSITIVE_NULL_CALIBRATION_RECEIPT.json"
CONTRACT = ROOT / "ODSP_TRAINING_PROCESS_POSITIVE_NULL_CALIBRATION_CONTRACT.json"


def test_first_1000_training_process_null_receipt_is_frozen_and_passes():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    run = receipt["first_1000_simulation_run"]
    assert run["github_actions_run_id"] == 37209364216
    assert run["github_actions_job_id"] == 111457203682
    assert run["head_sha"] == "59bb51d22891ba1af3a36f24fa24cf3a33b781b9"
    assert run["generator_version"] == GENERATOR_VERSION
    assert run["simulations_per_scenario"] == 1000
    assert run["bootstrap_draws_per_interval"] == 500
    assert run["contrast_count"] == 2

    assert receipt["summary"]["qualification_pass"] is True
    assert receipt["summary"]["pass_count"] == len(SCENARIOS) == 6
    assert receipt["summary"]["fail_count"] == 0

    frozen = {row["scenario_id"]: row for row in receipt["scenarios"]}
    assert set(frozen) == {row[0] for row in SCENARIOS}
    for scenario_id, distribution, refits, blocks, train_sd, valid_sd, interaction_sd in SCENARIOS:
        row = frozen[scenario_id]
        assert row["distribution"] == distribution
        assert row["refit_count"] == refits
        assert row["blocks_per_group"] == blocks
        assert row["training_sd"] == train_sd
        assert row["validation_sd"] == valid_sd
        assert row["interaction_sd"] == interaction_sd
        assert row["acceptance_pass"] is True
        assert row["one_sided_familywise_false_positive_rate"] <= row["maximum_accepted_rate"]
        assert row["terminal_false_generalizing_rate"] == 0.0
        assert row["infinite_critical_value_rate"] == 0.0

    expected = contract["acceptance_rule"]["maximum_accepted_rate_at_1000_simulations"]
    observed = receipt["acceptance_rule"]["implementation_float_maximum_accepted_rate"]
    assert abs(float(observed) - float(expected)) < 1e-15
    formula = 0.05 + 2.0 * math.sqrt(0.05 * 0.95 / 1000.0)
    assert abs(float(expected) - formula) < 1e-15


def test_null_receipt_does_not_promote_process_route_by_itself():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    boundary = receipt["qualification_boundary"]
    assert boundary["null_operating_characteristics_qualified_for_c2_independent_filtration"] is True
    assert boundary["null_result_alone_promotes_primary_route"] is False
    assert boundary["power_qualification_still_required"] is True
    assert boundary["training_process_generation_provenance_still_required"] is True
    assert boundary["untouched_external_endpoint_qualified"] is False
