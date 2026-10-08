from __future__ import annotations
import json
from pathlib import Path

P=Path("TRAINING_SOURCE_PROCESS_V0_BASE_QUALIFICATION_RECEIPT.json")


def test_source_v0_base_receipt_freezes_first_opened_result():
    p=json.loads(P.read_text(encoding="utf-8"))
    assert p["qualification_head_sha"] == "ba03f625c351619bb7f1bdba7c3c27d5f7ec94db"
    assert p["null_run"]["github_actions_run_id"] == 37391884203
    assert p["power_run"]["github_actions_run_id"] == 37391884204
    assert p["summary"]["base_qualification_pass"] is True
    assert p["summary"]["largest_component_false_positive_rate"] == 0.058
    assert p["summary"]["smallest_strong_terminal_power"] == 0.850
    assert p["chronology"]["first_workflow_attempt_reached_calibration_result"] is False


def test_source_v0_receipt_does_not_promote_route_or_expand_population_claim():
    p=json.loads(P.read_text(encoding="utf-8"))
    q=p["qualification_boundary"]
    assert q["primary_confirmatory_now"] is False
    assert q["route_registered"] is False
    assert q["adversarial_support_still_required"] is True
    b=p["scientific_boundary"]
    assert b["original_ecological_source_superpopulation_generalization_claimed"] is False
    assert b["fixed_set_results_reclassified"] is False
    assert b["qualified_training_process_v5_results_reclassified"] is False


def test_inner_dominant_scenario_passed_without_counting_inner_refits_as_sources():
    p=json.loads(P.read_text(encoding="utf-8"))
    assert p["summary"]["inner_dominant_null_rate_max"] == 0.051
    assert p["summary"]["inner_dominant_strong_terminal_power"] == 0.993
