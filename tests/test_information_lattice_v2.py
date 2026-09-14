from __future__ import annotations

import math

from odsp.information_lattice import InformationBlock, InformationLatticeNodeScore
from odsp.information_lattice_v2 import certify_information_lattice_v2


def _paired_groups(block_count: int = 12):
    groups = ["a"] * block_count + ["b"] * block_count
    blocks = [f"a-{i:02d}" for i in range(block_count)] + [
        f"b-{i:02d}" for i in range(block_count)
    ]
    return groups, blocks


def _blocks():
    return [
        InformationBlock("A", ("species",)),
        InformationBlock("B", ("season",)),
    ]


def test_lattice_v2_preserves_order_sensitive_full_transfer_despite_positive_total_gain():
    groups, resampling_blocks = _paired_groups()
    n = len(groups)
    result = certify_information_lattice_v2(
        [
            InformationLatticeNodeScore((), [0.0] * n),
            InformationLatticeNodeScore(("A",), [0.4] * n),
            InformationLatticeNodeScore(("B",), [0.1] * n),
            InformationLatticeNodeScore(("A", "B"), [0.3] * n),
        ],
        _blocks(),
        groups,
        blocks=resampling_blocks,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
    )

    assert result.point_audit.full_vs_base_gain_category == "generalizing"
    assert result.point_audit.path_status == "order_sensitive_full_transfer"
    assert result.total_admissible_path_count == 2
    assert result.robust_full_transfer_path_count == 1
    assert result.robust_full_transfer_path_fraction == 0.5
    assert result.certified_path_status == "order_sensitive_full_transfer"
    assert result.all_edges_robust_generalizing is False
    assert result.total_gain_can_override_failed_edge is False
    assert result.shapley_can_override_edge_failure is False
    assert result.bootstrap_t_audit.replicate_studentization_recomputed is True

    edge_status = {
        (edge.lower_blocks, edge.added_block): edge.bootstrap_t_summary.category
        for edge in result.edges
    }
    assert edge_status[((), "A")] == "robust_generalizing"
    assert edge_status[((), "B")] == "robust_generalizing"
    assert edge_status[(("A",), "B")] == "robust_non_generalizing"
    assert edge_status[(("B",), "A")] == "robust_generalizing"


def test_lattice_v2_reaches_universal_full_transfer_when_every_edge_is_positive():
    groups, resampling_blocks = _paired_groups()
    n = len(groups)
    result = certify_information_lattice_v2(
        [
            InformationLatticeNodeScore((), [0.0] * n),
            InformationLatticeNodeScore(("A",), [0.3] * n),
            InformationLatticeNodeScore(("B",), [0.2] * n),
            InformationLatticeNodeScore(("A", "B"), [0.6] * n),
        ],
        _blocks(),
        groups,
        blocks=resampling_blocks,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
    )
    assert result.robust_full_transfer_path_count == 2
    assert result.certified_path_status == "universal_full_transfer"
    assert result.all_edges_robust_generalizing is True
    assert all(
        edge.bootstrap_t_summary.category == "robust_generalizing"
        for edge in result.edges
    )


def test_lattice_v2_nonfinite_richest_node_stops_full_paths_fail_closed():
    groups, resampling_blocks = _paired_groups()
    n = len(groups)
    full = [0.6] * n
    full[-1] = -math.inf
    result = certify_information_lattice_v2(
        [
            InformationLatticeNodeScore((), [0.0] * n),
            InformationLatticeNodeScore(("A",), [0.3] * n),
            InformationLatticeNodeScore(("B",), [0.2] * n),
            InformationLatticeNodeScore(("A", "B"), full),
        ],
        _blocks(),
        groups,
        blocks=resampling_blocks,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
    )
    incoming = [
        edge.bootstrap_t_summary
        for edge in result.edges
        if len(edge.upper_blocks) == 2
    ]
    assert incoming
    assert all(summary.category == "unavailable" for summary in incoming)
    assert result.robust_full_transfer_path_count == 0
    assert result.certified_path_status == "no_full_transfer"
