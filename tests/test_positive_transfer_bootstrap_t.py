from __future__ import annotations

import numpy as np
import pytest

from odsp.bootstrap_t import studentized_max_t_critical_value
from odsp.information_transfer import InformationLevelScore
from odsp.information_transfer_positive_v2 import certify_positive_information_transfer_v2
from odsp.positive_transfer_bootstrap_t import (
    certify_independent_group_positive_transfer_v2,
    one_sided_lower_bounds,
    one_sided_lower_max_t_critical_value,
)


def _rows(group_count: int = 3, blocks_per_group: int = 20):
    groups = []
    blocks = []
    for group_index in range(group_count):
        for block_index in range(blocks_per_group):
            groups.append(f"g{group_index}")
            blocks.append(f"g{group_index}-b{block_index}")
    return tuple(groups), tuple(blocks)


def test_one_sided_critical_is_no_larger_than_two_sided_for_same_bootstrap_draws():
    means = np.asarray(
        [
            [0.2, -0.1],
            [-0.15, 0.25],
            [0.05, 0.1],
            [-0.05, -0.2],
            [0.3, 0.0],
        ]
    )
    ses = np.full_like(means, 0.1)
    point = np.zeros(2)
    one_sided = one_sided_lower_max_t_critical_value(
        means, ses, point, confidence_level=0.8
    )
    two_sided = studentized_max_t_critical_value(
        means, ses, point, confidence_level=0.8
    )
    assert one_sided <= two_sided
    assert one_sided >= 0.0


def test_one_sided_lower_bounds_never_exceed_point_when_critical_is_nonnegative():
    point = np.asarray([0.2, 0.5])
    se = np.asarray([0.1, 0.0])
    lower = one_sided_lower_bounds(point, se, 2.0)
    assert lower[0] == pytest.approx(0.0)
    assert lower[1] == pytest.approx(0.5)
    assert np.all(lower <= point)


def test_strong_positive_group_contrasts_generalize_directionally():
    groups, blocks = _rows()
    values = []
    for index in range(len(groups)):
        block_index = index % 20
        values.append([0.45 + 0.02 * ((block_index % 5) - 2), 0.30 + 0.015 * ((block_index % 4) - 1.5)])
    audit = certify_independent_group_positive_transfer_v2(
        values,
        groups,
        blocks=blocks,
        contrast_names=["coarse", "fine"],
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
        seed=77,
    )
    assert audit.alternative == "greater"
    assert audit.replicate_studentization_recomputed is True
    assert all(row.category == "robust_generalizing" for row in audit.contrasts)
    assert all(cell.lower_bound > 0 for row in audit.contrasts for cell in row.groups)


def test_exact_zero_gain_is_not_called_positive():
    groups, blocks = _rows()
    audit = certify_independent_group_positive_transfer_v2(
        [[0.0] for _ in groups],
        groups,
        blocks=blocks,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
    )
    assert audit.contrasts[0].category == "not_robust_generalizing"
    assert all(cell.lower_bound == pytest.approx(0.0) for cell in audit.contrasts[0].groups)


def test_positive_information_ceiling_stops_at_null_fine_step():
    groups, blocks = _rows()
    n = len(groups)
    pooled = np.zeros(n)
    coarse = np.full(n, 0.4)
    fine = coarse.copy()
    result = certify_positive_information_transfer_v2(
        [
            InformationLevelScore("pooled", (), pooled),
            InformationLevelScore("coarse", ("coarse",), coarse),
            InformationLevelScore("fine", ("coarse", "fine"), fine),
        ],
        groups,
        blocks=blocks,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
    )
    assert result.certified_transfer_ceiling == "coarse"
    assert result.alternative == "greater"


def test_insufficient_blocks_fail_directional_claim_closed():
    groups, blocks = _rows(blocks_per_group=4)
    audit = certify_independent_group_positive_transfer_v2(
        [[0.5] for _ in groups],
        groups,
        blocks=blocks,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
    )
    assert audit.contrasts[0].category == "unavailable"
    assert audit.estimable_cell_count == 0
