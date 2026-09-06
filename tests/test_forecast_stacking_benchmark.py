from __future__ import annotations

from odsp.forecast_stacking_benchmark import run_forecast_stacking_benchmark


def test_forecast_stacking_known_truth_benchmark_passes():
    result = run_forecast_stacking_benchmark()
    assert result["passed"] is True
    checks = {row["name"]: row["passed"] for row in result["checks"]}
    assert all(checks.values())
    stable = result["families"]["complementary_stable"]["stack"]
    shifted = result["families"]["validation_shift"]["stack"]
    mixed = result["families"]["mixed_group"]["stack"]
    assert stable["transfer_category"] == "generalizing"
    assert shifted["transfer_category"] == "non_generalizing"
    assert mixed["transfer_category"] == "mixed"
