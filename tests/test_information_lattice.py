from __future__ import annotations

import math

import pytest

from odsp.information_lattice import (
    InformationBlock,
    InformationLatticeNodeScore,
    audit_information_lattice,
    certify_information_lattice,
)


def _fixture():
    # Every vector is evaluated on the same two independent groups and blocks.
    # total(base -> AB)=+0.3 in both groups, but the marginal contribution of B
    # changes sign with predecessor information:
    #   base -> A  +0.4 ; A -> AB  -0.1
    #   base -> B  +0.1 ; B -> AB  +0.2
    groups = ["g1"] * 4 + ["g2"] * 4
    blocks = [f"g1-b{i}" for i in range(4)] + [f"g2-b{i}" for i in range(4)]
    n = len(groups)
    nodes = (
        InformationLatticeNodeScore((), [0.0] * n),
        InformationLatticeNodeScore(("A",), [0.4] * n),
        InformationLatticeNodeScore(("B",), [0.1] * n),
        InformationLatticeNodeScore(("A", "B"), [0.3] * n),
    )
    information = (
        InformationBlock("A", ("species",)),
        InformationBlock("B", ("context",)),
    )
    return nodes, information, groups, blocks


def _edge_lookup(result):
    return {
        (tuple(edge.lower_blocks), edge.added_block): edge
        for edge in result.edges
    }


def test_positive_total_gain_can_hide_order_sensitive_full_transfer():
    nodes, information, groups, _ = _fixture()
    result = audit_information_lattice(nodes, information, groups)

    assert result.node_count == 4
    assert result.edge_count == 4
    assert result.full_vs_base_gain_category == "generalizing"
    assert [row.mean_gain for row in result.full_vs_base_group_gains] == pytest.approx([0.3, 0.3])
    assert result.total_admissible_path_count == 2
    assert result.full_transfer_path_count == 1
    assert result.full_transfer_path_fraction == pytest.approx(0.5)
    assert result.path_status == "order_sensitive_full_transfer"
    assert result.all_edges_generalizing is False

    edge = _edge_lookup(result)
    assert edge[((), "A")].gain_category == "generalizing"
    assert edge[(("A",), "B")].gain_category == "non_generalizing"
    assert edge[((), "B")].gain_category == "generalizing"
    assert edge[(("B",), "A")].gain_category == "generalizing"


def test_shapley_summary_is_additive_but_cannot_rescue_failed_edge():
    nodes, information, groups, _ = _fixture()
    result = audit_information_lattice(nodes, information, groups)
    blocks = {row.block: row for row in result.block_summaries}

    assert blocks["A"].order_robust_category == "order_robust_generalizing"
    assert blocks["B"].order_robust_category == "order_sensitive"
    assert [row.mean_gain for row in blocks["A"].shapley_group_gains] == pytest.approx([0.3, 0.3])
    assert [row.mean_gain for row in blocks["B"].shapley_group_gains] == pytest.approx([0.0, 0.0], abs=1e-15)
    assert blocks["A"].shapley_gain_category == "generalizing"
    assert blocks["B"].shapley_gain_category == "non_generalizing"
    assert result.shapley_additivity_error_max_abs == pytest.approx(0.0, abs=1e-15)
    assert result.shapley_can_override_edge_failure is False
    assert result.path_status == "order_sensitive_full_transfer"


def test_joint_max_t_certification_preserves_order_sensitive_path_result():
    nodes, information, groups, blocks = _fixture()
    result = certify_information_lattice(
        nodes,
        information,
        groups,
        blocks=blocks,
        bootstrap_draws=700,
        seed=13,
        minimum_blocks_per_group=2,
    )

    assert result.all_cells_estimable is True
    assert result.cell_count == 8
    assert result.estimable_cell_count == 8
    assert result.total_admissible_path_count == 2
    assert result.robust_full_transfer_path_count == 1
    assert result.robust_full_transfer_path_fraction == pytest.approx(0.5)
    assert result.certified_path_status == "order_sensitive_full_transfer"
    assert result.all_edges_robust_generalizing is False
    assert result.total_gain_can_override_failed_edge is False
    assert result.shapley_can_override_edge_failure is False

    edges = {
        (tuple(edge.lower_blocks), edge.added_block): edge.category
        for edge in result.edges
    }
    assert edges[((), "A")] == "robust_generalizing"
    assert edges[(("A",), "B")] == "robust_non_generalizing"
    assert edges[((), "B")] == "robust_generalizing"
    assert edges[(("B",), "A")] == "robust_generalizing"

    summaries = {row.block: row.order_robust_category for row in result.block_summaries}
    assert summaries["A"] == "order_robust_generalizing"
    assert summaries["B"] == "order_sensitive"


