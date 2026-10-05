from __future__ import annotations
import json
from pathlib import Path

CONTRACT=Path("ODSP_TRAINING_PROCESS_V5_EXTERNAL_PROMOTION_GATE.json")
CONTRACT_V2=Path("ODSP_TRAINING_PROCESS_V5_EXTERNAL_PROMOTION_GATE_V2.json")
CONTRACT_V3=Path("ODSP_TRAINING_PROCESS_V5_EXTERNAL_PROMOTION_GATE_V3.json")


def test_external_promotion_gate_is_narrow_and_post_evidence():
    p=json.loads(CONTRACT.read_text(encoding="utf-8"))
    r=p["prospective_route"]
    assert r["upstream_refits"] == "predeclared_training_process"
    assert r["external_validation"] == "untouched_frozen"
    assert r["contrast_count"] == 2
    assert p["focused_endpoint_gate"]["happy_path_must_use_managed_score_bundle"] is True
    assert p["registration_rule"]["route_registry_update_must_occur_after_all_evidence_receipts_exist"] is True
    assert p["registration_rule"]["external_c4_process_route_promoted"] is False
    assert p["registration_rule"]["external_paired_process_route_promoted"] is False


def test_external_gate_reuses_stats_without_claiming_shift_robustness():
    p=json.loads(CONTRACT.read_text(encoding="utf-8"))
    s=p["statistical_method"]
    assert s["new_statistical_calibration_for_external_endpoint_required"] is False
    assert s["internal_v5_base_qualification_required"] is True
    assert s["internal_v5_adversarial_support_required"] is True
    assert s["external_distribution_shift_robustness_claimed"] is False


def test_v2_promotion_gate_requires_self_reference_free_final_identity():
    p=json.loads(CONTRACT_V2.read_text(encoding="utf-8"))
    assert p["self_reference_gate"][
        "external_endpoint_source_closure_must_not_include_confirmatory_method_routing_py"
    ] is True
    assert p["self_reference_gate"][
        "external_endpoint_source_closure_must_not_include_confirmatory_route_evidence_py"
    ] is True
    assert p["self_reference_gate"][
        "routing_registry_update_occurs_only_after_final_identity_receipt"
    ] is True
    assert p["scope"]["external_c2_independent_filtration_promoted_if_all_evidence_passes"] is True
    assert p["scope"]["external_c4_process_route_promoted"] is False


def test_v3_promotion_gate_requires_final_chronology_receipts_before_registration():
    p=json.loads(CONTRACT_V3.read_text(encoding="utf-8"))
    assert p["final_additional_requirement"][
        "external_outcomes_first_accessed_at_utc_required"
    ] is True
    assert p["final_additional_requirement"][
        "freeze_strictly_precedes_declared_first_access"
    ] is True
    assert p["registration_rule"]["final_post_chronology_focused_receipt_required"] is True
    assert p["registration_rule"]["final_post_chronology_identity_receipt_required"] is True
    assert p["registration_rule"][
        "route_registry_update_occurs_only_after_both_receipts"
    ] is True
    assert p["scope"]["external_c2_independent_filtration_only"] is True
    assert p["scope"]["external_c4_process_route_promoted"] is False
    assert p["claim_boundary"]["historical_truth_of_access_declaration_machine_proven"] is False
