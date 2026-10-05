from __future__ import annotations
import json
from pathlib import Path

from scripts.run_training_process_v5_external_identity import build_snapshot

CONTRACT=Path("ODSP_TRAINING_PROCESS_V5_EXTERNAL_ENDPOINT_IDENTITY_CONTRACT.json")

def test_external_identity_contract_targets_managed_scoring_endpoint():
    p=json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert p["canonical_surface"] == (
        "odsp.training_process_untouched_external_v5."
        "run_untouched_external_training_process_v5"
    )
    assert p["focused_test_requirement"]["must_pass_before_identity_receipt_is_admitted_to_route_evidence"] is True
    assert p["boundary"]["external_route_registered_by_identity_snapshot_alone"] is False

def test_external_identity_snapshot_contains_internal_route_and_contract_hashes():
    snapshot=build_snapshot()
    assert snapshot["canonical_surface"].endswith(
        "run_untouched_external_training_process_v5"
    )
    assert snapshot["implementation_source_snapshot"]
    assert snapshot["internal_v5_route_snapshot"]["role"] == "primary_confirmatory"
    assert len(snapshot["external_contract_sha256"]) == 4
    assert all(len(value)==64 for value in snapshot["external_contract_sha256"].values())
