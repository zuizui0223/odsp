import pytest

pytest.importorskip("sklearn")

from odsp.forecast_assessment_v7_benchmark import run_forecast_assessment_v7_benchmark


def test_forecast_assessment_v7_frozen_known_truth_benchmark_passes():
    result = run_forecast_assessment_v7_benchmark(seed=20260910)
    assert result["passed"] is True
    assert len(result["checks"]) == 15
    assert all(row["passed"] for row in result["checks"])
    assert result["clean_access"]["v7_certification"]["certification_status"] == "certified"
    assert result["final_evaluation_access_leakage"]["downstream_v6_assessment"] is None
    assert result["final_evaluation_access_leakage"]["v7_certification"]["certification_status"] == "unavailable"
    assert result["access_leakage_without_selection_or_scheme"]["v7_certification"]["certification_status"] == "unavailable"
