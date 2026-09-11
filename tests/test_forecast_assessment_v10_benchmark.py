import pytest

pytest.importorskip("sklearn")

from odsp.forecast_assessment_v10_benchmark import run_forecast_assessment_v10_benchmark


def test_forecast_assessment_v10_frozen_known_truth_benchmark_passes():
    result = run_forecast_assessment_v10_benchmark(seed=20260911)
    assert result["passed"] is True
    assert len(result["checks"]) == 18
    assert all(row["passed"] for row in result["checks"])
    assert result["clean_log_chain"]["v10_certification"]["certification_status"] == "certified"
    assert result["log_chain_mismatch"]["downstream_v9_assessment"] is None
    assert result["log_chain_mismatch"]["v10_certification"]["certification_status"] == "unavailable"
    assert result["clean_log_chain_binding_mismatch"]["v10_certification"]["certification_status"] == "unavailable"
