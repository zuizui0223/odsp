from __future__ import annotations

import math

import pytest

from odsp.information_lattice import InformationBlock, InformationLatticeNodeScore
from odsp.information_transfer import InformationLevelScore
from odsp.shared_block_certification import certify_shared_block_gains
from odsp.shared_block_information import (
    certify_shared_block_information_lattice,
    certify_shared_block_information_transfer,
)


def _paired_rows(block_count: int = 10):
    groups = []
    blocks = []
    for group in ("g1", "g2"):
        for block in range(block_count):
            groups.append(group)
            blocks.append(f"b{block:02d}")
    return groups, blocks


def test_shared_block_gain_certification_uses_one_joint_draw_family():
    groups, blocks = _paired_rows()
    n = len(groups)
    gains = [[0.4, 0.2] for _ in range(n)]
    result = certify_shared_block_gains(
        gains,
        groups,
        blocks,
        contrast_names=["species", "context"],
        bootstrap_draws=500,
        minimum_shared_blocks=8,
        seed=20260914,
    )

    assert result.group_count == 2
    assert result.contrast_count == 2
    assert result.shared_block_count == 10
    assert result.exact_shared_block_support_validated is True
    assert result.same_block_draw_shared_across_all_groups_and_contrasts is True
    assert result.validation_group_independence_assumed is False
    assert result.shared_block_exchangeability_assumed is True
    assert result.all_cells_estimable is True
    assert all(row.category == "robust_generalizing" for row in result.contrasts)


def test_shared_block_support_must_match_exactly_across_groups():
    groups = ["g1"] * 10 + ["g2"] * 9
    blocks = [f"b{i:02d}" for i in range(10)] + [f"b{i:02d}" for i in range(9)]
    gains = [[0.2] for _ in groups]
    with pytest.raises(ValueError, match="identical positive-mass block support"):
        certify_shared_block_gains(
            gains,
            groups,
            blocks,
            bootstrap_draws=500,
            minimum_shared_blocks=8,
        )


def test_zero_weight_shared_block_counts_as_missing_support():
    groups, blocks = _paired_rows()
    gains = [[0.2] for _ in groups]
    weight = [1.0] * len(groups)
    weight[-1] = 0.0
    with pytest.raises(ValueError, match="identical positive-mass block support"):
        certify_shared_block_gains(
            gains,
            groups,
            blocks,
            sample_weight=weight,
            bootstrap_draws=500,
            minimum_shared_blocks=8,
        )


def test_insufficient_shared_blocks_fail_all_cells_closed():
    groups, blocks = _paired_rows(block_count=4)
    result = certify_shared_block_gains(
        [[0.3] for _ in groups],
        groups,
        blocks,
        bootstrap_draws=500,
        minimum_shared_blocks=8,
    )
    assert result.all_cells_estimable is False
    assert result.estimable_cell_count == 0
    assert result.contrasts[0].category == "unavailable"
    assert all(cell.status == "unavailable" for cell in result.contrasts[0].groups)


def test_nonfinite_one_group_contrast_is_unavailable_not_pooled_away():
    groups, blocks = _paired_rows()
    gains = [[0.3, 0.2] for _ in groups]
    gains[-1][1] = -math.inf
    result = certify_shared_block_gains(
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


def test_row_order_does_not_change_shared_block_conclusion():
    groups, blocks = _paired_rows()
    gains = [[0.2 + (index % 10) * 0.01] for index in range(len(groups))]
    first = certify_shared_block_gains(
        gains,
        groups,
        blocks,
        bootstrap_draws=1000,
        minimum_shared_blocks=8,
        seed=99,
    )
    order = list(reversed(range(len(groups))))
    second = certify_shared_block_gains(
        [gains[index] for index in order],
        [groups[index] for index in order],
        [blocks[index] for index in order],
        bootstrap_draws=1000,
        minimum_shared_blocks=8,
        seed=99,
    )
    assert second.max_t_critical_value == pytest.approx(first.max_t_critical_value)
    assert [row.category for row in second.contrasts] == [
        row.category for row in first.contrasts
    ]


def test_shared_block_information_filtration_reaches_full_ceiling():
    groups, blocks = _paired_rows()
    n = len(groups)
    result = certify_shared_block_information_transfer(
        [
            InformationLevelScore("pooled", (), [0.0] * n),
            InformationLevelScore("species", ("species",), [0.3] * n),
            InformationLevelScore(
                "species_context",
                ("species", "context"),
                [0.5] * n,
            ),
        ],
        groups,
        blocks,
        bootstrap_draws=500,
        minimum_shared_blocks=8,
    )
    assert result.point_transfer_ceiling == "species_context"
    assert result.certified_transfer_ceiling == "species_context"
    assert result.validation_group_independence_assumed is False
    assert all(
        row.category == "robust_generalizing"
        for row in result.shared_block_certification.contrasts
    )


def test_shared_block_lattice_preserves_order_sensitive_full_transfer():
    groups, blocks = _paired_rows()
    n = len(groups)
    nodes = [
        InformationLatticeNodeScore((), [0.0] * n),
        InformationLatticeNodeScore(("A",), [0.4] * n),
        InformationLatticeNodeScore(("B",), [0.1] * n),
        InformationLatticeNodeScore(("A", "B"), [0.3] * n),
    ]
    result = certify_shared_block_information_lattice(
        nodes,
        [
            InformationBlock("A", ("species",)),
            InformationBlock("B", ("season",)),
        ],
        groups,
        blocks,
        bootstrap_draws=500,
        minimum_shared_blocks=8,
    )
    assert result.total_admissible_path_count == 2
    assert result.robust_full_transfer_path_count == 1
    assert result.certified_path_status == "order_sensitive_full_transfer"
    assert result.validation_group_independence_assumed is False
    edge = {(row.lower_blocks, row.added_block): row.category for row in result.edges}
    assert edge[((), "A")] == "robust_generalizing"
    assert edge[((), "B")] == "robust_generalizing"
    assert edge[(("B",), "A")] == "robust_generalizing"
    assert edge[(("A",), "B")] == "robust_non_generalizing"
