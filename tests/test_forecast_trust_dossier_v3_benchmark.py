from odsp.forecast_trust_dossier_v3_benchmark import run_forecast_trust_dossier_v3_benchmark


def test_frozen_forecast_trust_dossier_v3_benchmark_passes():
    result=run_forecast_trust_dossier_v3_benchmark(seed=20260906,bootstrap_draws=500)
    assert result["passed"] is True
    assert len(result["checks"])==13
    assert all(row["passed"] for row in result["checks"])
    strong=result["robust_recommended_radius_through_upper"]
    assert strong["joint_radius"]["status"]=="robust_through_search_upper"
    assert strong["decision_trace"]["operational_status"]=="admitted"
    finite=result["validation_admitted_at_gamma_1_5_with_finite_radius"]
    assert finite["validation"]["validation_status"]=="admitted"
    assert finite["joint_radius"]["status"]=="finite_radius"
    assert finite["decision_trace"]["operational_status"]=="admitted_with_warnings"
    weak=result["weak_positive_validation_blocked_and_radius_not_certified"]
    assert weak["validation"]["validation_status"]=="blocked"
    assert weak["joint_radius"]["status"]=="not_certified_at_baseline"
