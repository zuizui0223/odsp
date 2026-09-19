from __future__ import annotations

import itertools

import numpy as np
import pytest

from odsp.confirmatory_method_routing import route_confirmatory_method
from odsp.information_lattice import InformationBlock
from odsp.refit_information_lattice import RefitInformationLatticeNodeScores
from odsp.refit_positive_independent_lattice_robustness import (
    certify_all_refit_independent_positive_information_lattice_v2,
)


def _design(group_count: int = 3, blocks_per_group: int = 8):
    groups: list[str] = []
    blocks: list[str] = []
    for group_index in range(group_count):
        for block_index in range(blocks_per_group):
            groups.append(f"g{group_index}")
            blocks.append(f"g{group_index}-b{block_index:02d}")
    return groups, blocks


def _blocks(names: tuple[str, ...]):
    return tuple(InformationBlock(name=name, variables=(name.lower(),)) for name in names)


def _all_subsets(names: tuple[str, ...]):
    for size in range(len(names) + 1):
        yield from itertools.combinations(names, size)


def _constant_nodes(
    names: tuple[str, ...],
    values_by_refit: list[dict[tuple[str, ...], float]],
    n: int,
):
    rows = []
    for subset in _all_subsets(names):
        matrix = np.asarray(
            [[mapping[subset]] * n for mapping in values_by_refit],
            dtype=float,
        )
        rows.append(RefitInformationLatticeNodeScores(blocks=subset, score=matrix))
    return rows


def test_all_refit_independent_lattice_supports_universal_paths():
    groups, blocks = _design()
    names = ("A", "B")
    mapping = {(): 0.0, ("A",): 0.4, ("B",): 0.4, ("A", "B"): 0.8}
    result = certify_all_refit_independent_positive_information_lattice_v2(
        _constant_nodes(names, [mapping, mapping, mapping], len(groups)),
        _blocks(names),
        groups,
        blocks=blocks,
        refit_ids=("r2", "r0", "r1"),
        minimum_refits=2,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
    )

    assert result.refit_ids == ("r0", "r1", "r2")
    assert result.design == "independent_groups"
    assert result.information_block_count == 2
    assert result.edge_count == 4
    assert result.all_refit_robust_full_transfer_path_count == 2
    assert result.all_refit_certified_path_status == "universal_full_transfer"
    assert all(row.category == "robust_across_refits" for row in result.edges)
    assert result.intersection_union_rule_used is True
    assert result.different_refit_paths_can_be_combined is False
    assert result.refit_population_generalization_claimed is False
    assert result.validation_group_independence_assumed is True


def test_different_successful_paths_across_refits_cannot_form_global_path():
    groups, blocks = _design()
    names = ("A", "B")
    values = [
        {(): 0.0, ("A",): 0.4, ("B",): 0.1, ("A", "B"): 0.3},
        {(): 0.0, ("A",): 0.1, ("B",): 0.4, ("A", "B"): 0.3},
    ]
    result = certify_all_refit_independent_positive_information_lattice_v2(
        _constant_nodes(names, values, len(groups)),
        _blocks(names),
        groups,
        blocks=blocks,
        refit_ids=("r0", "r1"),
        minimum_refits=2,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
    )

    assert tuple(row.robust_full_transfer_path_count for row in result.per_refit) == (1, 1)
    assert result.all_refit_robust_full_transfer_path_count == 0
    assert result.all_refit_certified_path_status == "no_full_transfer"
    assert result.different_refit_paths_can_be_combined is False
    incoming = [row for row in result.edges if row.lower_blocks]
    assert all(row.category == "not_robust_across_refits" for row in incoming)


def test_three_block_all_refit_independent_lattice_hard_stops():
    groups, blocks = _design()
    names = ("A", "B", "C")
    mapping = {subset: 0.3 * len(subset) for subset in _all_subsets(names)}
    with pytest.raises(ValueError, match="exactly 2 information blocks"):
        certify_all_refit_independent_positive_information_lattice_v2(
            _constant_nodes(names, [mapping, mapping], len(groups)),
            _blocks(names),
            groups,
            blocks=blocks,
            refit_ids=("r0", "r1"),
            minimum_refits=2,
            bootstrap_draws=500,
            minimum_blocks_per_group=8,
        )


def test_insufficient_refits_makes_global_independent_lattice_unavailable():
    groups, blocks = _design()
    names = ("A", "B")
    mapping = {(): 0.0, ("A",): 0.4, ("B",): 0.4, ("A", "B"): 0.8}
    result = certify_all_refit_independent_positive_information_lattice_v2(
        _constant_nodes(names, [mapping, mapping], len(groups)),
        _blocks(names),
        groups,
        blocks=blocks,
        refit_ids=("r0", "r1"),
        minimum_refits=3,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
    )
    assert result.robustness_evaluable is False
    assert result.all_refit_robust_full_transfer_path_count == 0
    assert result.all_refit_certified_path_status == "unavailable"
    assert all(row.category == "unavailable" for row in result.edges)


def test_refit_order_is_canonicalized():
    groups, blocks = _design()
    names = ("A", "B")
    mappings = [
        {(): 0.0, ("A",): 0.3, ("B",): 0.2, ("A", "B"): 0.6},
        {(): 0.0, ("A",): 0.4, ("B",): 0.3, ("A", "B"): 0.8},
    ]
    first = certify_all_refit_independent_positive_information_lattice_v2(
        _constant_nodes(names, mappings, len(groups)),
        _blocks(names),
        groups,
        blocks=blocks,
        refit_ids=("r1", "r0"),
        minimum_refits=2,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
        seed=13,
    )
    second = certify_all_refit_independent_positive_information_lattice_v2(
        _constant_nodes(names, list(reversed(mappings)), len(groups)),
        _blocks(names),
        groups,
        blocks=blocks,
        refit_ids=("r0", "r1"),
        minimum_refits=2,
        bootstrap_draws=500,
        minimum_blocks_per_group=8,
        seed=13,
    )
    assert first.as_dict() == second.as_dict()


def test_router_promotes_fixed_set_internal_independent_four_edge_lattice_only():
    route = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="fixed_set",
        external_validation="none",
        information_block_count=2,
    )
    assert route.role == "primary_confirmatory"
    assert route.canonical_surface == (
        "odsp.refit_positive_independent_lattice_robustness."
        "certify_all_refit_independent_positive_information_lattice_v2"
    )
    assert route.refit_population_generalization_claimed is False

    external = route_confirmatory_method(
        alternative="greater",
        validation_design="independent_groups",
        information_structure="complete_lattice",
        upstream_refits="fixed_set",
        external_validation="untouched_frozen",
        information_block_count=2,
    )
    assert external.role == "unqualified"
