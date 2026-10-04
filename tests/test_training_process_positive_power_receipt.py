from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "TRAINING_PROCESS_POSITIVE_POWER_CALIBRATION_RECEIPT.json"


def test_first_training_process_power_gate_is_frozen_as_failure():
    payload = json.loads(RECEIPT.read_text(encoding="utf-8"))
    run = payload["first_1000_simulation_run"]
    assert run["github_actions_run_id"] == 37210129138
    assert run["github_actions_job_id"] == 111459445739
    assert run["head_sha"] == "ec0fd15a90e117757bd18100ecfa830b1e02adba"
    assert payload["summary"]["qualification_pass"] is False
    assert payload["summary"]["pass_count"] == 1
    assert payload["summary"]["fail_count"] == 5

    rows = {row["scenario_id"]: row for row in payload["scenarios"]}
    assert rows["balanced-normal-r20-b20"]["acceptance_pass"] is True
    assert rows["balanced-normal-r20-b20"]["strong_terminal_power"] == 0.84
    assert rows["validation-dominant-normal-r20-b8"]["strong_terminal_power"] == 0.086
    assert all(row["monotonic_power"] for row in rows.values())


def test_failed_power_gate_cannot_be_reinterpreted_as_v1_qualification():
    boundary = json.loads(RECEIPT.read_text(encoding="utf-8"))[
        "qualification_boundary"
    ]
    assert boundary["v1_power_gate_failed"] is True
    assert boundary["v1_primary_promotion_allowed"] is False
    assert boundary["null_qualification_remains_valid"] is True
    assert boundary["power_threshold_or_effect_sizes_may_be_changed_post_hoc_to_rescue_v1"] is False
    assert boundary["successor_method_requires_new_predeclared_null_and_power_qualification"] is True