def test_universal_and_no_full_transfer_path_statuses():
    nodes, information, groups, _ = _fixture()
    n = len(groups)

    universal = audit_information_lattice(
        (
            InformationLatticeNodeScore((), [0.0] * n),
            InformationLatticeNodeScore(("A",), [0.2] * n),
            InformationLatticeNodeScore(("B",), [0.1] * n),
            InformationLatticeNodeScore(("A", "B"), [0.4] * n),
        ),
        information,
        groups,
    )
    assert universal.full_transfer_path_count == 2
    assert universal.path_status == "universal_full_transfer"

    none = audit_information_lattice(
        (
            InformationLatticeNodeScore((), [0.0] * n),
            InformationLatticeNodeScore(("A",), [-0.1] * n),
            InformationLatticeNodeScore(("B",), [-0.2] * n),
            InformationLatticeNodeScore(("A", "B"), [0.3] * n),
        ),
        information,
        groups,
    )
    assert none.full_vs_base_gain_category == "generalizing"
    assert none.full_transfer_path_count == 0
    assert none.path_status == "no_full_transfer"


def test_complete_subset_table_is_required():
    nodes, information, groups, _ = _fixture()
    with pytest.raises(ValueError, match="complete subset score table"):
        audit_information_lattice(nodes[:-1], information, groups)


def test_information_blocks_must_be_disjoint_from_each_other_and_base():
    nodes, _, groups, _ = _fixture()
    overlapping = (
        InformationBlock("A", ("species", "site")),
        InformationBlock("B", ("site", "season")),
    )
    with pytest.raises(ValueError, match="variable-disjoint"):
        audit_information_lattice(nodes, overlapping, groups)

    information = (
        InformationBlock("A", ("species",)),
        InformationBlock("B", ("context",)),
    )
    with pytest.raises(ValueError, match="disjoint from added information blocks"):
        audit_information_lattice(
            nodes,
            information,
            groups,
            base_information=("species",),
        )


def test_nonfinite_full_node_marks_shapley_unavailable_and_stops_paths():
    nodes, information, groups, blocks = _fixture()
    full = list(nodes[-1].score)
    full[0] = -math.inf
    broken = (*nodes[:-1], InformationLatticeNodeScore(("A", "B"), full))

    point = audit_information_lattice(broken, information, groups)
    assert point.full_transfer_path_count == 0
    assert point.path_status == "no_full_transfer"
    assert point.shapley_additivity_error_max_abs is None
    assert all(row.shapley_gain_category == "unavailable" for row in point.block_summaries)

    certified = certify_information_lattice(
        broken,
        information,
        groups,
        blocks=blocks,
        bootstrap_draws=500,
        minimum_blocks_per_group=2,
    )
    assert certified.robust_full_transfer_path_count == 0
    assert certified.certified_path_status == "no_full_transfer"
    incoming = [edge for edge in certified.edges if tuple(edge.upper_blocks) == ("A", "B")]
    assert incoming and all(edge.category == "unavailable" for edge in incoming)


def test_node_order_and_row_order_do_not_change_scientific_summary():
    nodes, information, groups, blocks = _fixture()
    reference = certify_information_lattice(
        nodes,
        information,
        groups,
        blocks=blocks,
        bootstrap_draws=600,
        seed=99,
        minimum_blocks_per_group=2,
    )

    reversed_nodes = tuple(reversed(nodes))
    reversed_rows = tuple(
        InformationLatticeNodeScore(node.blocks, list(reversed(node.score)))
        for node in reversed_nodes
    )
    other = certify_information_lattice(
        reversed_rows,
        information,
        list(reversed(groups)),
        blocks=list(reversed(blocks)),
        bootstrap_draws=600,
        seed=99,
        minimum_blocks_per_group=2,
    )

    assert other.point_audit.path_status == reference.point_audit.path_status
    assert other.certified_path_status == reference.certified_path_status
    assert other.robust_full_transfer_path_count == reference.robust_full_transfer_path_count
    assert other.max_t_critical_value == pytest.approx(reference.max_t_critical_value)
