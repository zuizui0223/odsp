from __future__ import annotations

import math

import pytest

from odsp.information_lattice import InformationBlock
from odsp.refit_information_lattice import (
    RefitInformationLatticeNodeScores,
    certify_refit_information_lattice,
)


def _rows(n_per_group: int = 8):
    groups = ["g1"] * n_per_group + ["g2"] * n_per_group
    blocks = [f"g1-b{i}" for i in range(n_per_group)] + [
        f"g2-b{i}" for i in range(n_per_group)
    ]
    return groups, blocks


def _matrix(values: list[float], n_rows: int) -> list[list[float]]:
    return [[value] * n_rows for value in values]


def _known_refit_lattice():
    groups, blocks = _rows()
    n = len(groups)
    refit_ids = [f"r{i:02d}" for i in range(8)]
    # Reference r00 has universal transfer. The remaining refits make the
    # A->AB edge negative while preserving the B->AB path.
    ab = [0.9] + [0.4] * 7
    nodes = [
        RefitInformationLatticeNodeScores((), _matrix([0.0] * 8, n)),
        RefitInformationLatticeNodeScores(("A",), _matrix([0.6] * 8, n)),
        RefitInformationLatticeNodeScores(("B",), _matrix([0.01] * 8, n)),
        RefitInformationLatticeNodeScores(("A", "B"), _matrix(ab, n)),
    ]
    info = [
        InformationBlock("A", ("species",)),
        InformationBlock("B", ("season",)),
    ]
    return nodes, info, groups, blocks, refit_ids


def test_reference_universal_but_refit_aware_lattice_is_order_sensitive():
    nodes, info, groups, blocks, refit_ids = _known_refit_lattice()
    result = certify_refit_information_lattice(
        nodes,
        info,
        groups,
        blocks=blocks,
        refit_ids=refit_ids,
        reference_refit_id="r00",
        nested_draws=2000,
        minimum_refits=8,
        minimum_blocks_per_group=8,
        seed=20260914,
    )

    assert result.total_admissible_path_count == 2
    assert result.reference_point_full_transfer_path_count == 2
    assert result.reference_point_path_status == "universal_full_transfer"
    assert result.reference_certified_full_transfer_path_count == 2
    assert result.reference_certified_path_status == "universal_full_transfer"

    assert result.refit_point_full_transfer_path_counts[0] == 2
    assert all(value == 1 for value in result.refit_point_full_transfer_path_counts[1:])
    assert result.refit_path_stability == "refit_sensitive"

    assert result.ensemble_point_full_transfer_path_count == 1
    assert result.ensemble_point_path_status == "order_sensitive_full_transfer"
    assert result.refit_aware_full_transfer_path_count == 1
    assert result.refit_aware_path_status == "order_sensitive_full_transfer"
    assert result.reference_fit_can_override_refit_aware_failure is False
    assert result.best_path_can_override_failed_edge is False
    assert result.shapley_can_override_edge_failure is False
    assert result.same_selected_refit_shared_across_all_group_edge_cells is True
    assert result.same_block_draw_shared_across_edges_within_group is True
    assert sum(result.selected_refit_draw_counts) == 2000

    edge = {
        (row.lower_blocks, row.added_block): row for row in result.edges
    }
    assert edge[((), "A")].refit_aware_category == "robust_generalizing"
    assert edge[((), "B")].refit_aware_category == "robust_generalizing"
    assert edge[(("B",), "A")].refit_aware_category == "robust_generalizing"
    assert edge[(("A",), "B")].refit_aware_category != "robust_generalizing"
    assert edge[(("A",), "B")].refit_category_stability == "refit_sensitive"


