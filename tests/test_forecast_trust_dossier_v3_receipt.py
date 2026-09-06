import json
import math
from pathlib import Path

from odsp.forecast_trust_dossier_v3_benchmark import run_forecast_trust_dossier_v3_benchmark


RECEIPT=Path("FORECAST_TRUST_DOSSIER_V3_VALIDATION_RECEIPT.json")
CONTRACT=Path("FORECAST_TRUST_DOSSIER_V3_CONTRACT.json")


def test_forecast_trust_dossier_v3_receipt_replays_frozen_benchmark():
    receipt=json.loads(RECEIPT.read_text())
    contract=json.loads(CONTRACT.read_text())
    result=run_forecast_trust_dossier_v3_benchmark(seed=20260906,bootstrap_draws=500)

    assert receipt["schema_version"]==1
    assert receipt["contract"]==CONTRACT.name
    assert contract["contract_id"]=="odsp-forecast-trust-dossier-v3-radius"
    assert result["passed"] is True
    assert len(result["checks"])==receipt["canonical_results"]["obligation_count"]==13
    assert all(row["passed"] for row in result["checks"])

    strong=result["robust_recommended_radius_through_upper"]
    rs=receipt["canonical_results"]["robust_recommended"]
    assert strong["validation"]["validation_status"]==rs["validation_status"]
    assert strong["decision_trace"]["operational_status"]==rs["operational_status"]
    assert strong["selection"]["status"]==rs["selection_status"]
    assert strong["joint_radius"]["status"]==rs["joint_radius_status"]
    assert strong["joint_radius"]["certified_gamma"]==rs["certified_gamma"]
    assert strong["joint_radius"]["radius_is_lower_bound_only"] is rs["radius_is_lower_bound_only"]
    assert strong["joint_radius"]["certified_maximum_multiplier_ratio"]==rs["certified_maximum_multiplier_ratio"]

    finite=result["validation_admitted_at_gamma_1_5_with_finite_radius"]
    rf=receipt["canonical_results"]["finite_radius"]
    assert finite["validation"]["validation_status"]==rf["validation_status"]
    assert finite["validation"]["validation_gamma"]==rf["validation_gamma"]
    assert finite["decision_trace"]["operational_status"]==rf["operational_status"]
    assert finite["joint_radius"]["status"]==rf["joint_radius_status"]
    assert math.isclose(finite["joint_radius"]["certified_gamma"],rf["certified_gamma"],abs_tol=1e-15)
    assert math.isclose(finite["joint_radius"]["break_gamma"],rf["break_gamma"],abs_tol=1e-15)
    assert math.isclose(finite["joint_radius"]["boundary_interval_width"],rf["boundary_interval_width"],abs_tol=1e-18)
    assert finite["joint_radius"]["limiting_group_count"]==rf["limiting_group_count"]
    assert math.isclose(abs(finite["joint_radius"]["break_gamma"]-math.sqrt(3.0)),rf["break_gamma_error_vs_sqrt3"],abs_tol=1e-15)

    strict=result["finite_radius_plus_strict_extrapolation"]
    expected=set(receipt["canonical_results"]["finite_radius_plus_strict_extrapolation"]["warning_set"])
    assert set(strict["decision_trace"]["warning_reasons"])==expected
    assert len(strict["decision_trace"]["warning_reasons"])==2

    weak=result["weak_positive_validation_blocked_and_radius_not_certified"]
    rw=receipt["canonical_results"]["weak_positive"]
    assert weak["validation"]["validation_status"]==rw["validation_status"]
    assert weak["validation"]["joint_robustness_category"]==rw["joint_robustness_category"]
    assert weak["joint_radius"]["status"]==rw["joint_radius_status"]
    assert math.isclose(weak["validation"]["minimum_worst_case_lower_bound"],rw["minimum_worst_case_lower_bound"],abs_tol=1e-15)

    few=result["too_few_blocks_validation_and_radius_unavailable"]
    rfe=receipt["canonical_results"]["too_few_blocks"]
    assert few["validation"]["validation_status"]==rfe["validation_status"]
    assert few["joint_radius"]["status"]==rfe["joint_radius_status"]
    assert few["joint_radius"]["limiting_group_count"]==rfe["limiting_group_count"]

    broad=result["robust_broad_not_pareto_with_radius"]
    rb=receipt["canonical_results"]["robust_broad"]
    assert broad["validation"]["validation_status"]==rb["validation_status"]
    assert broad["selection"]["status"]==rb["selection_status"]
    assert broad["joint_radius"]["status"]==rb["joint_radius_status"]
    assert result["selection"]["recommended_by_log_score"]==receipt["canonical_results"]["selection_recommended"]

    assert receipt["claim_boundary"]==contract["claim_boundary"]
    assert receipt["frozen_v4_preservation"]==contract["frozen_v4_boundary"]
    assert receipt["canonical_results"]["aggregate_confidence_score_emitted"] is False
    assert receipt["pre_green_diagnostic"]["scientific_logic_changed"] is False
    assert receipt["pre_green_diagnostic"]["threshold_changed"] is False
