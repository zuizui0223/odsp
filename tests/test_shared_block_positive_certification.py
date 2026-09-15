from __future__ import annotations

import numpy as np
import pytest

from odsp.information_lattice import InformationBlock, InformationLatticeNodeScore
from odsp.information_transfer import InformationLevelScore
from odsp.shared_block_positive_certification import certify_shared_block_positive_gains_v2
from odsp.shared_block_positive_information import (
    certify_shared_block_positive_information_lattice_v2,
    certify_shared_block_positive_information_transfer_v2,
)


def _paired_rows(group_count: int = 3, block_count: int = 20):
    groups = []
    blocks = []
    for group_index in range(group_count):
        for block_index in range(block_count):
            groups.append(f"g{group_index}")
            blocks.append(f"b{block_index}")
    return tuple(groups), tuple(blocks)


def test_strong_positive_paired_contrasts_generalize_directionally():
    groups, blocks = _paired_rows()
    values = []
    for row, group in enumerate(groups):
        block_index = row % 20
        group_index = int(group[1:])
        shared = 0.015 * ((block_index % 5) - 2)
        values.append([
            0.45 + shared + 0.002 * group_index,
            0.30 + 0.7 * shared - 0.001 * group_index,
        ])
    audit = certify_shared_block_positive_gains_v2(
        values,
        groups,
        blocks,
        contrast_names=["coarse", "fine"],
        bootstrap_draws=500,
        minimum_shared_blocks=8,
        seed=77,
    )
    assert audit.alternative == "greater"
    assert audit.validation_group_independence_assumed is False
    assert audit.same_block_draw_shared_across_all_groups_and_contrasts is True
    assert audit.exact_shared_block_support_validated is True
    assert all(row.category == "robust_generalizing" for row in audit.contrasts)
    assert all(cell.lower_bound > 0 for row in audit.contrasts for cell in row.groups)


def test_mismatched_positive_block_support_fails_closed():
    groups, blocks = _paired_rows(group_count=2, block_count=10)
    weights = np.ones(len(groups), dtype=float)
    # Remove one positive-mass shared block from the second group only.
    weights[10] = 0.0
    with pytest.raises(ValueError, match="identical positive-mass block support"):
        certify_shared_block_positive_gains_v2(
            [[0.2] for _ in groups],
            groups,
            blocks,
            sample_weight=weights,
            bootstrap_draws=500,
            minimum_shared_blocks=8,
        )


def test_one_shared_block_is_unavailable_not_exception():
    groups, blocks = _paired_rows(group_count=2, block_count=1)
    audit = certify_shared_block_positive_gains_v2(
        [[0.5] for _ in groups],
        groups,
        blocks,
        bootstrap_draws=500,
        minimum_shared_blocks=8,
    )
    assert audit.shared_block_count == 1
    assert audit.estimable_cell_count == 0
    assert audit.contrasts[0].category == "unavailable"
    assert all(cell.status == "unavailable" for cell in audit.contrasts[0].groups)
    assert all(cell.studentizing_standard_error is None for cell in audit.contrasts[0].groups)


def test_paired_information_ceiling_stops_at_null_fine_step():
    groups, blocks = _paired_rows()
    n = len(groups)
    pooled = np.zeros(n)
    coarse = np.full(n, 0.4)
    fine = coarse.copy()
    result = certify_shared_block_positive_information_transfer_v2(
        [
            InformationLevelScore("pooled", (), pooled),
            InformationLevelScore("coarse", ("coarse",), coarse),
            InformationLevelScore("fine", ("coarse", "fine"), fine),
        ],
        groups,
        blocks,
        bootstrap_draws=500,
        minimum_shared_blocks=8,
    )
    assert result.certified_transfer_ceiling == "coarse"
    assert result.alternative == "greater"
    assert result.validation_group_independence_assumed is False


def test_paired_directional_lattice_preserves_all_paths_when_all_edges_positive():
    groups, blocks = _paired_rows()
    n = len(groups)
    base = np.zeros(n)
    a = np.full(n, 0.30)
    b = np.full(n, 0.25)
    ab = np.full(n, 0.55)
    result = certify_shared_block_positive_information_lattice_v2(
        [
            InformationLatticeNodeScore((), base),
            InformationLatticeNodeScore(("A",), a),
            InformationLatticeNodeScore(("B",), b),
            InformationLatticeNodeScore(("A", "B"), ab),
        ],
        [InformationBlock("A", ("a",)), InformationBlock("B", ("b",))],
        groups,
        blocks,
        bootstrap_draws=500,
        minimum_shared_blocks=8,
    )
    assert result.total_admissible_path_count == 2
    assert result.robust_full_transfer_path_count == 2
    assert result.robust_full_transfer_path_fraction == pytest.approx(1.0)
    assert result.best_path_can_override_failed_edge is False
    assert result.shapley_can_override_edge_failure is False


def test_row_order_does_not_change_paired_directional_result():
    groups, blocks = _paired_rows()
    values = np.asarray([[0.35 + 0.01 * ((index % 5) - 2)] for index in range(len(groups))])
    first = certify_shared_block_positive_gains_v2(
        values,
        groups,
        blocks,
        bootstrap_draws=500,
        seed=123,
        minimum_shared_blocks=8,
    )
    order = np.arange(len(groups))[::-1]
    second = certify_shared_block_positive_gains_v2(
        values[order],
        tuple(np.asarray(groups, dtype=object)[order]),
        tuple(np.asarray(blocks, dtype=object)[order]),
        bootstrap_draws=500,
        seed=123,
        minimum_shared_blocks=8,
    )
    assert first.as_dict() == second.as_dict()