def test_refit_and_row_order_do_not_change_scientific_lattice_result():
    nodes, info, groups, blocks, refit_ids = _known_refit_lattice()
    first = certify_refit_information_lattice(
        nodes,
        info,
        groups,
        blocks=blocks,
        refit_ids=refit_ids,
        reference_refit_id="r00",
        nested_draws=1000,
        minimum_refits=8,
        minimum_blocks_per_group=8,
        seed=77,
    )

    refit_order = [7, 0, 5, 1, 4, 2, 6, 3]
    row_order = list(reversed(range(len(groups))))
    reordered_nodes = []
    for node in nodes:
        matrix = node.score
        reordered_nodes.append(
            RefitInformationLatticeNodeScores(
                node.blocks,
                [
                    [matrix[r][c] for c in row_order]
                    for r in refit_order
                ],
            )
        )
    second = certify_refit_information_lattice(
        reordered_nodes,
        info,
        [groups[index] for index in row_order],
        blocks=[blocks[index] for index in row_order],
        refit_ids=[refit_ids[index] for index in refit_order],
        reference_refit_id="r00",
        nested_draws=1000,
        minimum_refits=8,
        minimum_blocks_per_group=8,
        seed=77,
    )

    assert second.refit_ids == first.refit_ids
    assert second.refit_point_full_transfer_path_counts == first.refit_point_full_transfer_path_counts
    assert second.refit_aware_full_transfer_path_count == first.refit_aware_full_transfer_path_count
    assert second.refit_aware_path_status == first.refit_aware_path_status
    assert second.selected_refit_draw_counts == first.selected_refit_draw_counts
    first_edges = {
        (row.lower_blocks, row.added_block): row.refit_aware_category
        for row in first.edges
    }
    second_edges = {
        (row.lower_blocks, row.added_block): row.refit_aware_category
        for row in second.edges
    }
    assert second_edges == first_edges


def test_insufficient_refits_make_every_lattice_edge_unavailable():
    nodes, info, groups, blocks, refit_ids = _known_refit_lattice()
    result = certify_refit_information_lattice(
        nodes,
        info,
        groups,
        blocks=blocks,
        refit_ids=refit_ids,
        nested_draws=500,
        minimum_refits=9,
        minimum_blocks_per_group=8,
    )
    assert result.all_cells_estimable is False
    assert result.estimable_cell_count == 0
    assert result.refit_aware_full_transfer_path_count == 0
    assert result.refit_aware_path_status == "no_full_transfer"
    assert all(row.refit_aware_category == "unavailable" for row in result.edges)


def test_nonfinite_richest_refit_stops_all_full_paths_but_reference_remains_traceable():
    nodes, info, groups, blocks, refit_ids = _known_refit_lattice()
    full = nodes[-1].score
    damaged = [list(row) for row in full]
    damaged[-1] = [-math.inf] * len(groups)
    damaged_nodes = [*nodes[:-1], RefitInformationLatticeNodeScores(("A", "B"), damaged)]

    result = certify_refit_information_lattice(
        damaged_nodes,
        info,
        groups,
        blocks=blocks,
        refit_ids=refit_ids,
        reference_refit_id="r00",
        nested_draws=500,
        minimum_refits=8,
        minimum_blocks_per_group=8,
    )
    assert result.reference_point_path_status == "universal_full_transfer"
    assert result.refit_aware_full_transfer_path_count == 0
    assert result.refit_aware_path_status == "no_full_transfer"
    incoming = [row for row in result.edges if len(row.upper_blocks) == 2]
    assert incoming
    assert all(row.refit_aware_category == "unavailable" for row in incoming)


def test_nonfinite_comparator_refit_fails_closed():
    nodes, info, groups, blocks, refit_ids = _known_refit_lattice()
    a = [list(row) for row in nodes[1].score]
    a[-1][0] = -math.inf
    broken = [
        nodes[0],
        RefitInformationLatticeNodeScores(("A",), a),
        nodes[2],
        nodes[3],
    ]
    with pytest.raises(ValueError, match="comparator lattice node"):
        certify_refit_information_lattice(
            broken,
            info,
            groups,
            blocks=blocks,
            refit_ids=refit_ids,
            nested_draws=500,
            minimum_refits=8,
            minimum_blocks_per_group=8,
        )


def test_complete_subset_table_is_required_for_refit_lattice():
    nodes, info, groups, blocks, refit_ids = _known_refit_lattice()
    with pytest.raises(ValueError, match="complete subset score table"):
        certify_refit_information_lattice(
            nodes[:-1],
            info,
            groups,
            blocks=blocks,
            refit_ids=refit_ids,
            nested_draws=500,
            minimum_refits=8,
            minimum_blocks_per_group=8,
        )
