from __future__ import annotations

from odsp.forecast_trust_dossier_benchmark import run_forecast_trust_dossier_benchmark


def test_dossier_separates_validation_blockers_from_deployment_warnings():
    result = run_forecast_trust_dossier_benchmark(seed=20260906, bootstrap_draws=1000)
    assert result["passed"] is True
    dossiers = result["dossiers"]

    robust = dossiers["robust_in_domain"]
    assert robust["validation"]["robust_validation_status"] == "admitted"
    assert robust["validation"]["blocking_reasons"] == []
    assert robust["deployment"]["status"] == "in_domain"
    assert robust["selection"]["status"] == "recommended"

    fragile = dossiers["fragile_in_domain"]
    assert fragile["validation"]["robust_validation_status"] == "blocked"
    assert "transfer_uncertain" in fragile["validation"]["blocking_reasons"]
    assert fragile["deployment"]["status"] == "in_domain"

    strict = dossiers["robust_strict_extrapolation"]
    assert strict["validation"]["robust_validation_status"] == "admitted"
    assert strict["validation"]["blocking_reasons"] == []
    assert strict["deployment"]["status"] == "strict_extrapolation_warning"
    assert "strict_extrapolation" in strict["deployment"]["warnings"]
    assert strict["aggregate_confidence_score_emitted"] is False


def test_too_few_blocks_is_unavailable_not_failed():
    result = run_forecast_trust_dossier_benchmark(seed=20260906, bootstrap_draws=1000)
    dossier = result["dossiers"]["too_few_blocks"]
    assert dossier["validation"]["robust_validation_status"] == "unavailable"
    assert dossier["validation"]["transfer_uncertainty_gate"] == "unavailable"
    assert "transfer_unavailable" in dossier["validation"]["blocking_reasons"]
