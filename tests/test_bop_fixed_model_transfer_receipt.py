from __future__ import annotations

import json

import pytest

from scripts.validate_bop_fixed_model_group_transfer_receipt import (
    CONTRACT, RECEIPT, validate_report,
)


def _fixture():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    contract = CONTRACT.read_bytes()
    n = 40960
    s_count = round(0.8994384765625 * n)
    shift_count = round(0.0680908203125 * n)
    assert s_count == 36841
    assert shift_count == 2789
    repeats = []
    for index in range(128):
        repeats.append({
            "replicate_index": index,
            "plan_sha256": f"{index:064x}",
            "calibration_sha256": f"{index + 128:064x}",
            "validation_groups": 320,
            "calibration_groups": 156,
            "training_groups": 80,
            "model_artifact_retrained_after_calibration": False,
            "calibration_touched_validation_labels": False,
            "same_covered": s_count // 128 + (index < s_count % 128),
            "shift_covered": shift_count // 128 + (index < shift_count % 128),
        })
    result = {
        "contract_id": "bop-fixed-model-group-transfer-known-truth-v1",
        "contract_sha256": receipt["frozen_contract_sha256"],
        "result_role": "prospective_known_truth_only_not_empirical_BOP",
        "frozen_empirical_terminal": "empirical_state_prediction_mixed",
        "empirical_result_recomputed": False,
        "n_replicates": 128,
        "strata": 4,
        "validation_groups_each_scenario": n,
        "passed": True,
        "acceptance_checks": receipt["first_result"]["checks"].copy(),
        "coverage": {
            "same_process": 0.8994384765625,
            "shifted_validation_labels_plus_two_mod_four": 0.0680908203125,
        },
        "per_replicate_provenance": repeats,
    }
    return result, receipt, contract


def test_first_result_matches_frozen_contract_and_stored_artifact_metadata():
    report, receipt, contract = _fixture()
    assert receipt["first_successful_execution"]["artifact_id"] == 12626376388
    assert receipt["first_successful_execution"]["workflow_run_id"] == 40265218136
    assert receipt["first_successful_execution"]["artifact_zip_digest"].startswith("sha256:")
    validate_report(report, receipt, contract)


@pytest.mark.parametrize("change,match", [
    ("coverage", "coverage changed"),
    ("count", "acceptance/counts"),
    ("group_provenance", "group-level audit"),
    ("contract", "scientific contract"),
    ("terminal", "real BOP terminal"),
])
def test_freeze_receipt_validator_rejects_inconsistent_replay(change, match):
    report, receipt, contract = _fixture()
    if change == "coverage":
        report["coverage"]["same_process"] = 0.90
    elif change == "count":
        report["n_replicates"] = 127
    elif change == "group_provenance":
        report["per_replicate_provenance"][0]["same_covered"] -= 1
    elif change == "contract":
        contract += b"drift"
    elif change == "terminal":
        report["frozen_empirical_terminal"] = "generalizing"
    with pytest.raises(ValueError, match=match):
        validate_report(report, receipt, contract)
