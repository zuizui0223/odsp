import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "N2_SERENGETI_TECHNICAL_RECOVERY_CONTRACT.json"
WORKFLOW = ROOT / ".github/workflows/n2-serengeti-terminal-recovery.yml"


def test_recovery_contract_pins_failed_attempt_and_original_analysis_commit():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    failed = contract["failed_authoritative_attempt"]
    assert failed["workflow_run_id"] == 33726030526
    assert failed["workflow_head_sha"] == "d17a204527b5426d29535ef6303bc759fe52adcc"
    assert failed["conclusion"] == "failure"
    assert failed["failure_type"] == "python_name_error_during_result_serialization"
    assert failed["terminal_artifact_count"] == 0
    assert failed["raw_numeric_result_logged"] is False
    assert failed["terminal_result_persisted"] is False
    assert failed["scientific_calculation_reached_before_failure"] is True

    boundary = contract["frozen_scientific_boundary"]
    assert boundary["original_analysis_commit"] == failed["workflow_head_sha"]
    assert boundary["consensus_md5"] == "5ed2d32fd09127c178cf9dca8ccfd623"
    assert boundary["effort_md5"] == "27cb42f3feaa0642b17cbde24ba15fbd"
    assert all(value is False for key, value in boundary.items() if key.startswith("change_"))
    assert boundary["inspect_or_select_on_hidden_numeric_result"] is False


def test_recovery_contract_allows_only_five_boolean_repairs():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    repair = contract["only_authorized_code_repair"]
    replacements = repair["exact_replacements"]

    assert repair["base_commit"] == "d17a204527b5426d29535ef6303bc759fe52adcc"
    assert repair["replacement_count_must_equal"] == 5
    assert len(replacements) == 5
    assert repair["other_analysis_source_changes_authorized"] is False
    assert {item["from"] for item in replacements} == {
        '"outcome_opened": true',
        '"true_activity_niche_partition_identified": false',
        '"interspecific_displacement_causality_identified": false',
        '"solar_time_partition_identified": false',
        '"bat_endpoint_reinterpreted": false',
    }


def test_recovery_workflow_uses_original_commit_and_does_not_print_result_json():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "ref: d17a204527b5426d29535ef6303bc759fe52adcc" in workflow
    assert "authorized_boolean_replacements=5" in workflow
    assert "5ed2d32fd09127c178cf9dca8ccfd623" in workflow
    assert "27cb42f3feaa0642b17cbde24ba15fbd" in workflow
    assert "cat n2_serengeti_temporal_partition_result.json" not in workflow
    assert "n2-serengeti-temporal-partition-recovered-result" in workflow
    assert "rerun" not in workflow.lower()


def test_recovery_is_not_a_bat_tawaki_or_gate_e_rescue():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    other = contract["other_endpoints"]
    assert other == {
        "tawaki_reopened": False,
        "bat_reopened": False,
        "gate_e_authorized": False,
    }
