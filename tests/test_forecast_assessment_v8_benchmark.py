import pytest

pytest.importorskip("sklearn")

from odsp.forecast_assessment_v8_benchmark import run_forecast_assessment_v8_benchmark


def test_forecast_assessment_v8_frozen_known_truth_benchmark_passes():
    result = run_forecast_assessment_v8_benchmark(seed=20260910)
    assert result["passed"] is True
    assert len(result["checks"]) == 16
    assert all(row["passed"] for row in result["checks"])
    assert result["clean_content"]["v8_certification"]["certification_status"] == "certified"
    assert result["final_evaluation_content_leakage"]["downstream_v7_assessment"] is None
    assert result["final_evaluation_content_leakage"]["v8_certification"]["certification_status"] == "unavailable"
    assert result["content_leakage_without_downstream_layers"]["v8_certification"]["certification_status"] == "unavailable"
