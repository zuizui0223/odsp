from __future__ import annotations

import numpy as np
import pytest

from odsp.shared_block_certification import certify_shared_block_gains
from odsp.shared_block_certification_v2 import certify_shared_block_gains_v2


def _paired_rows(group_count: int = 3, block_count: int = 12):
    groups: list[str] = []
    blocks: list[str] = []
    for group_index in range(group_count):
        for block_index in range(block_count):
            groups.append(f"g{group_index}")
            blocks.append(f"b{block_index:02d}")
    return groups, blocks


def test_shared_block_v2_constant_positive_family_is_exact():
    groups, blocks = _paired_rows()
    gains = [[0.3, 0.2] for _ in groups]

    result = certify_shared_block_gains_v2(
        gains,
        groups,
        blocks,
        contrast_names=["coarse", "fine"],
        bootstrap_draws=500,
        minimum_shared_blocks=8,
        seed=7,
    )

    assert result.schema_version == 2
    assert result.replicate_studentization_recomputed is True
    assert result.same_block_draw_shared_across_all_groups_and_contrasts is True
    assert result.validation_group_independence_assumed is False
    assert result.bootstrap_t_critical_value == pytest.approx(0.0)
    assert result.all_cells_estimable is True
    assert all(row.category == "robust_generalizing" for row in result.contrasts)
    for contrast in result.contrasts:
        for cell in contrast.groups:
            assert cell.studentizing_standard_error == pytest.approx(0.0)
            assert cell.lower_bound == pytest.approx(cell.mean_gain)
            assert cell.upper_bound == pytest.approx(cell.mean_gain)


def test_shared_block_v2_recomputes_studentizer_and_is_row_order_invariant():
    groups, blocks = _paired_rows()
    gains = []
    for group_index in range(3):
        for block_index in range(12):
            gains.append(
                [
                    0.25 + 0.03 * ((block_index % 4) - 1.5),
                    0.18 + 0.02 * ((block_index % 3) - 1.0) + 0.01 * group_index,
                ]
            )

    first = certify_shared_block_gains_v2(
        gains,
        groups,
        blocks,
        contrast_names=["a", "b"],
        bootstrap_draws=1000,
        minimum_shared_blocks=8,
        seed=91,
    )
    order = np.arange(len(groups))[::-1]
    second = certify_shared_block_gains_v2(
        np.asarray(gains)[order],
        [groups[index] for index in order],
        [blocks[index] for index in order],
        contrast_names=["a", "b"],
        bootstrap_draws=1000,
        minimum_shared_blocks=8,
        seed=91,
    )

    assert first.bootstrap_t_critical_value is not None
    assert first.bootstrap_t_critical_value > 0
    assert second.bootstrap_t_critical_value == pytest.approx(
        first.bootstrap_t_critical_value, abs=1e-12
    )
    first_cells = {
        (contrast.contrast, cell.group): cell
        for contrast in first.contrasts
        for cell in contrast.groups
    }
    second_cells = {
        (contrast.contrast, cell.group): cell
        for contrast in second.contrasts
        for cell in contrast.groups
    }
    for key, left in first_cells.items():
        right = second_cells[key]
        assert right.mean_gain == pytest.approx(left.mean_gain, abs=1e-12)
        assert right.studentizing_standard_error == pytest.approx(
            left.studentizing_standard_error, abs=1e-12
        )
        assert right.lower_bound == pytest.approx(left.lower_bound, abs=1e-12)
        assert right.upper_bound == pytest.approx(left.upper_bound, abs=1e-12)
    assert any(
        abs(float(cell.bootstrap_standard_error) - float(cell.studentizing_standard_error))
        > 1e-8
        for cell in first_cells.values()
    )


def test_shared_block_v2_rejects_unbalanced_positive_mass_support():
    groups, blocks = _paired_rows(group_count=2, block_count=10)
    weights = np.ones(len(groups), dtype=float)
    # Remove support for b09 only in g1.
    weights[-1] = 0.0
    with pytest.raises(ValueError, match="identical positive-mass block support"):
        certify_shared_block_gains_v2(
            [[0.2] for _ in groups],
            groups,
            blocks,
            sample_weight=weights,
            bootstrap_draws=500,
            minimum_shared_blocks=8,
        )


def test_shared_block_v2_fails_nonfinite_cell_without_rescuing_other_groups():
    groups, blocks = _paired_rows(group_count=2, block_count=10)
    gains = [[0.3, 0.2] for _ in groups]
    gains[-1][1] = -np.inf
    result = certify_shared_block_gains_v2(
        gains,
        groups,
        blocks,
        contrast_names=["coarse", "fine"],
        bootstrap_draws=500,
        minimum_shared_blocks=8,
    )
    assert result.contrasts[0].category == "robust_generalizing"
    assert result.contrasts[1].category == "unavailable"
    assert result.contrasts[1].unavailable_group_count == 1


def test_shared_block_v1_remains_available_for_frozen_provenance():
    groups, blocks = _paired_rows(group_count=2, block_count=10)
    gains = [[0.2 + 0.01 * (index % 4)] for index in range(len(groups))]
    legacy = certify_shared_block_gains(
        gains,
        groups,
        blocks,
        bootstrap_draws=500,
        minimum_shared_blocks=8,
        seed=11,
    )
    prospective = certify_shared_block_gains_v2(
        gains,
        groups,
        blocks,
        bootstrap_draws=500,
        minimum_shared_blocks=8,
        seed=11,
    )
    assert legacy.max_t_critical_value is not None
    assert prospective.bootstrap_t_critical_value is not None
    assert prospective.schema_version == 2
