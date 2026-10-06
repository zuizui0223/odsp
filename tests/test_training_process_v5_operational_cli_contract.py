from __future__ import annotations

import json
from pathlib import Path


CONTRACT = Path("ODSP_TRAINING_PROCESS_V5_OPERATIONAL_CLI_CONTRACT.json")


def test_operational_cli_is_glue_not_new_inference():
    p = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert p["public_surface"]["new_top_level_command_added"] is False
    assert p["public_surface"]["namespace"] == "odsp experimental training-process"
    assert p["public_surface"]["operations"] == [
        "freeze",
        "generate",
        "external-freeze",
        "external-score",
        "external-run",
    ]
    g = p["governance"]
    assert g["changes_statistical_method"] is False
    assert g["changes_v5_operating_characteristics"] is False
    assert g["changes_route_evidence_registry"] is False
    assert g["changes_canonical_primary_surface"] is False


def test_external_run_cli_cannot_bypass_managed_score_derivation():
    p = json.loads(CONTRACT.read_text(encoding="utf-8"))
    e = p["external_run_contract"]
    assert e["caller_supplied_score_tensor_field_allowed"] is False
    assert e["reconstructs_row_group_block_weight_from_frozen_external_roster"] is True
    assert e["reconstructs_refit_ids_from_external_freeze_manifest"] is True
    assert e["calls_canonical_external_endpoint"] == (
        "odsp.training_process_untouched_external_v5."
        "run_untouched_external_training_process_v5"
    )


def test_operational_cli_is_outside_frozen_external_endpoint_identity():
    identity = json.loads(
        Path("TRAINING_PROCESS_V5_EXTERNAL_ENDPOINT_IDENTITY_RECEIPT_V2.json").read_text(
            encoding="utf-8"
        )
    )
    paths = {row["path"] for row in identity["implementation_source_snapshot"]}
    assert "odsp/cli.py" not in paths
    assert "odsp/training_process_external_contract.py" not in paths
    assert "odsp/training_process_untouched_external_v5.py" in paths
