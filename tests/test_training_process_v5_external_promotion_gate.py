from __future__ import annotations
import json
from pathlib import Path

CONTRACT=Path("ODSP_TRAINING_PROCESS_V5_EXTERNAL_PROMOTION_GATE.json")

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
