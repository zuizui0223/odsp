from __future__ import annotations

from odsp.groupwise_coverage_audit_benchmark import run_groupwise_coverage_audit_benchmark


def test_groupwise_coverage_known_truth_benchmark_passes():
    result = run_groupwise_coverage_audit_benchmark()
    assert result["passed"] is True
    assert all(row["passed"] for row in result["checks"])
    assert result["masked_failure"]["pooled_coverage_ok"] is True
    assert result["masked_failure"]["coverage_category"] == "mixed"
    assert result["positive_transfer_bad_coverage"]["trusted_admissible"] is False
    assert result["good_coverage_bad_transfer"]["trusted_admissible"] is False
