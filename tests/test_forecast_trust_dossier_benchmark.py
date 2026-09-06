from odsp.forecast_trust_dossier_benchmark import run_forecast_trust_dossier_benchmark


def test_frozen_forecast_trust_dossier_benchmark_passes():
    result = run_forecast_trust_dossier_benchmark(seed=20260906, bootstrap_draws=2000)
    assert result["passed"] is True
    assert len(result["checks"]) == 13
    assert all(row["passed"] for row in result["checks"])
    assert result["dossiers"]["robust_in_domain"]["selection"]["status"] == "recommended"
    assert result["dossiers"]["fragile_in_domain"]["validation"]["robust_validation_status"] == "blocked"
    assert result["dossiers"]["coverage_failed_in_domain"]["validation"]["groupwise_coverage_gate"] == "fail"
    assert result["dossiers"]["robust_strict_extrapolation"]["deployment"]["status"] == "strict_extrapolation_warning"
    assert result["dossiers"]["too_few_blocks"]["validation"]["robust_validation_status"] == "unavailable"
