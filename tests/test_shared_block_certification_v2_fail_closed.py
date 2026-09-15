from __future__ import annotations

import pytest

from odsp.shared_block_certification_v2 import certify_shared_block_gains_v2


def test_one_shared_block_is_unavailable_not_an_exception():
    groups = ("g0", "g0", "g1", "g1", "g2", "g2")
    blocks = ("b0",) * len(groups)
    gains = (
        (0.2, 0.4),
        (0.4, 0.6),
        (0.3, 0.5),
        (0.5, 0.7),
        (0.1, 0.3),
        (0.3, 0.5),
    )

    result = certify_shared_block_gains_v2(
        gains,
        groups,
        blocks,
        contrast_names=("coarse", "fine"),
        bootstrap_draws=500,
        minimum_shared_blocks=8,
    )

    assert result.shared_block_count == 1
    assert result.bootstrap_t_critical_value is None
    assert result.estimable_cell_count == 0
    assert result.all_cells_estimable is False
    assert all(row.category == "unavailable" for row in result.contrasts)
    assert all(
        cell.status == "unavailable"
        and cell.estimable is False
        and cell.bootstrap_standard_error is None
        and cell.studentizing_standard_error is None
        and cell.lower_bound is None
        and cell.upper_bound is None
        for row in result.contrasts
        for cell in row.groups
    )

    coarse = result.contrasts[0]
    assert [cell.mean_gain for cell in coarse.groups] == pytest.approx([0.3, 0.4, 0.2])


def test_one_block_support_mismatch_still_hard_stops():
    gains = ((0.2,), (0.3,))
    groups = ("g0", "g1")
    blocks = ("b0", "b1")

    with pytest.raises(ValueError, match="identical positive-mass block support"):
        certify_shared_block_gains_v2(
            gains,
            groups,
            blocks,
            bootstrap_draws=500,
            minimum_shared_blocks=8,
        )


def test_two_shared_blocks_keep_existing_insufficient_support_path():
    groups = ("g0", "g0", "g1", "g1")
    blocks = ("b0", "b1", "b0", "b1")
    gains = ((0.2,), (0.4,), (0.3,), (0.5,))

    result = certify_shared_block_gains_v2(
        gains,
        groups,
        blocks,
        bootstrap_draws=500,
        minimum_shared_blocks=8,
    )

    assert result.shared_block_count == 2
    assert result.estimable_cell_count == 0
    assert result.contrasts[0].category == "unavailable"
