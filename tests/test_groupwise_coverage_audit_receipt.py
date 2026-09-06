from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.groupwise_coverage_audit_benchmark import run_groupwise_coverage_audit_benchmark

ROOT = Path(__file__).resolve().parents[1]


def test_groupwise_coverage_receipt_replays_frozen_benchmark():
    receipt = json.loads((ROOT / "GROUPWISE_COVERAGE_AUDIT_VALIDATION_RECEIPT.json").read_text(encoding="utf-8"))
    result = run_groupwise_coverage_audit_benchmark()
    expected = receipt["canonical_results"]
    assert result["passed"] is expected["passed"] is True

    masked = result["masked_failure"]
    frozen_masked = expected["masked_failure"]
    assert masked["pooled_coverage"] == pytest.approx(frozen_masked["pooled_coverage"], abs=1e-15, rel=0.0)
    assert masked["pooled_absolute_error"] == pytest.approx(frozen_masked["pooled_absolute_error"], abs=1e-15, rel=0.0)
    assert masked["pooled_coverage_ok"] is frozen_masked["pooled_coverage_ok"]
    assert masked["coverage_category"] == frozen_masked["coverage_category"]
    assert masked["failed_group_count"] == frozen_masked["failed_group_count"]
    assert masked["groups"][0]["empirical_coverage"] == pytest.approx(frozen_masked["first_group_coverage"], abs=1e-15, rel=0.0)

    novelty = {row["group_id"]: row["empirical_coverage"] for row in result["novelty_strata"]["groups"]}
    for name in ("in_domain", "novel", "strict"):
        assert novelty[name] == pytest.approx(expected["novelty_strata"][name], abs=1e-15, rel=0.0)
    assert novelty["in_domain"] > novelty["novel"] > novelty["strict"]

    for key in ("positive_transfer_bad_coverage", "good_coverage_bad_transfer"):
        actual = result[key]
        frozen = expected[key]
        assert actual["mean_log_density_gain"] == pytest.approx(frozen["mean_log_density_gain"], abs=1e-15, rel=0.0)
        assert actual["transfer_category"] == frozen["transfer_category"]
        assert actual["coverage_category"] == frozen["coverage_category"]
        assert actual["failed_trust_group_count"] == frozen["failed_trust_group_count"]
        assert actual["trusted_admissible"] is frozen["trusted_admissible"]

    assert result["group_permutation_max_abs_error"] == pytest.approx(expected["group_permutation_max_abs_error"], abs=1e-15, rel=0.0)
    assert receipt["claim_boundary"]["groupwise_empirical_audit_proves_conditional_coverage"] is False
    assert receipt["claim_boundary"]["aggregate_confidence_score_emitted"] is False
