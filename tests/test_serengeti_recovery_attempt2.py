import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_attempt2_failed_before_any_scientific_calculation():
    receipt = json.loads(
        (ROOT / "N2_SERENGETI_RECOVERY_ATTEMPT2_FAILURE.json").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["workflow_run_id"] == 33774376786
    assert receipt["failure_type"] == "overbroad_static_recovery_guard"
    assert receipt["input_download_started"] is False
    assert receipt["scientific_calculation_started"] is False
    assert receipt["scientific_outcome_accessed"] is False
    assert receipt["terminal_artifact_created"] is False
    assert receipt["scientific_contract_changed"] is False


def test_recovery_guard_checks_only_contract_authorized_old_tokens():
    workflow = (
        ROOT / ".github/workflows/n2-serengeti-terminal-recovery.yml"
    ).read_text(encoding="utf-8")

    assert "remaining = [old for old, _ in replacements if old in text]" in workflow
    assert "authorized original replacement total was not exactly five" in workflow
    assert "forbidden = ('\"outcome_opened\": true', ': false')" not in workflow
    assert "authorized_boolean_replacements=5" in workflow
