import pytest

pytest.importorskip("sklearn")

from odsp.forecast_assessment_v3_benchmark import run_forecast_assessment_v3_benchmark


def test_frozen_forecast_assessment_v3_benchmark_passes():
    result=run_forecast_assessment_v3_benchmark(seed=20260907)
    assert result["passed"] is True
    assert len(result["checks"])==12
    assert all(row["passed"] for row in result["checks"])
    assert result["strong"]["v3_certification"]["certification_status"]=="certified"
    assert result["scheme_sensitive"]["v3_certification"]["certification_status"]=="not_certified"
    assert result["scheme_unavailable"]["v3_certification"]["certification_status"]=="unavailable"
