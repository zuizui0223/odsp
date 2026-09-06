from __future__ import annotations

from odsp.trust_aware_model_selection_benchmark import run_trust_aware_model_selection_benchmark


def test_trust_aware_model_selection_known_truth_passes():
    result = run_trust_aware_model_selection_benchmark()
    assert result["passed"] is True
    assert all(row["passed"] for row in result["checks"])
    assert result["selection"]["recommended_by_log_score"] == "balanced_trusted"
    assert result["selection"]["pareto_front_names"] == ["balanced_trusted"]
    by_name = {row["name"]: row for row in result["selection"]["candidates"]}
    assert by_name["pooled_masked_coverage_failure"]["forecast_score"]["coverage_ok"] is True
    assert by_name["pooled_masked_coverage_failure"]["groupwise_trust"]["coverage_category"] == "mixed"
    assert by_name["pooled_masked_coverage_failure"]["trusted_admissible"] is False
