import json
import math
from pathlib import Path

import pytest


pytest.importorskip("sklearn")

from odsp.forecast_assessment_benchmark import run_forecast_assessment_benchmark


ROOT = Path(__file__).resolve().parents[1]


def _close(actual, expected, *, tol=1e-12):
    assert math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=tol)


def test_forecast_assessment_validation_receipt_replays_known_truth():
    receipt = json.loads(
        (ROOT / "FORECAST_ASSESSMENT_VALIDATION_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    cfg = receipt["benchmark_config"]
    result = run_forecast_assessment_benchmark(
        seed=cfg["seed"], bootstrap_draws=cfg["bootstrap_draws"]
    )
    canonical = receipt["canonical_results"]

    assert result["passed"] is True
    assert len(result["checks"]) == canonical["obligation_count"] == 13
    assert all(row["passed"] for row in result["checks"])
    assert canonical["passed"] is True

    strong = result["strong_full"]
    strong_c = canonical["strong_full"]
    assert strong["dossier"]["validation"]["validation_status"] == strong_c["validation_status"]
    assert strong["dossier"]["decision_trace"]["operational_status"] == strong_c["operational_status"]
    assert strong["dossier"]["robustness_profile"]["sampling_weight_status"] == strong_c["sampling_weight_status"]
    assert strong["dossier"]["robustness_profile"]["bounded_reweighting_status"] == strong_c["bounded_reweighting_status"]
    assert strong["dossier"]["selection"]["status"] == strong_c["selection_status"]
    assert strong["joint_radius"]["status"] == strong_c["radius_status"]
    _close(strong["joint_radius"]["certified_gamma"], strong_c["certified_gamma"])

    strict = result["strong_strict_extrapolation"]
    strict_c = canonical["strict_extrapolation"]
    assert strict["dossier"]["validation"]["validation_status"] == strict_c["validation_status"]
    assert strict["dossier"]["deployment"]["status"] == strict_c["deployment_status"]
    assert strict["dossier"]["decision_trace"]["operational_status"] == strict_c["operational_status"]
    assert strict["dossier"]["decision_trace"]["warning_reasons"] == strict_c["warning_reasons"]

    weight = result["weight_sensitive"]
    weight_c = canonical["weight_sensitive"]
    assert weight["dossier"]["validation"]["validation_status"] == weight_c["validation_status"]
    assert weight["dossier"]["decision_trace"]["operational_status"] == weight_c["operational_status"]
    assert weight["sampling_weight_audit"]["sensitivity_category"] == weight_c["sampling_weight_status"]
    _close(weight["sampling_weight_audit"]["minimum_scenario_mean_gain"], weight_c["minimum_scenario_mean_gain"])
    _close(weight["sampling_weight_audit"]["maximum_scenario_mean_gain"], weight_c["maximum_scenario_mean_gain"])

    finite = result["finite_radius"]
    finite_c = canonical["finite_radius"]
    assert finite["dossier"]["validation"]["validation_status"] == finite_c["validation_status"]
    _close(finite["dossier"]["validation"]["validation_gamma"], finite_c["validation_gamma"])
    assert finite["dossier"]["robustness_profile"]["bounded_reweighting_status"] == finite_c["bounded_status"]
    _close(finite["dossier"]["robustness_profile"]["minimum_critical_gamma"], finite_c["minimum_critical_gamma"])
    assert finite["joint_radius"]["status"] == finite_c["radius_status"]
    _close(finite["joint_radius"]["certified_gamma"], finite_c["certified_gamma"])
    _close(finite["joint_radius"]["break_gamma"], finite_c["break_gamma"])
    _close(finite["joint_radius"]["boundary_interval_width"], finite_c["boundary_interval_width"])

    weak = result["weak_positive"]
    weak_c = canonical["weak_positive"]
    assert weak["dossier"]["validation"]["validation_status"] == weak_c["validation_status"]
    assert weak["dossier"]["decision_trace"]["operational_status"] == weak_c["operational_status"]
    assert weak["dossier"]["decision_trace"]["blocking_reasons"] == weak_c["blocking_reasons"]

    few = result["too_few_blocks"]
    few_c = canonical["too_few_blocks"]
    assert few["dossier"]["validation"]["validation_status"] == few_c["validation_status"]
    assert few["dossier"]["decision_trace"]["operational_status"] == few_c["operational_status"]
    assert few["dossier"]["decision_trace"]["blocking_reasons"] == few_c["blocking_reasons"]

    omitted = result["strong_optional_layers_omitted"]
    omitted_c = canonical["optional_layers_omitted"]
    assert omitted["dossier"]["robustness_profile"]["sampling_weight_status"] == omitted_c["sampling_weight_status"]
    assert omitted["dossier"]["robustness_profile"]["bounded_reweighting_status"] == omitted_c["bounded_reweighting_status"]
    assert omitted["dossier"]["deployment"]["status"] == omitted_c["deployment_status"]
    assert omitted["joint_radius"]["status"] == omitted_c["radius_status"]

    assert result["strong_full"]["aggregate_confidence_score_emitted"] is False
    assert receipt["claim_boundary"]["aggregate_confidence_score_emitted"] is False
    assert receipt["claim_boundary"]["creates_new_statistical_estimand"] is False
    assert all(value is False for value in receipt["frozen_v4_preservation"].values())
