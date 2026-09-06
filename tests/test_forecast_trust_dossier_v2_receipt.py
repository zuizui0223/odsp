from __future__ import annotations

import json
import math
from pathlib import Path

from odsp.forecast_trust_dossier_v2_benchmark import run_forecast_trust_dossier_v2_benchmark

ROOT=Path(__file__).resolve().parents[1]


def _close(a,b,tol=1e-15):
    return math.isclose(float(a),float(b),rel_tol=0.0,abs_tol=tol)


def test_forecast_trust_dossier_v2_receipt_replays_frozen_benchmark():
    receipt=json.loads((ROOT/"FORECAST_TRUST_DOSSIER_V2_VALIDATION_RECEIPT.json").read_text(encoding="utf-8"))
    result=run_forecast_trust_dossier_v2_benchmark(seed=20260906,bootstrap_draws=1000)
    canonical=receipt["canonical_results"]
    assert result["passed"] is canonical["passed"] is True
    assert len(result["checks"])==canonical["obligation_count"]==12
    assert all(row["passed"] for row in result["checks"])

    robust=result["robust_recommended_in_domain"]
    expected=canonical["robust_recommended_in_domain"]
    assert robust["validation"]["validation_status"]==expected["validation_status"]
    assert robust["decision_trace"]["operational_status"]==expected["operational_status"]
    assert robust["selection"]["status"]==expected["selection_status"]
    assert _close(robust["validation"]["mean_log_density_gain"],expected["mean_log_density_gain"])
    assert _close(robust["validation"]["minimum_worst_case_lower_bound"],expected["minimum_worst_case_lower_bound"])
    assert robust["robustness_profile"]["sampling_weight_status"]==expected["sampling_weight_status"]
    assert robust["robustness_profile"]["bounded_reweighting_status"]==expected["bounded_reweighting_status"]
    assert len(robust["decision_trace"]["warning_reasons"])==expected["warning_count"]

    strict=result["robust_recommended_strict_extrapolation"]
    expected=canonical["robust_recommended_strict_extrapolation"]
    assert strict["validation"]["validation_status"]==expected["validation_status"]
    assert strict["decision_trace"]["operational_status"]==expected["operational_status"]
    assert strict["deployment"]["status"]==expected["deployment_status"]
    assert _close(strict["deployment"]["strict_extrapolation_fraction"],expected["strict_extrapolation_fraction"])
    assert _close(strict["deployment"]["maximum_novelty_ratio"],expected["maximum_novelty_ratio"])
    assert strict["decision_trace"]["warning_reasons"]==expected["warning_reasons"]

    sensitive=result["validation_admitted_but_sampling_weight_sensitive"]
    expected=canonical["validation_admitted_but_sampling_weight_sensitive"]
    assert sensitive["validation"]["validation_status"]==expected["validation_status"]
    assert sensitive["decision_trace"]["operational_status"]==expected["operational_status"]
    assert sensitive["robustness_profile"]["sampling_weight_status"]==expected["sampling_weight_status"]
    assert _close(sensitive["robustness_profile"]["minimum_scenario_mean_gain"],expected["minimum_scenario_mean_gain"])
    assert _close(sensitive["robustness_profile"]["maximum_scenario_mean_gain"],expected["maximum_scenario_mean_gain"])
    assert sensitive["robustness_profile"]["sampling_group_status_flip_count"]==expected["sampling_group_status_flip_count"]
    assert sensitive["robustness_profile"]["bounded_reweighting_status"]==expected["bounded_reweighting_status"]
    assert _close(sensitive["robustness_profile"]["minimum_critical_gamma"],expected["minimum_critical_gamma"])
    assert sensitive["decision_trace"]["warning_reasons"]==expected["warning_reasons"]

    breakpoint=result["validation_admitted_at_gamma_1_5_but_breaks_by_gamma_2"]
    expected=canonical["validation_admitted_at_gamma_1_5_but_breaks_by_gamma_2"]
    assert breakpoint["validation"]["validation_status"]==expected["validation_status"]
    assert breakpoint["decision_trace"]["operational_status"]==expected["operational_status"]
    assert _close(breakpoint["validation"]["validation_gamma"],expected["validation_gamma"])
    assert _close(breakpoint["validation"]["minimum_worst_case_lower_bound"],expected["validation_minimum_worst_case_lower_bound"])
    assert _close(breakpoint["robustness_profile"]["bounded_gamma"],expected["bounded_gamma"])
    assert breakpoint["robustness_profile"]["bounded_reweighting_status"]==expected["bounded_reweighting_status"]
    assert _close(breakpoint["robustness_profile"]["minimum_worst_case_group_gain"],expected["bounded_minimum_worst_case_group_gain"])
    assert _close(breakpoint["robustness_profile"]["minimum_critical_gamma"],expected["minimum_critical_gamma"])
    assert breakpoint["robustness_profile"]["critical_gamma_group_count"]==expected["critical_gamma_group_count"]
    assert breakpoint["decision_trace"]["warning_reasons"]==expected["warning_reasons"]

    blocked=result["joint_envelope_sensitive_validation_blocked"]
    expected=canonical["joint_envelope_sensitive_validation_blocked"]
    assert blocked["validation"]["validation_status"]==expected["validation_status"]
    assert blocked["validation"]["joint_robustness_category"]==expected["joint_robustness_category"]
    assert _close(blocked["validation"]["minimum_worst_case_lower_bound"],expected["minimum_worst_case_lower_bound"])
    assert blocked["validation"]["blocking_reasons"]==expected["blocking_reasons"]

    unavailable=result["too_few_blocks_validation_unavailable"]
    expected=canonical["too_few_blocks_validation_unavailable"]
    assert unavailable["validation"]["validation_status"]==expected["validation_status"]
    assert unavailable["validation"]["joint_robustness_category"]==expected["joint_robustness_category"]
    assert unavailable["validation"]["blocking_reasons"]==expected["blocking_reasons"]

    broad=result["robust_broad_not_pareto"]
    expected=canonical["robust_broad_not_pareto"]
    assert broad["validation"]["validation_status"]==expected["validation_status"]
    assert broad["selection"]["status"]==expected["selection_status"]
    assert broad["selection"]["bias_robust_trusted"] is expected["bias_robust_trusted"]
    assert broad["selection"]["pareto_member"] is expected["pareto_member"]

    assert result["selection"]["recommended_by_log_score"]==canonical["selection_recommendation"]
    assert canonical["aggregate_confidence_score_emitted"] is False
    assert receipt["claim_boundary"]["dossier_adds_new_statistical_evidence"] is False
    assert receipt["claim_boundary"]["sampling_weight_stability_proves_no_observation_bias"] is False
    assert receipt["claim_boundary"]["novelty_is_error_probability"] is False
    assert receipt["frozen_v4_preservation"]["closed_empirical_endpoint_reopened"] is False
