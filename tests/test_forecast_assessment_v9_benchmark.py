import pytest

pytest.importorskip("sklearn")

from odsp.forecast_assessment_v9_benchmark import run_forecast_assessment_v9_benchmark


def test_forecast_assessment_v9_frozen_known_truth_benchmark_passes():
    result = run_forecast_assessment_v9_benchmark(seed=20260910)
    assert result["passed"] is True
    assert len(result["checks"]) == 17
    assert all(row["passed"] for row in result["checks"])
    assert result["clean_binding"]["v9_certification"]["certification_status"] == "certified"
    assert result["ledger_binding_mismatch"]["downstream_v8_assessment"] is None
    assert result["ledger_binding_mismatch"]["v9_certification"]["certification_status"] == "unavailable"
    assert result["binding_mismatch_without_downstream_layers"]["v9_certification"]["certification_status"] == "unavailable"
