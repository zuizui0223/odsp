from odsp.forecast_trust_dossier_v2_benchmark import run_forecast_trust_dossier_v2_benchmark


def test_frozen_forecast_trust_dossier_v2_benchmark_passes():
    result=run_forecast_trust_dossier_v2_benchmark(seed=20260906,bootstrap_draws=1000)
    assert result["passed"] is True
    assert len(result["checks"])==12
    assert all(row["passed"] for row in result["checks"])
    robust=result["robust_recommended_in_domain"]
    assert robust["validation"]["validation_status"]=="admitted"
    assert robust["decision_trace"]["operational_status"]=="admitted"
    assert robust["selection"]["status"]=="recommended"
    weight=result["validation_admitted_but_sampling_weight_sensitive"]
    assert weight["validation"]["validation_status"]=="admitted"
    assert weight["robustness_profile"]["sampling_weight_status"]=="weight_sensitive"
    breakpoint=result["validation_admitted_at_gamma_1_5_but_breaks_by_gamma_2"]
    assert breakpoint["validation"]["validation_gamma"]==1.5
    assert breakpoint["robustness_profile"]["bounded_reweighting_status"]=="gamma_sensitive"
