from __future__ import annotations

import itertools
import math

import pytest

from odsp.confirmatory_method_routing import route_confirmatory_method
from odsp.information_lattice import InformationBlock, InformationLatticeNodeScore
from odsp.information_lattice_positive_v2 import certify_positive_information_lattice_v2


def _rows(group_count: int = 3, blocks_per_group: int = 20):
    groups = []
    blocks = []
    for group_index in range(group_count):
        for block_index in range(blocks_per_group):
            groups.append(f"g{group_index}")
            blocks.append(f"g{group_index}-b{block_index:02d}")
    return tuple(groups), tuple(blocks)


def _information_blocks():
    return (
        InformationBlock("A", ("species",)),
        InformationBlock("B", ("season",)),
    )


def _nodes(n: int, *, full: float = 0.6):
    return (
        InformationLatticeNodeScore((), [0.0] * n),
        InformationLatticeNodeScore(("A",), [0.3] * n),
        InformationLatticeNodeScore(("B",), [0.2] * n),
        InformationLatticeNodeScore(("A", "B"), [full] * n),
    )


def test_two_block_independent_positive_lattice_reaches_universal_full_transfer():
    groups, blocks = _rows()
    result = certify_positive_information_lattice_v2(
        _nodes(len(groups)),
        _information_blocks(),
        groups,
        blocks=blocks,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
        seed=77,
    )

    assert result.alternative == "greater"
    assert result.validation_group_independence_assumed is True
    assert result.edge_count == 4
    assert result.robust_full_transfer_path_count == 2
    assert result.certified_path_status == "universal_full_transfer"
    assert result.all_edges_robust_generalizing is True
    assert result.best_path_can_override_failed_edge is False
    assert result.shapley_can_override_edge_failure is False
    assert result.one_sided_bootstrap_t_audit.contrast_count == 4
    assert all(edge.category == "robust_generalizing" for edge in result.edges)


def test_two_block_independent_positive_lattice_preserves_order_sensitive_failure():
    groups, blocks = _rows()
    n = len(groups)
    result = certify_positive_information_lattice_v2(
        (
            InformationLatticeNodeScore((), [0.0] * n),
            InformationLatticeNodeScore(("A",), [0.4] * n),
            InformationLatticeNodeScore(("B",), [0.1] * n),
            InformationLatticeNodeScore(("A", "B"), [0.3] * n),
        ),
        _information_blocks(),
        groups,
        blocks=blocks,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
        seed=77,
    )

    categories = {
        (edge.lower_blocks, edge.added_block): edge.category
        for edge in result.edges
    }
    assert categories[((), "A")] == "robust_generalizing"
    assert categories[((), "B")] == "robust_generalizing"
    assert categories[(("A",), "B")] == "not_robust_generalizing"
    assert categories[(("B",), "A")] == "robust_generalizing"
    assert result.robust_full_transfer_path_count == 1
    assert result.certified_path_status == "order_sensitive_full_transfer"


def test_four_block_independent_positive_lattice_fails_closed_before_inference():
    groups, blocks = _rows()
    n = len(groups)
    names = ("A", "B", "C", "D")
    info = tuple(InformationBlock(name, (name.lower(),)) for name in names)
    nodes = tuple(
        InformationLatticeNodeScore(subset, [0.1 * len(subset)] * n)
        for size in range(len(names) + 1)
        for subset in itertools.combinations(names, size)
    )
    with pytest.raises(ValueError, match="2 or 3 information blocks"):
        certify_positive_information_lattice_v2(
            nodes,
            info,
            groups,
            blocks=blocks,
            bootstrap_draws=500,
            minimum_blocks_per_group=8,
        )


def test_insufficient_blocks_are_unavailable_not_an_exception():
    groups, blocks = _rows(blocks_per_group=1)
    result = certify_positive_information_lattice_v2(
        _nodes(len(groups)),
        _information_blocks(),
        groups,
        blocks=blocks,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
    )
    assert result.one_sided_bootstrap_t_audit.estimable_cell_count == 0
    assert result.robust_full_transfer_path_count == 0
    assert result.certified_path_status == "no_full_transfer"
    assert all(edge.category == "unavailable" for edge in result.edges)


def test_nonfinite_richest_node_stops_incoming_edges_fail_closed():
    groups, blocks = _rows()
    n = len(groups)
    full = [0.6] * n
    full[-1] = -math.inf
    result = certify_positive_information_lattice_v2(
        (
            InformationLatticeNodeScore((), [0.0] * n),
            InformationLatticeNodeScore(("A",), [0.3] * n),
            InformationLatticeNodeScore(("B",), [0.2] * n),
            InformationLatticeNodeScore(("A", "B"), full),
        ),
        _information_blocks(),
        groups,
        blocks=blocks,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
    )
    incoming = [edge for edge in result.edges if len(edge.upper_blocks) == 2]
    assert incoming
    assert all(edge.category == "unavailable" for edge in incoming)
    assert result.robust_full_transfer_path_count == 0


def test_confirmatory_router_promotes_qualified_independent_directional_lattices():
    for block_count, edge_count in ((2, 4), (3, 12)):
        route = route_confirmatory_method(
            alternative="greater",
            validation_design="independent_groups",
            information_structure="complete_lattice",
            upstream_refits="none",
            external_validation="none",
            information_block_count=block_count,
        )
        assert route.role == "primary_confirmatory"
        assert route.primary_for_claim is True
        assert route.edge_count == edge_count
        assert route.canonical_surface == (
            "odsp.information_lattice_positive_v2.certify_positive_information_lattice_v2"
        )

    larger = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="none",
        external_validation="none",
        information_block_count=4,
    )
    assert larger.role == "unqualified"
    assert larger.edge_count == 32

