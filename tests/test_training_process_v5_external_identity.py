from __future__ import annotations
import json
from pathlib import Path

from scripts.run_training_process_v5_external_identity import build_snapshot

CONTRACT=Path("ODSP_TRAINING_PROCESS_V5_EXTERNAL_ENDPOINT_IDENTITY_CONTRACT.json")
CONTRACT_V2=Path("ODSP_TRAINING_PROCESS_V5_EXTERNAL_ENDPOINT_IDENTITY_CONTRACT_V2.json")


def test_external_identity_contract_targets_managed_scoring_endpoint():
    p=json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert p["canonical_surface"] == (
        "odsp.training_process_untouched_external_v5."
        "run_untouched_external_training_process_v5"
    )
    assert p["focused_test_requirement"]["must_pass_before_identity_receipt_is_admitted_to_route_evidence"] is True
    assert p["boundary"]["external_route_registered_by_identity_snapshot_alone"] is False


def test_v2_identity_contract_removes_live_routing_self_reference():
    p=json.loads(CONTRACT_V2.read_text(encoding="utf-8"))
    binding=p["internal_v5_evidence_binding"]
    assert binding["live_route_lookup_used_by_external_endpoint"] is False
    assert binding["live_route_registry_imported_by_external_endpoint"] is False
    assert binding["live_method_routing_imported_by_external_endpoint"] is False
    assert binding["artifact_bytes_reverified_at_runtime"] is True
    assert p["snapshot_requirements"]["confirmatory_routing_modules_absent_from_source_closure"] is True


def test_external_identity_snapshot_contains_frozen_internal_route_and_contract_hashes():
    snapshot=build_snapshot()
    assert snapshot["schema_version"] == 2
    assert snapshot["canonical_surface"].endswith(
        "run_untouched_external_training_process_v5"
    )
    paths=[row["path"] for row in snapshot["implementation_source_snapshot"]]
    assert "odsp/training_process_internal_qualification_v5.py" in paths
    assert "odsp/confirmatory_method_routing.py" not in paths
    assert "odsp/confirmatory_route_evidence.py" not in paths
    assert snapshot["internal_v5_route_snapshot"]["role"] == "primary_confirmatory"
    assert snapshot["internal_v5_route_snapshot"]["qualification_registry_id"] == (
        "odsp-confirmatory-route-evidence-v4"
    )
    assert len(snapshot["external_contract_sha256"]) == 6
    assert all(len(value)==64 for value in snapshot["external_contract_sha256"].values())
