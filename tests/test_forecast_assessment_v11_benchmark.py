import pytest

pytest.importorskip("sklearn")

from odsp.forecast_assessment_v11_benchmark import run_forecast_assessment_v11_benchmark


def test_frozen_forecast_assessment_v11_benchmark():
    result = run_forecast_assessment_v11_benchmark()
    assert result["passed"] is True
    assert len(result["checks"]) == 19
    assert all(row["passed"] for row in result["checks"])
    assert result["clean_checkpoints"]["v11_certification"]["certification_status"] == "certified"
    assert result["checkpoint_mismatch"]["downstream_v10_assessment"] is None
    assert result["checkpoint_mismatch"]["v11_certification"]["certification_status"] == "unavailable"
    assert result["clean_checkpoints_log_chain_mismatch"]["v11_certification"]["certification_status"] == "unavailable"
