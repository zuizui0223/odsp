from __future__ import annotations
import json
from pathlib import Path

P=Path("ODSP_TRAINING_SOURCE_PROCESS_V0_ROUTE_REGISTRATION_CONTRACT.json")

def test_source_v0_registration_contract_uses_distinct_upstream_mode():
    p=json.loads(P.read_text(encoding="utf-8"))
    r=p["routing"]
    assert r["new_upstream_mode"] == "predeclared_training_source_process"
    assert r["reuse_predeclared_training_process_mode"] is False
    assert r["role"] == "primary_confirmatory"
    assert r["contrast_count"] == 2
    assert r["external_validation"] == "none"
    assert r["raw_numeric_surface_primary"] is False
    assert r["managed_provenance_wrapper_primary"] is True

def test_source_v0_registration_does_not_expand_beyond_declared_source_process():
    p=json.loads(P.read_text(encoding="utf-8"))
    b=p["claim_boundary"]
    assert b["outer_source_process_conditional_on_frozen_original_source_roster"] is True
    assert b["unknown_ecological_source_superpopulation_generalization_claimed"] is False
    assert b["qualified_training_process_v5_reclassified"] is False
    assert b["fixed_set_results_reclassified"] is False
    u=p["unqualified_scope"]
    assert all(u.values())

def test_source_v0_registration_uses_predeclared_15_artifact_chain():
    p=json.loads(P.read_text(encoding="utf-8"))
    assert p["evidence"]["route_chain_artifact_count"] == 15
    assert p["evidence"]["hash_receipt_is_meta_evidence_not_route_chain_member"] is True
    assert p["prerequisites"]["hash_snapshot_completed_before_registration"] is True
