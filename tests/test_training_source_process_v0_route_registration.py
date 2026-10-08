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


def test_source_v0_external_route_fails_closed_before_evidence_lookup():
    from odsp.confirmatory_method_routing import route_confirmatory_method

    for external_mode in ("untouched_frozen", "untouched_unfrozen"):
        route = route_confirmatory_method(
            alternative="greater",
            validation_design="independent_groups",
            information_structure="filtration",
            upstream_refits="predeclared_training_source_process",
            external_validation=external_mode,
            contrast_count=2,
        )
        assert route.role == "unqualified"
        assert route.primary_for_claim is False
        assert route.canonical_surface is None
        assert route.qualification_key is None
        assert route.requires_preoutcome_freeze is True


def test_source_v0_internal_c2_remains_qualified():
    from odsp.confirmatory_method_routing import route_confirmatory_method

    route = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="filtration",
        upstream_refits="predeclared_training_source_process",
        external_validation="none",
        contrast_count=2,
    )
    assert route.role == "primary_confirmatory"
    assert route.canonical_surface == (
        "odsp.training_source_process_managed_internal_v0."
        "run_managed_internal_training_source_process_v0"
    )
    assert route.training_source_process_generalization_claimed is True
