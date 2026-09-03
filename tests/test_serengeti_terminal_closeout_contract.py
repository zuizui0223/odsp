import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_closeout_contract_pins_recovery_artifact_and_validator():
    contract = json.loads(
        (ROOT / "N2_SERENGETI_TERMINAL_CLOSEOUT_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    recovery = contract["source_recovery"]
    artifact = contract["source_artifact"]
    validation = contract["validation"]

    assert recovery["recovery_workflow_run_id"] == 33774650396
    assert recovery["recovery_conclusion"] == "success"
    assert recovery["original_analysis_commit"] == "d17a204527b5426d29535ef6303bc759fe52adcc"
    assert artifact["artifact_id"] == 9901082589
    assert artifact["artifact_digest"] == "sha256:4cbba5bc2f98e0967fa6a2db37ef0e2ab893e4ee0600491b4b6eb2a70231fc78"
    assert artifact["expected_file"] == "n2_serengeti_temporal_partition_result.json"
    assert validation["receipt_schema_id"] == "n2-serengeti-terminal-receipt-v1"
    assert validation["validate_before_interpreting_numeric_result"] is True
    assert validation["terminal_summary_alone_authorizes_empirical_n3_state"] is False


def test_closeout_workflow_never_reruns_analysis_or_prints_raw_result():
    workflow = (
        ROOT / ".github/workflows/n2-serengeti-terminal-closeout.yml"
    ).read_text(encoding="utf-8")

    assert "actions/artifacts/9901082589" in workflow
    assert "33774650396" in workflow
    assert "4cbba5bc2f98e0967fa6a2db37ef0e2ab893e4ee0600491b4b6eb2a70231fc78" in workflow
    assert "scripts/validate_n2_serengeti_terminal_result.py" in workflow
    assert "run_n2_serengeti_temporal_partition.py" not in workflow
    assert "cat recovered-terminal/n2_serengeti_temporal_partition_result.json" not in workflow
    assert "n2-serengeti-temporal-terminal-receipt" in workflow
