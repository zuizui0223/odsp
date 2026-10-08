"""Fail-closed checks of the FIRST outcome for a distinct unqualified route.

Receipt is explicitly post-outcome. The Monte Carlo gates and world roster
were fixed in an earlier pre-outcome committed plan.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "ODSP_FUTURE_REFIT_SHARED_EVALUE_V0_SIMULATION_PLAN.json"
RECEIPT = ROOT / "FUTURE_REFIT_SHARED_EVALUE_V0_FIRST_STATISTICAL_PANEL_RECEIPT.json"


def test_first_panel_is_sealed_to_preoutcome_plan_and_original_workflow():
    raw = PLAN.read_bytes()
    p = json.loads(raw)
    r = json.loads(RECEIPT.read_text())
    assert r["contract_sha256"] == hashlib.sha256(raw).hexdigest()
    assert p["first_result_exposed"] is False
    assert p["do_not_change_after_first_result"] is True
    assert p["replicates_per_scenario"] == r["world_repetitions"] == 1000
    assert r["first_outcome_workflow_run_id"] == 37715294839
    assert r["first_outcome_artifact_id"] == 11523267832
    assert r["method_head_sha"] == "2c8700df2db806e286e4824dfda77441ea53bd4a"
    assert r["post_outcome_receipt_materialized"] is True
    assert r["first_outcome_artifact_zip_sha256"] == (
        "3fe902df52e117de69e99426c05beef29aeaa1993293160219d71b0999080673"
    )
    assert r["primary_qualified"] is False
    assert r["registration_status"].startswith("NOT_REGISTERED")
    assert r["validation_iid_blocks_verified_in_real_ecology"] is False
    assert r["process_wide_score_support_provenance_verified"] is False
    assert r["untouched_external_endpoint_qualified"] is False
    assert r["existing_routes_reclassified"] is False


def test_all_frozen_statistical_gates_replay_from_result_not_new_thresholds():
    p = json.loads(PLAN.read_text())
    r = json.loads(RECEIPT.read_text())
    assert r["status"] == "statistical_panel_pass"
    assert r["all_required_gates_passed"] is True
    assert len(r["results"]) == 11
    by_id = {x["id"]: x for x in r["results"]}
    expected = {x[0] for x in p["coverage_cases"]}
    expected |= {x[0] for x in p["power_cases"]}
    expected |= {x[0] for x in p["diagnostic_cases"]}
    expected |= {"non_iid_blocks_shared_shock"}
    assert set(by_id) == expected
    gates = p["gates"]
    for row in r["results"]:
        assert row["n_worlds"] == p["replicates_per_scenario"]
        for field in (
            "overclaim_rate", "any_false_certificate_panel_rate",
            "probability_lower_bound_above_0p8", "all_certified_rate",
        ):
            value = row[field]
            assert math.isfinite(value)
            assert 0 <= value <= 1
        if row["role"] == "coverage":
            assert row["overclaim_rate"] <= gates["coverage_overstatement_max"]
            assert row["any_false_certificate_panel_rate"] <= (
                gates["any_false_certificate_panel_max"]
            )
        elif row["role"] == "power_required":
            assert row["probability_lower_bound_above_0p8"] >= (
                gates["each_required_power_min"]
            )
        elif row["role"] == "invalid_design_sentinel":
            assert row["overclaim_rate"] >= gates["invalid_design_overstatement_min"]
        else:
            assert row["role"] == "power_diagnostic_only"
        assert row["frozen_gate_passed"] is True


def test_small_signal_limit_and_dependence_negative_control_are_not_hidden():
    rows = {
        x["id"]: x
        for x in json.loads(RECEIPT.read_text())["results"]
    }
    assert rows["p1_small_B12"]["probability_lower_bound_above_0p8"] == 0.0
    assert rows["p1_small_B12"]["all_certified_rate"] == 0.0
    assert rows["p1_small_largeB"]["probability_lower_bound_above_0p8"] == 1.0
    assert rows["non_iid_blocks_shared_shock"]["overclaim_rate"] == 0.498
    assert rows["p0"]["any_false_certificate_panel_rate"] == 0.001
