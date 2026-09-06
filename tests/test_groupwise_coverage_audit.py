from __future__ import annotations

import numpy as np

from odsp.groupwise_coverage_audit import (
    audit_groupwise_coverage,
    audit_groupwise_forecast_trust,
)


def test_pooled_coverage_cannot_rescue_failed_group():
    covered = np.concatenate([
        np.r_[np.ones(600, dtype=bool), np.zeros(400, dtype=bool)],
        *[
            np.r_[np.ones(916, dtype=bool), np.zeros(84, dtype=bool)]
            for _ in range(19)
        ],
    ])
    groups = tuple(
        label
        for index in range(20)
        for label in [f"g{index + 1}"] * 1000
    )
    audit = audit_groupwise_coverage(covered, groups)
    assert abs(audit.pooled_coverage - 0.9002) < 1e-12
    assert audit.pooled_coverage_ok is True
    assert audit.coverage_category == "mixed"
    assert audit.failed_group_count == 1
    assert audit.all_groups_ok is False
    assert audit.conditional_coverage_guarantee_claimed is False


def test_trust_requires_both_group_gain_and_group_coverage():
    covered = np.concatenate([
        np.r_[np.ones(600, dtype=bool), np.zeros(400, dtype=bool)],
        np.r_[np.ones(900, dtype=bool), np.zeros(100, dtype=bool)],
    ])
    groups = tuple(["a"] * 1000 + ["b"] * 1000)
    marginal = np.full(2000, -2.0)
    conditional = marginal + 0.2
    result = audit_groupwise_forecast_trust(
        conditional,
        marginal,
        covered,
        groups,
    )
    assert result.transfer_category == "generalizing"
    assert result.coverage_category == "mixed"
    assert result.trusted_admissible is False
    assert result.failed_trust_group_count == 1
    assert result.aggregate_confidence_score_emitted is False
